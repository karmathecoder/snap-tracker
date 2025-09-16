import os
import subprocess
import logging
import json
import hashlib
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

# Set up improved logging configuration with rotation
log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
log_filename = os.path.join(log_folder, 'github_push.log')

# Create logger with rotating file handler to manage log size
logger = logging.getLogger('git_commiter')
logger.setLevel(logging.INFO)

# Create rotating file handler (5MB max, keep 2 backup files)
file_handler = RotatingFileHandler(
    log_filename, 
    maxBytes=5*1024*1024,  # 5MB
    backupCount=2
)
file_handler.setLevel(logging.INFO)

# Create console handler for immediate feedback
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent duplicate logs
logger.propagate = False

# File to track pushed files state
PUSHED_FILES_TRACKER = 'logs/pushed_files_tracker.json'

def get_ist_time():
    """Get the current time in IST and format it."""
    # Define IST timezone offset (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_timezone = timezone(ist_offset)
    
    # Get the current time in IST
    ist_time = datetime.now(ist_timezone)
    
    # Format the time as a string for the commit message
    return ist_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def get_file_hash(file_path):
    """Calculate MD5 hash of a file for change detection"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return None

def load_pushed_files_tracker():
    """Load the tracker of previously pushed files"""
    if os.path.exists(PUSHED_FILES_TRACKER):
        try:
            with open(PUSHED_FILES_TRACKER, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pushed files tracker: {str(e)}")
    return {}

def save_pushed_files_tracker(tracker_data):
    """Save the tracker of pushed files"""
    try:
        os.makedirs(os.path.dirname(PUSHED_FILES_TRACKER), exist_ok=True)
        with open(PUSHED_FILES_TRACKER, 'w') as f:
            json.dump(tracker_data, f, indent=2)
        logger.info(f"Updated pushed files tracker with {len(tracker_data)} files")
    except Exception as e:
        logger.error(f"Error saving pushed files tracker: {str(e)}")

def get_incremental_changes(folder_path):
    """Identify only new/modified files since last push"""
    tracker = load_pushed_files_tracker()
    current_files = {}
    new_or_modified = []
    
    # Scan all files in the directory
    for root, dirs, files in os.walk(folder_path):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)
            
            # Calculate current hash
            current_hash = get_file_hash(file_path)
            if current_hash:
                current_files[relative_path] = {
                    'hash': current_hash,
                    'mtime': os.path.getmtime(file_path)
                }
                
                # Check if file is new or modified
                if (relative_path not in tracker or 
                    tracker[relative_path].get('hash') != current_hash):
                    new_or_modified.append(relative_path)
    
    return new_or_modified, current_files

def incremental_push_to_github(folder_path, branch='main'):
    """
    Push only new/modified files to GitHub incrementally (optimized for storage).
    
    :param folder_path: Path to the folder containing the Git repository.
    :param branch: The branch to push to. Default is 'main'.
    """
    try:
        logger.info(f"Starting incremental GitHub push for {folder_path}")
        
        # Get incremental changes
        new_or_modified, current_files = get_incremental_changes(folder_path)
        
        if not new_or_modified:
            logger.info("No new or modified files to push. Repository is up to date.")
            return
        
        logger.info(f"Found {len(new_or_modified)} new/modified files: {new_or_modified[:5]}{'...' if len(new_or_modified) > 5 else ''}")
        
        # Add only the new/modified files
        for file_path in new_or_modified:
            add_result = subprocess.run(
                ['git', 'add', file_path], 
                capture_output=True, text=True, cwd=folder_path
            )
            if add_result.returncode != 0:
                logger.error(f"Failed to add {file_path}: {add_result.stderr}")
                continue
        
        logger.info(f"Added {len(new_or_modified)} files to staging area")

        # Check if there are actually staged changes
        status_result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'], 
            capture_output=True, text=True, cwd=folder_path
        )
        
        if not status_result.stdout.strip():
            logger.info("No staged changes found after adding files")
            return

        # Create incremental commit message
        commit_message = f"Incremental update: {len(new_or_modified)} files at {get_ist_time()}"
        
        # Commit the changes
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message], 
            capture_output=True, text=True, cwd=folder_path
        )
        if commit_result.returncode != 0:
            logger.error(f"Failed to commit changes: {commit_result.stderr}")
            return
        logger.info(f"Incremental commit created: {commit_message}")

        # Get GitHub repository URL
        repo_url = os.getenv('REPO_URL_WITH_TOKEN')
        if not repo_url:
            logger.error("GitHub repository URL not found in .env file")
            return

        # One-way push: just add our changes on top, no pull/fetch
        # Use --force to ensure we push our changes without any remote checks
        push_result = subprocess.run(
            ['git', 'push', '--force', repo_url, branch], 
            capture_output=True, text=True, cwd=folder_path
        )
            
        if push_result.returncode == 0:
            logger.info(f"Successfully force-pushed {len(new_or_modified)} files to {branch} branch (one-way)")
            # Update tracker only after successful push
            save_pushed_files_tracker(current_files)
        else:
            logger.error(f"One-way push failed: {push_result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.cmd} - {e.stderr if hasattr(e, 'stderr') else str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during incremental push: {str(e)}")

def push_to_github(folder_path, branch='main'):
    """Wrapper function that calls incremental push"""
    incremental_push_to_github(folder_path, branch)

if __name__ == "__main__":
    # These are for testing purposes only.
    folder_path = os.getenv('DOWNLOAD_DIR')
    branch = os.getenv('REPO_BRANCH')

    # Call the function to push to GitHub
    push_to_github(folder_path, branch)
