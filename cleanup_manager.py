#!/usr/bin/env python3
"""
Daily cleanup manager for storage optimization
Manages storage by cleaning up old files, logs, and temporary data
"""

import os
import shutil
import logging
import schedule
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging with rotation
log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)

logger = logging.getLogger('cleanup_manager')
logger.setLevel(logging.INFO)

# Rotating file handler (2MB max, keep 1 backup)
file_handler = RotatingFileHandler(
    os.path.join(log_folder, 'cleanup.log'),
    maxBytes=2*1024*1024,  # 2MB
    backupCount=1
)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

def get_directory_size(directory):
    """Calculate total size of directory in MB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Error calculating size for {directory}: {str(e)}")
    return total_size / (1024 * 1024)  # Convert to MB

def cleanup_old_files(directory, days_old=7):
    """Remove files older than specified days"""
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return 0
    
    removed_count = 0
    removed_size = 0
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        removed_size += file_size
                        logger.info(f"Removed old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error walking directory {directory}: {str(e)}")
    
    return removed_count, removed_size / (1024 * 1024)  # Size in MB

def cleanup_zip_files(max_age_hours=24):
    """Remove zip files older than specified hours"""
    removed_count = 0
    removed_size = 0
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    
    try:
        for file in os.listdir('.'):
            if file.endswith('.zip'):
                file_path = os.path.join('.', file)
                try:
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        removed_size += file_size
                        logger.info(f"Removed old zip file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing zip file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning zip files: {str(e)}")
    
    return removed_count, removed_size / (1024 * 1024)  # Size in MB

def cleanup_git_objects(repo_path):
    """Clean up git objects to save space"""
    if not os.path.exists(os.path.join(repo_path, '.git')):
        logger.warning(f"No git repository found at {repo_path}")
        return
    
    try:
        import subprocess
        # Git garbage collection
        result = subprocess.run(
            ['git', 'gc', '--aggressive', '--prune=now'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Git garbage collection completed successfully")
        else:
            logger.error(f"Git gc failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error during git cleanup: {str(e)}")

def daily_cleanup():
    """Perform daily cleanup operations"""
    logger.info("Starting daily cleanup process")
    
    total_removed_files = 0
    total_freed_space = 0
    
    # Get initial storage usage
    download_dir = os.getenv('DOWNLOAD_DIR', 'downloads')
    initial_size = get_directory_size('.')
    logger.info(f"Initial total directory size: {initial_size:.2f} MB")
    
    # Clean old download files (keep for 5 days)
    if os.path.exists(download_dir):
        count, size = cleanup_old_files(download_dir, days_old=5)
        total_removed_files += count
        total_freed_space += size
        logger.info(f"Cleaned {count} old download files, freed {size:.2f} MB")
    
    # Clean old log files (keep for 3 days)
    if os.path.exists('logs'):
        count, size = cleanup_old_files('logs', days_old=3)
        total_removed_files += count
        total_freed_space += size
        logger.info(f"Cleaned {count} old log files, freed {size:.2f} MB")
    
    # Clean old zip files (keep for 1 day)
    count, size = cleanup_zip_files(max_age_hours=24)
    total_removed_files += count
    total_freed_space += size
    logger.info(f"Cleaned {count} old zip files, freed {size:.2f} MB")
    
    # Git cleanup if download directory is a git repo
    if os.path.exists(download_dir):
        cleanup_git_objects(download_dir)
    
    # Final storage check
    final_size = get_directory_size('.')
    logger.info(f"Final total directory size: {final_size:.2f} MB")
    logger.info(f"Cleanup completed: {total_removed_files} files removed, {total_freed_space:.2f} MB freed")
    
    # Alert if storage is still high (>400MB)
    if final_size > 400:
        logger.warning(f"Storage usage still high: {final_size:.2f} MB (>400MB threshold)")

def emergency_cleanup():
    """Emergency cleanup when storage is critically low"""
    logger.warning("Starting emergency cleanup - storage critically low")
    
    # More aggressive cleanup
    download_dir = os.getenv('DOWNLOAD_DIR', 'downloads')
    
    # Keep only 2 days of downloads
    if os.path.exists(download_dir):
        count, size = cleanup_old_files(download_dir, days_old=2)
        logger.info(f"Emergency: Cleaned {count} files, freed {size:.2f} MB from downloads")
    
    # Keep only 1 day of logs
    if os.path.exists('logs'):
        count, size = cleanup_old_files('logs', days_old=1)
        logger.info(f"Emergency: Cleaned {count} files, freed {size:.2f} MB from logs")
    
    # Remove all zip files
    count, size = cleanup_zip_files(max_age_hours=1)
    logger.info(f"Emergency: Cleaned {count} zip files, freed {size:.2f} MB")

def check_storage_and_cleanup():
    """Check storage usage and perform cleanup if needed"""
    current_size = get_directory_size('.')
    logger.info(f"Current storage usage: {current_size:.2f} MB")
    
    if current_size > 450:  # Emergency threshold
        logger.warning("Storage usage critical (>450MB), starting emergency cleanup")
        emergency_cleanup()
    elif current_size > 350:  # Regular cleanup threshold
        logger.info("Storage usage high (>350MB), starting regular cleanup")
        daily_cleanup()
    else:
        logger.info("Storage usage normal, no cleanup needed")

if __name__ == "__main__":
    # Schedule daily cleanup at 2 AM
    schedule.every().day.at("02:00").do(daily_cleanup)
    
    # Check storage every 6 hours
    schedule.every(6).hours.do(check_storage_and_cleanup)
    
    logger.info("Cleanup manager started - scheduled daily cleanup at 2 AM and storage checks every 6 hours")
    
    # Run initial cleanup
    check_storage_and_cleanup()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour
