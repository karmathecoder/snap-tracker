# telegram_helper.py

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Send a text message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # To allow HTML formatting in the message
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Message sent successfully: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

def send_telegram_file(file_path):
    """Send a file to a Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendDocument"
    
    with open(file_path, 'rb') as file:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
        }
        files = {
            'document': file,
        }
        
        try:
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            print(f"File sent successfully: {file_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send file: {e}")
