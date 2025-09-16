#!/usr/bin/env python3
"""
Startup script to integrate cleanup manager with the main application
"""

import os
import sys
import subprocess
import threading
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('startup')

def start_cleanup_manager():
    """Start the cleanup manager in a separate process"""
    try:
        logger.info("Starting cleanup manager...")
        subprocess.Popen([sys.executable, 'cleanup_manager.py'], 
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        logger.info("Cleanup manager started successfully")
    except Exception as e:
        logger.error(f"Failed to start cleanup manager: {str(e)}")

def start_monitor_and_notify():
    """Start the monitor and notify process"""
    try:
        logger.info("Starting monitor and notify...")
        subprocess.Popen([sys.executable, 'monitor_and_notify.py'],
                        cwd=os.path.dirname(os.path.abspath(__file__)))
        logger.info("Monitor and notify started successfully")
    except Exception as e:
        logger.error(f"Failed to start monitor and notify: {str(e)}")

def main():
    """Main startup function"""
    logger.info("=== Snap Tracker Application Startup ===")
    
    # Start cleanup manager
    start_cleanup_manager()
    
    # Wait a moment before starting the main monitor
    time.sleep(2)
    
    # Start monitor and notify
    start_monitor_and_notify()
    
    logger.info("All services started. Application is running.")
    logger.info("Storage optimization features:")
    logger.info("- Rotating logs to prevent disk space issues")
    logger.info("- No git pull operations to save storage")
    logger.info("- Daily cleanup of old files")
    logger.info("- Emergency cleanup when storage is low")

if __name__ == "__main__":
    main()
