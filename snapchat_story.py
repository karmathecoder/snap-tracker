import os
import subprocess
import logging
import threading
from dotenv import load_dotenv
import time

# Load environment variables from .env
load_dotenv()

# Configure logging
LOG_DIR = './logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'snapchat_dl.log')

# Set up logging to both file and console (optional)
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

USERNAME = os.getenv('SNAPCHAT_USERNAME')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')

usernames = USERNAME.split()

def trim_log_file():
    """Keep only the latest 100 lines in the log file."""
    with open(LOG_FILE, 'r') as file:
        lines = file.readlines()
    
    # Keep only the last 100 lines
    if len(lines) > 2000:
        lines = lines[-2000:]
    
    # Rewrite the log file with the latest 100 lines
    with open(LOG_FILE, 'w') as file:
        file.writelines(lines)

def periodic_log_trimming():
    """Trim the log file every 10 seconds while the process is running."""
    while True:
        time.sleep(10)  # Trim the log every 10 seconds
        trim_log_file()

def download_snapchat_stories():
    """Run the snapchat-dl command to download stories."""
    logging.info("Starting Snapchat story download...")

    command = ['snapchat-dl'] + usernames + ['-u', '-P', DOWNLOAD_DIR, '-d', '-s']

    # Start the periodic log trimming in a background thread
    trim_thread = threading.Thread(target=periodic_log_trimming, daemon=True)
    trim_thread.start()

    # Run the snapchat-dl subprocess and log output to a file
    with open(LOG_FILE, 'a') as log_file:
        process = subprocess.Popen(command, stdout=log_file, stderr=log_file)
        process.wait()  # Wait for the process to finish (this will block indefinitely)

    if process.returncode == 0:
        logging.info("Snapchat story download completed.")
    else:
        logging.error("Snapchat story download failed.")

if __name__ == "__main__":
    download_snapchat_stories()
