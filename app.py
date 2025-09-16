import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from urllib.parse import unquote
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.getenv('WEB_SECRET_KEY')

# Setup improved logging for Flask app
if not app.debug:
    log_folder = 'logs'
    os.makedirs(log_folder, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_folder, 'app.log'),
        maxBytes=2*1024*1024,  # 2MB
        backupCount=1
    )
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask app startup')

# Base directories (change as needed)
DOWNLOADS_DIR = 'downloads'
LOGS_DIR = 'logs'

# Username and password for login (for simplicity, you can replace with a proper DB or auth system)
USERNAME = os.getenv('WEB_USERNAME')
PASSWORD = os.getenv('WEB_PASSWORD')

app.logger.info(f'Web interface configured for user: {USERNAME}')

# Function to list files and directories in a given path
def list_directory_contents(directory):
    contents = []
    try:
        # List all files and subdirectories
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                contents.append({'name': item, 'type': 'directory'})
            elif os.path.isfile(full_path):
                contents.append({'name': item, 'type': 'file'})
    except FileNotFoundError:
        app.logger.warning(f'Directory not found: {directory}')
    return contents

def list_zip_files_in_pwd():
    contents = []
    try:
        for item in os.listdir('.'):  # '.' refers to the current working directory
            if os.path.isfile(item) and item.endswith('.zip'):
                contents.append({'name': item, 'type': 'file'})
    except FileNotFoundError:
        app.logger.warning('Current directory not accessible for zip file listing')
    return contents


@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in'] == True:
        # List the contents of the base directories
        downloads_contents = list_directory_contents(DOWNLOADS_DIR)
        logs_contents = list_directory_contents(LOGS_DIR)
        zip_files = list_zip_files_in_pwd()  # List zip files in the current directory
        return render_template('index.html', downloads=downloads_contents, logs=logs_contents, zip_files=zip_files)
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            app.logger.info(f'Successful login for user: {username}')
            return redirect(url_for('index'))
        else:
            app.logger.warning(f'Failed login attempt for user: {username}')
            return "Invalid login credentials, please try again."
    return render_template('login.html')


@app.route('/logout')
def logout():
    app.logger.info('User logged out')
    session['logged_in'] = False
    return redirect(url_for('login'))


# Route to browse directories and files
@app.route('/browse/<path:subpath>')
def browse(subpath):
    if 'logged_in' not in session or session['logged_in'] == False:
        return redirect(url_for('login'))

    # Decode the subpath and normalize the path
    subpath = unquote(subpath)  # Decode any URL-encoded characters
    download_path = os.path.join(DOWNLOADS_DIR, subpath)
    log_path = os.path.join(LOGS_DIR, subpath)

    # Check if the subpath exists in either directory
    if os.path.exists(download_path) and os.path.isdir(download_path):
        contents = list_directory_contents(download_path)
        return render_template('browse.html', directory=subpath, contents=contents, base_directory=DOWNLOADS_DIR)

    if os.path.exists(log_path) and os.path.isdir(log_path):
        contents = list_directory_contents(log_path)
        return render_template('browse.html', directory=subpath, contents=contents, base_directory=LOGS_DIR)

    app.logger.error(f'Directory not found for subpath: {subpath}')
    return "Directory not found."


@app.route('/files/<path:filename>')
def download_file(filename):
    # Decode and normalize the filename
    filename = unquote(filename)  # Decode any URL-encoded characters
    download_path = os.path.join(DOWNLOADS_DIR, filename)
    log_path = os.path.join(LOGS_DIR, filename)
    
    # Current working directory (PWD) check
    pwd_path = os.path.join(os.getcwd(), filename)  # PWD is the current directory where the app is running

    # Check if the file exists in the downloads directory
    if os.path.exists(download_path) and os.path.isfile(download_path):
        return send_from_directory(DOWNLOADS_DIR, filename)

    # Check if the file exists in the logs directory
    elif os.path.exists(log_path) and os.path.isfile(log_path):
        return send_from_directory(LOGS_DIR, filename)

    # Check if the file exists in the current directory (PWD)
    elif os.path.exists(pwd_path) and os.path.isfile(pwd_path):
        return send_from_directory('.', filename)  # Serve from the current directory (PWD)

    else:
        app.logger.error(f'File not found: {filename}')
        return "File not found."


if __name__ == '__main__':
    app.logger.info('Starting Flask development server')
    app.run(debug=True)
