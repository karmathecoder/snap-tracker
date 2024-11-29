# helper.py

import os
import pyzipper
import random
import string
import logging

def zip_directory(directory):
    """Zip the entire directory with AES encryption and return the zip file path and random password."""
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Random password
    zip_filename = f"{directory}_backup_aes.zip"
    
    # Create a zip file of the entire directory with AES encryption
    with pyzipper.AESZipFile(zip_filename, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword(password.encode())
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory)
                
                # Read the file content
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Write the file content to the zip file with AES encryption
                zipf.writestr(arcname, file_content)
    
    logging.info(f"Zipped directory {directory} into {zip_filename} with AES encryption and password {password}")
    return zip_filename, password
