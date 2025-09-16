# helper.py

import os
import pyzipper
import random
import string
import logging
from logging.handlers import RotatingFileHandler

# Setup improved logging for helper module
logger = logging.getLogger('helper')
logger.setLevel(logging.INFO)

# Only add handlers if they don't exist
if not logger.handlers:
    # Rotating file handler
    log_folder = 'logs'
    os.makedirs(log_folder, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_folder, 'helper.log'),
        maxBytes=2*1024*1024,  # 2MB
        backupCount=1
    )
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.propagate = False

def zip_directory(directory):
    """Zip the entire directory with AES encryption and return the zip file path and random password."""
    logger.info(f"Starting zip process for directory: {directory}")
    
    if not os.path.exists(directory):
        logger.error(f"Directory {directory} does not exist")
        raise FileNotFoundError(f"Directory {directory} not found")
    
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Random password
    zip_filename = f"{directory}_backup_aes.zip"
    
    try:
        # Calculate total files to zip
        total_files = sum(len(files) for _, _, files in os.walk(directory))
        logger.info(f"Preparing to zip {total_files} files from {directory}")
        
        # Create a zip file of the entire directory with AES encryption
        with pyzipper.AESZipFile(zip_filename, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipf:
            zipf.setpassword(password.encode())
            
            files_processed = 0
            total_size = 0
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory)
                    
                    try:
                        # Get file size for logging
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                        # Read the file content
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Write the file content to the zip file with AES encryption
                        zipf.writestr(arcname, file_content)
                        files_processed += 1
                        
                        # Log progress every 10 files
                        if files_processed % 10 == 0:
                            logger.info(f"Zipped {files_processed}/{total_files} files")
                            
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
                        continue
        
        # Log final statistics
        zip_size = os.path.getsize(zip_filename) if os.path.exists(zip_filename) else 0
        logger.info(f"Successfully created {zip_filename}")
        logger.info(f"Original size: {total_size / (1024*1024):.2f} MB, Compressed size: {zip_size / (1024*1024):.2f} MB")
        logger.info(f"Compression ratio: {((total_size - zip_size) / total_size * 100):.1f}%" if total_size > 0 else "N/A")
        
        return zip_filename, password
        
    except Exception as e:
        logger.error(f"Error creating zip file {zip_filename}: {str(e)}")
        # Clean up partial zip file if it exists
        if os.path.exists(zip_filename):
            try:
                os.remove(zip_filename)
                logger.info(f"Cleaned up partial zip file: {zip_filename}")
            except:
                pass
        raise
