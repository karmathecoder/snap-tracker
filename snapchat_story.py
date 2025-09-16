import os
import subprocess
import threading
from dotenv import load_dotenv
import time
from logger_config import snapchat_logger, log_error_with_context, log_function_entry, log_function_exit

# Load environment variables from .env
load_dotenv()

# Use centralized logging
LOG_FILE = 'logs/snapchat_dl.log'

USERNAME = os.getenv('SNAPCHAT_USERNAME')
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './downloads')

usernames = USERNAME.split()

# Removed log trimming - handled by RotatingFileHandler in logger_config

def download_snapchat_stories():
    """Run the snapchat-dl command to download stories."""
    log_function_entry(snapchat_logger, "download_snapchat_stories", usernames=usernames)
    
    snapchat_logger.info("SNAPCHAT-DL: Starting story download process")
    snapchat_logger.info(f"Target usernames: {usernames}")
    snapchat_logger.info(f"Download directory: {DOWNLOAD_DIR}")

    command = ['snapchat-dl'] + usernames + ['-u', '-P', DOWNLOAD_DIR, '-d', '-s']
    snapchat_logger.info(f"Command: {' '.join(command)}")

    try:
        # Create download directory if it doesn't exist
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        snapchat_logger.debug(f"Ensured download directory exists: {DOWNLOAD_DIR}")
        
        # Run snapchat-dl with detailed logging
        snapchat_logger.info("SNAPCHAT-DL: Executing download command...")
        
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Log output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                snapchat_logger.info(f"SNAPCHAT-DL OUTPUT: {output.strip()}")
        
        # Get any remaining output
        stdout, stderr = process.communicate()
        
        if stdout:
            for line in stdout.splitlines():
                if line.strip():
                    snapchat_logger.info(f"SNAPCHAT-DL STDOUT: {line}")
        
        if stderr:
            for line in stderr.splitlines():
                if line.strip():
                    snapchat_logger.error(f"SNAPCHAT-DL STDERR: {line}")

        if process.returncode == 0:
            snapchat_logger.info("SNAPCHAT-DL SUCCESS: Story download completed")
            log_function_exit(snapchat_logger, "download_snapchat_stories", "success")
            return True
        else:
            snapchat_logger.error(f"SNAPCHAT-DL FAILED: Exit code {process.returncode}")
            log_function_exit(snapchat_logger, "download_snapchat_stories", "failed")
            return False
            
    except FileNotFoundError:
        snapchat_logger.error("SNAPCHAT-DL ERROR: snapchat-dl command not found - is it installed?")
        return False
    except Exception as e:
        log_error_with_context(snapchat_logger, e, "Snapchat story download process")
        return False

if __name__ == "__main__":
    try:
        snapchat_logger.info("SNAPCHAT-DL STARTUP: Initializing story downloader")
        snapchat_logger.info(f"Environment check - USERNAME: {bool(USERNAME)}")
        snapchat_logger.info(f"Environment check - DOWNLOAD_DIR: {DOWNLOAD_DIR}")
        
        if not USERNAME:
            snapchat_logger.error("SNAPCHAT-DL ERROR: No SNAPCHAT_USERNAME in environment")
            exit(1)
            
        if not usernames:
            snapchat_logger.error("SNAPCHAT-DL ERROR: No valid usernames found")
            exit(1)
            
        # Continuous download loop
        while True:
            try:
                success = download_snapchat_stories()
                if success:
                    snapchat_logger.info("SNAPCHAT-DL: Download cycle completed, waiting 30 minutes...")
                else:
                    snapchat_logger.warning("SNAPCHAT-DL: Download failed, retrying in 10 minutes...")
                    time.sleep(600)  # Wait 10 minutes on failure
                    continue
                    
                # Wait 30 minutes before next download
                time.sleep(1800)
                
            except KeyboardInterrupt:
                snapchat_logger.info("SNAPCHAT-DL: Stopped by user (Ctrl+C)")
                break
            except Exception as e:
                log_error_with_context(snapchat_logger, e, "Main download loop")
                snapchat_logger.warning("SNAPCHAT-DL: Unexpected error, retrying in 5 minutes...")
                time.sleep(300)
                
    except Exception as e:
        log_error_with_context(snapchat_logger, e, "Snapchat downloader startup")
        snapchat_logger.critical("SNAPCHAT-DL FAILURE: Cannot start downloader")
        exit(1)
