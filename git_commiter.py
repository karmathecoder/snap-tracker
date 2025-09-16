import os
import subprocess
import json
import hashlib
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from logger_config import system_logger, log_error_with_context, log_function_entry, log_function_exit

# Load environment variables from .env file
load_dotenv()

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
        system_logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return None

def load_pushed_files_tracker():
    """Load the tracker of previously pushed files"""
    log_function_entry(system_logger, "load_pushed_files_tracker")
    if os.path.exists(PUSHED_FILES_TRACKER):
        try:
            with open(PUSHED_FILES_TRACKER, 'r') as f:
                data = json.load(f)
            system_logger.debug(f"Loaded tracker with {len(data)} files")
            return data
        except Exception as e:
            log_error_with_context(system_logger, e, "Loading pushed files tracker")
    system_logger.debug("No existing tracker found, starting fresh")
    return {}

def save_pushed_files_tracker(tracker_data):
    """Save the tracker of pushed files"""
    log_function_entry(system_logger, "save_pushed_files_tracker", count=len(tracker_data))
    try:
        os.makedirs(os.path.dirname(PUSHED_FILES_TRACKER), exist_ok=True)
        with open(PUSHED_FILES_TRACKER, 'w') as f:
            json.dump(tracker_data, f, indent=2)
        system_logger.info(f"Updated pushed files tracker with {len(tracker_data)} files")
    except Exception as e:
        log_error_with_context(system_logger, e, "Saving pushed files tracker")

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
    log_function_entry(system_logger, "incremental_push_to_github", folder=folder_path, branch=branch)
    
    try:
        system_logger.info(f"GIT PUSH: Starting incremental push for {folder_path}")
        
        # Get incremental changes
        system_logger.debug("Analyzing file changes...")
        new_or_modified, current_files = get_incremental_changes(folder_path)
        
        if not new_or_modified:
            system_logger.info("GIT PUSH: No changes detected, repository up to date")
            return True
        
        system_logger.info(f"GIT PUSH: Found {len(new_or_modified)} changed files")
        for file in new_or_modified[:10]:  # Log first 10 files
            system_logger.info(f"  CHANGED: {file}")
        if len(new_or_modified) > 10:
            system_logger.info(f"  ... and {len(new_or_modified) - 10} more files")
        
        # Add files to git
        added_files = 0
        for file_path in new_or_modified:
            system_logger.debug(f"Adding to git: {file_path}")
            add_result = subprocess.run(
                ['git', 'add', file_path], 
                capture_output=True, text=True, cwd=folder_path
            )
            if add_result.returncode != 0:
                system_logger.error(f"Failed to add {file_path}: {add_result.stderr}")
                continue
            added_files += 1
        
        system_logger.info(f"GIT ADD: Successfully added {added_files}/{len(new_or_modified)} files")

        # Verify staged changes
        status_result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'], 
            capture_output=True, text=True, cwd=folder_path
        )
        
        staged_files = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        system_logger.info(f"GIT STATUS: {len(staged_files)} files staged for commit")
        
        if not staged_files or not staged_files[0]:
            system_logger.warning("GIT STATUS: No staged changes found after adding files")
            return False

        # Create commit
        commit_message = f"Incremental update: {len(staged_files)} files at {get_ist_time()}"
        system_logger.info(f"GIT COMMIT: Creating commit with message: {commit_message}")
        
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message], 
            capture_output=True, text=True, cwd=folder_path
        )
        if commit_result.returncode != 0:
            system_logger.error(f"GIT COMMIT FAILED: {commit_result.stderr}")
            return False
        
        system_logger.info("GIT COMMIT: Successfully created commit")

        # Get repository URL
        repo_url = os.getenv('REPO_URL_WITH_TOKEN')
        if not repo_url:
            system_logger.error("GIT PUSH FAILED: No REPO_URL_WITH_TOKEN in environment")
            return False

        # Force push (one-way)
        system_logger.info(f"GIT PUSH: Force pushing to {branch} (one-way, no pull)")
        push_result = subprocess.run(
            ['git', 'push', '--force', repo_url, branch], 
            capture_output=True, text=True, cwd=folder_path
        )
            
        if push_result.returncode == 0:
            system_logger.info(f"GIT PUSH SUCCESS: Pushed {len(staged_files)} files to {branch}")
            # Update tracker only after successful push
            save_pushed_files_tracker(current_files)
            return True
        else:
            system_logger.error(f"GIT PUSH FAILED: {push_result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        log_error_with_context(system_logger, e, f"Git subprocess error in {folder_path}")
        return False
    except Exception as e:
        log_error_with_context(system_logger, e, f"Incremental push error in {folder_path}")
        return False

def push_to_github(folder_path, branch='main'):
    """Wrapper function that calls incremental push"""
    incremental_push_to_github(folder_path, branch)

if __name__ == "__main__":
    # These are for testing purposes only.
    folder_path = os.getenv('DOWNLOAD_DIR')
    branch = os.getenv('REPO_BRANCH')

    # Call the function to push to GitHub
    push_to_github(folder_path, branch)
