# telegram_helper.py

import os
import requests
import os
from dotenv import load_dotenv
from logger_config import system_logger, log_error_with_context, log_function_entry, log_function_exit

# Load environment variables
load_dotenv()

def send_telegram_message(message):
    """Send a message to the Telegram bot."""
    log_function_entry(system_logger, "send_telegram_message", msg_length=len(message))
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        system_logger.error("TELEGRAM ERROR: Bot token or chat ID not found in environment")
        system_logger.error(f"Bot token exists: {bool(bot_token)}")
        system_logger.error(f"Chat ID exists: {bool(chat_id)}")
        return False
    
    system_logger.info(f"TELEGRAM: Sending message ({len(message)} chars) to chat {chat_id}")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'  # Enable HTML formatting
    }
    
    try:
        system_logger.debug(f"TELEGRAM API: POST to {url}")
        response = requests.post(url, data=payload, timeout=30)
        
        if response.status_code == 200:
            system_logger.info("TELEGRAM SUCCESS: Message sent successfully")
            log_function_exit(system_logger, "send_telegram_message", "success")
            return True
        else:
            system_logger.error(f"TELEGRAM FAILED: Status {response.status_code}")
            system_logger.error(f"Response: {response.text}")
            log_function_exit(system_logger, "send_telegram_message", "failed")
            return False
            
    except requests.exceptions.Timeout:
        system_logger.error("TELEGRAM ERROR: Request timeout (30s)")
        return False
    except requests.exceptions.ConnectionError:
        system_logger.error("TELEGRAM ERROR: Connection error - check internet")
        return False
    except Exception as e:
        log_error_with_context(system_logger, e, "Telegram message sending")
        return False

def send_telegram_file(file_path):
    """Send a file to the Telegram bot."""
    log_function_entry(system_logger, "send_telegram_file", file=file_path)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        system_logger.error("TELEGRAM FILE ERROR: Bot token or chat ID not found")
        return False
    
    if not os.path.exists(file_path):
        system_logger.error(f"TELEGRAM FILE ERROR: File does not exist: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    system_logger.info(f"TELEGRAM FILE: Sending {file_path} ({file_size / (1024*1024):.2f} MB)")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    try:
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {'chat_id': chat_id}
            response = requests.post(url, files=files, data=data, timeout=120)  # 2 min timeout for files
        
        if response.status_code == 200:
            system_logger.info(f"TELEGRAM FILE SUCCESS: {file_path} sent")
            log_function_exit(system_logger, "send_telegram_file", "success")
            return True
        else:
            system_logger.error(f"TELEGRAM FILE FAILED: Status {response.status_code}")
            system_logger.error(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        system_logger.error("TELEGRAM FILE ERROR: Upload timeout (2min)")
        return False
    except Exception as e:
        log_error_with_context(system_logger, e, f"Telegram file sending: {file_path}")
        return False
