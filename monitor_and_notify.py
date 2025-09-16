import os
import time
from datetime import datetime
from dotenv import load_dotenv
from logger_config import system_logger, log_error_with_context, log_function_entry, log_function_exit
from telegram_helper import send_telegram_message, send_telegram_file
from git_commiter import push_to_github

# Load environment variables
load_dotenv()

# Directory to monitor
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    system_logger.info(f"Created missing directory: {DOWNLOAD_DIR}")
else:
    system_logger.info(f"Monitoring directory: {DOWNLOAD_DIR}")

def get_ist_time():
    """Get the current date and time in IST format."""
    log_function_entry(system_logger, "get_ist_time")
    try:
        now = datetime.now()
        ist_time = now.strftime("%d %B %Y %I:%M %p")
        log_function_exit(system_logger, "get_ist_time", ist_time)
        return ist_time
    except Exception as e:
        log_error_with_context(system_logger, e, "Getting IST time")
        return "Unknown time"

def log_download_summary():
    """Log summary of downloads directory for tracking"""
    log_function_entry(system_logger, "log_download_summary")
    try:
        total_files = 0
        total_size = 0
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
        
        system_logger.info(f"Download directory summary: {total_files} files, {total_size / (1024*1024):.2f} MB total")
        log_function_exit(system_logger, "log_download_summary", f"{total_files} files, {total_size / (1024*1024):.2f} MB")
        return total_files, total_size
    except Exception as e:
        log_error_with_context(system_logger, e, "Calculating download summary")
        return 0, 0

def monitor_downloads():
    """Monitor the downloads directory for new files or folders at 10-minute intervals."""
    log_function_entry(system_logger, "monitor_downloads", download_dir=DOWNLOAD_DIR)
    
    system_logger.info("Starting file monitoring system")
    last_seen_files = set()
    
    # Initial scan
    try:
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                last_seen_files.add(os.path.join(root, file))
        system_logger.info(f"Initial scan complete: {len(last_seen_files)} files found")
    except Exception as e:
        log_error_with_context(system_logger, e, "Initial directory scan")
    
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            system_logger.debug(f"Starting monitoring cycle #{cycle_count}")
            
            time.sleep(600)  # 10 minutes
            current_files = set()
            
            # Scan for current files
            try:
                for root, dirs, files in os.walk(DOWNLOAD_DIR):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        current_files.add(os.path.join(root, file))
                system_logger.debug(f"Current scan: {len(current_files)} files found")
            except Exception as e:
                log_error_with_context(system_logger, e, "Directory scanning")
                continue
            
            # Check for new files
            new_files = current_files - last_seen_files
            
            if new_files:
                system_logger.info(f"NEW FILES DETECTED: {len(new_files)} files")
                for file in new_files:
                    system_logger.info(f"  -> {file}")
                
                # Calculate storage info
                total_size = 0
                try:
                    for f in new_files:
                        if os.path.exists(f):
                            size = os.path.getsize(f)
                            total_size += size
                            system_logger.debug(f"File size: {f} = {size} bytes")
                    system_logger.info(f"Total new files size: {total_size / (1024*1024):.2f} MB")
                except Exception as e:
                    log_error_with_context(system_logger, e, "Calculating file sizes")
                    total_size = 0
                
                # Get timestamp
                ist_time = get_ist_time()
                file_names = [os.path.basename(f) for f in new_files]
                
                # Send Telegram notification
                try:
                    system_logger.info("Preparing Telegram notification")
                    message = f"📥 New Snapchat story downloaded\n\n"
                    message += f"📁 Files: {len(new_files)}\n"
                    message += f"📊 Size: {total_size / (1024*1024):.2f} MB\n"
                    message += f"🕒 Time: {ist_time}\n\n"
                    
                    if len(file_names) <= 5:
                        message += f"📋 Files:\n" + "\n".join([f"• {name}" for name in file_names])
                    else:
                        message += f"📋 Files (showing first 5):\n" + "\n".join([f"• {name}" for name in file_names[:5]])
                        message += f"\n... and {len(file_names) - 5} more files"
                    
                    system_logger.debug(f"Telegram message prepared: {len(message)} characters")
                    
                    # Push to GitHub first
                    system_logger.info("Starting GitHub push operation")
                    push_result = push_to_github(DOWNLOAD_DIR, os.getenv('REPO_BRANCH'))
                    
                    message += f"\n\n✅ Files pushed to GitHub repository"
                    
                    system_logger.info("Sending Telegram notification")
                    send_telegram_message(message)
                    system_logger.info(f"SUCCESS: Notification sent for {len(new_files)} files")
                    
                except Exception as e:
                    log_error_with_context(system_logger, e, "Telegram notification process")
            else:
                system_logger.debug(f"No new files detected in cycle #{cycle_count}")
            
            # Update file list
            last_seen_files = current_files
            system_logger.debug(f"Cycle #{cycle_count} completed successfully")
            
        except Exception as e:
            log_error_with_context(system_logger, e, f"Monitoring cycle #{cycle_count}")
            system_logger.warning("Continuing monitoring despite error")
            time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    try:
        system_logger.info("MONITOR_AND_NOTIFY STARTUP")
        
        # Log environment variables
        system_logger.info(f"DOWNLOAD_DIR: {DOWNLOAD_DIR}")
        system_logger.info(f"REPO_BRANCH: {os.getenv('REPO_BRANCH')}")
        
        # Send startup message
        try:
            startup_msg = "🚀 Snap-Tracker Monitoring Started\n\n"
            startup_msg += f"📂 Watching: {DOWNLOAD_DIR}\n"
            startup_msg += f"⏱️ Check interval: 10 minutes\n"
            startup_msg += f"🔄 Git push: Incremental, one-way\n"
            startup_msg += f"📊 Storage optimized: No zip files"
            
            send_telegram_message(startup_msg)
            system_logger.info("Startup notification sent")
        except Exception as e:
            log_error_with_context(system_logger, e, "Sending startup notification")

        # Start monitoring
        system_logger.info("Starting download monitoring")
        monitor_downloads()
        
    except KeyboardInterrupt:
        system_logger.info("Monitoring stopped by user (Ctrl+C)")
    except Exception as e:
        log_error_with_context(system_logger, e, "Main execution")
        system_logger.critical("SYSTEM FAILURE - Monitor stopped")
