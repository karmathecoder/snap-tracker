import os
import time
import logging
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

# Initialize logging
LOG_DIR = './logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'monitor_and_notify.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
        logging.info(f"Password file updated with new password: {password}")
    except Exception as e:
        logging.error(f"Failed to update password file: {str(e)}")

def monitor_downloads():
    """Monitor the downloads directory for new files or folders at 20-second intervals."""
    last_seen_files = set()
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        # Skip directories starting with a dot
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            last_seen_files.add(os.path.join(root, file))
    
    while True:
        time.sleep(60)  # Sleep for 20 seconds between checks
        current_files = set()
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                current_files.add(os.path.join(root, file))
        
        # Check for new files
        new_files = current_files - last_seen_files
        
        if new_files:
            logging.info(f"New files detected: {new_files}")
            # Zip the entire downloads directory
            logging.info(f"Zipping the download folder.")
            zip_file, password = zip_directory(DOWNLOAD_DIR)
            
            # Update the password.txt file
            update_password_file(password)
            
            # Get the current date and time in IST
            ist_time = get_ist_time()
            
            # Send a Telegram message about new files
            send_telegram_message(f"New Snapchat story downloaded.\nPassword: <code>{password}</code>\nDate & Time: {ist_time}")
            # send_telegram_file(zip_file)

            # Log the activity
            logging.info(f"Sent {zip_file} with password: {password} at {ist_time}")
        
        # Update the list of files
        last_seen_files = current_files

        push_to_github(DOWNLOAD_DIR,os.getenv('REPO_BRANCH'))


if __name__ == "__main__":
    try:
        # Send the "Hi" message when the script starts
        send_telegram_message("Hi! Monitoring has started.")

        logging.basicConfig(level=logging.INFO)
        monitor_downloads()
    except Exception as e:
        logging.error(f"Error in the main execution: {str(e)}")
