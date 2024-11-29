# download_snapchat_stories.py

import os
import subprocess
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
LOG_DIR = './logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'snapchat_dl.log'),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

USERNAME = os.getenv('SNAPCHAT_USERNAME')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')

def download_snapchat_stories():
    """Run the snapchat-dl command to download stories."""
    logging.info("Starting Snapchat story download...")

    command = [
        'snapchat-dl', '-u', USERNAME, '-P', DOWNLOAD_DIR,'-d','-s',
    ]

    # Run the snapchat-dl subprocess and log output
    with open(os.path.join(LOG_DIR, 'snapchat_dl.log'), 'a') as log_file:
        process = subprocess.Popen(command, stdout=log_file, stderr=log_file)
        process.wait()

    if process.returncode == 0:
        logging.info("Snapchat story download completed.")
    else:
        logging.error("Snapchat story download failed.")

if __name__ == "__main__":
    download_snapchat_stories()
