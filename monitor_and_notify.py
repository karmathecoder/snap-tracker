import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv
from helper import zip_directory
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

def update_password_file(password):
    """Update the password.txt file with the latest password."""
    try:
        with open(PASSWORD_FILE, 'w') as f:
            f.write(password)
        logger.info(f"Password file updated with new password: {password}")
    except Exception as e:
        logger.error(f"Failed to update password file: {str(e)}")

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
            
            # Check storage before zipping
            try:
                total_size = sum(os.path.getsize(f) for f in new_files if os.path.exists(f))
                logger.info(f"New files total size: {total_size / (1024*1024):.2f} MB")
            except Exception as e:
                logger.warning(f"Could not calculate new files size: {str(e)}")
            
            # Zip the entire downloads directory
            logger.info("Starting zip process for download folder")
            try:
                zip_file, password = zip_directory(DOWNLOAD_DIR)
                logger.info(f"Successfully created zip: {zip_file}")
                
                # Update the password.txt file
                update_password_file(password)
                
                # Get the current date and time in IST
                ist_time = get_ist_time()
                
                # Send a Telegram message about new files
                message = f"New Snapchat story downloaded.\nFiles: {len(new_files)}\nPassword: <code>{password}</code>\nDate & Time: {ist_time}"
                send_telegram_message(message)
                # send_telegram_file(zip_file)  # Commented to save bandwidth

                # Log the activity
                logger.info(f"Notification sent for {zip_file} with password: {password} at {ist_time}")
                
            except Exception as e:
                logger.error(f"Error during zip/notification process: {str(e)}")
        
        # Update the list of files
        last_seen_files = current_files

        push_to_github(DOWNLOAD_DIR,os.getenv('REPO_BRANCH'))


if __name__ == "__main__":
    try:
        # Send the "Hi" message when the script starts
        send_telegram_message("Hi! Monitoring has started.")

        logger.info("Starting main execution")
        monitor_downloads()
    except Exception as e:
        logger.error(f"Error in the main execution: {str(e)}")
