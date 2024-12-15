import logging
from typing import Optional
import requests

class SMSHandler:
    def __init__(self, config: dict):
        self.enabled = config['enabled']
        self.chat_id = config.get('chat_id', '')  # Telegram chat ID
        self.provider = config['provider']
        self.api_key = config['api_key']  # Telegram bot token

    def send_alert(self, message: str) -> bool:
        """
        Send an alert using Telegram.
        Returns True if successful, False otherwise.
        """
        if not self.enabled:
            logging.info("Alerts are disabled")
            return False

        if not all([self.chat_id, self.provider, self.api_key]):
            logging.error("Telegram configuration incomplete")
            return False

        try:
            response = self._send_message(message)
            if response:
                logging.info(f"Telegram alert sent successfully: {message}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error sending Telegram alert: {str(e)}")
            return False

    def _send_message(self, message: str) -> Optional[bool]:
        """
        Send message using Telegram Bot API.
        """
        try:
            if self.provider.lower() != "telegram":
                logging.error(f"Unsupported provider: {self.provider}")
                return None

            url = f"https://api.telegram.org/bot{self.api_key}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"  # Allows basic formatting
            }
            
            response = requests.post(url, json=data)
            response_json = response.json()
            
            if response.status_code == 200 and response_json.get('ok'):
                return True
            else:
                error = response_json.get('description', 'Unknown error')
                logging.error(f"Telegram API error: {error}")
                return False
                
        except Exception as e:
            logging.error(f"Error in send_message: {str(e)}")
            return None
