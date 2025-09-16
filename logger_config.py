#!/usr/bin/env python3
"""
Centralized logging configuration for snap-tracker
Only 2 log files: snapchat_dl.log and system.log
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
SNAPCHAT_LOG = os.path.join(LOG_DIR, 'snapchat_dl.log')
SYSTEM_LOG = os.path.join(LOG_DIR, 'system.log')

# Custom formatter with more details
class DetailedFormatter(logging.Formatter):
    def format(self, record):
        # Add module and function info
        if hasattr(record, 'funcName') and hasattr(record, 'lineno'):
            record.location = f"{record.filename}:{record.funcName}:{record.lineno}"
        else:
            record.location = f"{record.filename}:unknown"
        
        # Format the message
        formatted = super().format(record)
        return formatted

# Create formatters
detailed_formatter = DetailedFormatter(
    '%(asctime)s | %(levelname)-8s | %(location)-30s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%H:%M:%S'
)

def setup_snapchat_logger():
    """Setup logger for snapchat-dl operations"""
    logger = logging.getLogger('snapchat_dl')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        SNAPCHAT_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=2
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

def setup_system_logger():
    """Setup logger for all other system operations"""
    logger = logging.getLogger('system')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        SYSTEM_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=2
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger

def get_logger(name):
    """Get appropriate logger based on module name"""
    if 'snapchat' in name.lower() or 'story' in name.lower():
        return setup_snapchat_logger()
    else:
        return setup_system_logger()

def log_system_info():
    """Log system startup information"""
    system_logger = setup_system_logger()
    system_logger.info("="*80)
    system_logger.info("SNAP-TRACKER SYSTEM STARTUP")
    system_logger.info("="*80)
    system_logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    system_logger.info(f"Python: {sys.version}")
    system_logger.info(f"Working Directory: {os.getcwd()}")
    system_logger.info(f"Log Files: {SNAPCHAT_LOG}, {SYSTEM_LOG}")
    system_logger.info("="*80)

def log_error_with_context(logger, error, context=""):
    """Log error with full context and traceback"""
    import traceback
    
    logger.error("="*60)
    logger.error(f"ERROR OCCURRED: {context}")
    logger.error(f"Error Type: {type(error).__name__}")
    logger.error(f"Error Message: {str(error)}")
    logger.error("Traceback:")
    for line in traceback.format_exc().splitlines():
        logger.error(f"  {line}")
    logger.error("="*60)

def log_function_entry(logger, func_name, **kwargs):
    """Log function entry with parameters"""
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"ENTER: {func_name}({params})")

def log_function_exit(logger, func_name, result=None):
    """Log function exit with result"""
    if result is not None:
        logger.debug(f"EXIT: {func_name} -> {result}")
    else:
        logger.debug(f"EXIT: {func_name}")

# Initialize loggers on import
snapchat_logger = setup_snapchat_logger()
system_logger = setup_system_logger()

# Log system startup
log_system_info()
