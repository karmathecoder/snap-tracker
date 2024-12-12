import os
import subprocess
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()

# Set up logging configuration
log_folder = 'logs'
os.makedirs(log_folder, exist_ok=True)
log_filename = os.path.join(log_folder, 'github_push.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_ist_time():
    """Get the current time in IST and format it."""
    # Define IST timezone offset (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_timezone = timezone(ist_offset)
    
    # Get the current time in IST
    ist_time = datetime.now(ist_timezone)
    
    # Format the time as a string for the commit message
    return ist_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def push_to_github(folder_path, branch='main'):
    """
    Push changes to GitHub.
    
    :param folder_path: Path to the folder containing the Git repository.
    :param branch: The branch to push to. Default is 'main'.
    """
    try:
        # Check for changes to commit in the specified directory without changing the working directory
        result = subprocess.run(
            ['git', 'status', '--porcelain'], 
            capture_output=True, text=True, cwd=folder_path
        )

        # If there are no changes, exit without errors
        if not result.stdout.strip():
            logging.info("No changes to commit. Exiting.")
            return

        # Add all changes in the specified directory
        subprocess.run(
            ['git', 'add', '.'], 
            check=True, cwd=folder_path
        )
        logging.info("All changes added to the staging area.")

        # Use the IST timestamp as the commit message
        commit_message = f"Commit made at {get_ist_time()}"
        
        # Commit the changes in the specified directory
        subprocess.run(
            ['git', 'commit', '-m', commit_message], 
            check=True, cwd=folder_path
        )
        logging.info(f"Changes committed with message: {commit_message}")

        # Get GitHub repository URL from environment variables
        repo_url = os.getenv('REPO_URL_WITH_TOKEN')
        if not repo_url:
            logging.error("GitHub repository URL not found in the .env file.")
            return

        # Push to the specified branch in the specified directory
        subprocess.run(
            ['git', 'push', repo_url, branch], 
            check=True, cwd=folder_path
        )
        logging.info(f"Changes successfully pushed to {branch} branch on GitHub!")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error occurred while executing Git commands: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # These are for testing purposes only.
    folder_path = os.getenv('DOWNLOAD_DIR')
    branch = os.getenv('REPO_BRANCH')

    # Call the function to push to GitHub
    push_to_github(folder_path, branch)
