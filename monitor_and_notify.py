import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv
# Removed zip_directory import to save storage
from telegram_helper import send_telegram_message, send_telegram_file
from git_commiter import push_to_github

# Load environment variables
load_dotenv()

# Directory to monitor
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"Created missing directory: {DOWNLOAD_DIR}")

# Initialize improved logging with rotation
LOG_DIR = './logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create logger with rotating file handler
logger = logging.getLogger('monitor_notify')
logger.setLevel(logging.INFO)

# Rotating file handler (3MB max, keep 2 backup files)
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'monitor_and_notify.log'),
    maxBytes=3*1024*1024,  # 3MB
    backupCount=2
)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

PASSWORD_FILE = os.path.join(LOG_DIR, 'password.txt')

def get_ist_time():
    """Get the current date and time in IST format."""
    now = datetime.now()
    ist_time = now.strftime("%d %B %Y %I:%M %p")
    return ist_time

def log_download_summary():
    """Log summary of downloads directory for tracking"""
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
        
        logger.info(f"Download directory summary: {total_files} files, {total_size / (1024*1024):.2f} MB total")
        return total_files, total_size
    except Exception as e:
        logger.error(f"Error calculating download summary: {str(e)}")
        return 0, 0

def monitor_downloads():
    """Monitor the downloads directory for new files or folders at 20-second intervals."""
    last_seen_files = set()
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        # Skip directories starting with a dot
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            last_seen_files.add(os.path.join(root, file))
    
    while True:
        time.sleep(600)  
        current_files = set()
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                current_files.add(os.path.join(root, file))
        
        # Check for new files
        new_files = current_files - last_seen_files
        
        if new_files:
            logger.info(f"New files detected: {len(new_files)} files - {[os.path.basename(f) for f in list(new_files)[:5]]}{'...' if len(new_files) > 5 else ''}")
            
            # Calculate storage info for notification
            try:
                total_size = sum(os.path.getsize(f) for f in new_files if os.path.exists(f))
                logger.info(f"New files total size: {total_size / (1024*1024):.2f} MB")
            except Exception as e:
                logger.warning(f"Could not calculate new files size: {str(e)}")
                total_size = 0
            
            # Get the current date and time in IST
            ist_time = get_ist_time()
            
            # Prepare file list for notification
            file_names = [os.path.basename(f) for f in new_files]
            
            # Send Telegram notification without zip
            try:
                message = f"📥 New Snapchat story downloaded\n\n"
                message += f"📁 Files: {len(new_files)}\n"
                message += f"📊 Size: {total_size / (1024*1024):.2f} MB\n"
                message += f"🕒 Time: {ist_time}\n\n"
                
                if len(file_names) <= 5:
                    message += f"📋 Files:\n" + "\n".join([f"• {name}" for name in file_names])
                else:
                    message += f"📋 Files (showing first 5):\n" + "\n".join([f"• {name}" for name in file_names[:5]])
                    message += f"\n... and {len(file_names) - 5} more files"
                
                message += f"\n\n✅ Files pushed to GitHub repository"
                
                send_telegram_message(message)
                logger.info(f"Telegram notification sent for {len(new_files)} new files at {ist_time}")
                
            except Exception as e:
                logger.error(f"Error sending telegram notification: {str(e)}")
        
        # Update the list of files
        last_seen_files = current_files

        # Push to GitHub (one-way, incremental)
        try:
            push_to_github(DOWNLOAD_DIR, os.getenv('REPO_BRANCH'))
            logger.info("Git push operation completed")
        except Exception as e:
            logger.error(f"Error during git push: {str(e)}")


if __name__ == "__main__":
    try:
        # Send the "Hi" message when the script starts
        send_telegram_message("Hi! Monitoring has started.")

        logger.info("Starting main execution")
        monitor_downloads()
    except Exception as e:
        logger.error(f"Error in the main execution: {str(e)}")
