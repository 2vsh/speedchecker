import configparser
import os
import logging
from typing import Dict, Any

class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'config.ini'
        self._ensure_config_exists()
        self.load_config()

    def _ensure_config_exists(self) -> None:
        """Create default config file if it doesn't exist."""
        if not os.path.exists(self.config_file):
            self.config['Thresholds'] = {
                'download_speed': '50',
                'upload_speed': '10',
                'ping': '100',
                'packet_loss': '1.0'
            }
            self.config['SMS'] = {
                'enabled': 'true',
                'chat_id': '',  # Changed from phone_number to chat_id for Telegram
                'provider': 'telegram',  # Default to Telegram
                'api_key': ''
            }
            self.config['General'] = {
                'test_interval': '1200',
                'jitter_range': '60'
            }
            self.save_config()
            logging.info("Created default config.ini file")

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            self.config.read(self.config_file)
            logging.info("Configuration loaded successfully")
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            raise

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
            raise

    def get_thresholds(self) -> Dict[str, float]:
        """Get all threshold values."""
        return {
            'download_speed': self.config.getfloat('Thresholds', 'download_speed'),
            'upload_speed': self.config.getfloat('Thresholds', 'upload_speed'),
            'ping': self.config.getfloat('Thresholds', 'ping'),
            'packet_loss': self.config.getfloat('Thresholds', 'packet_loss')
        }

    def get_sms_config(self) -> Dict[str, Any]:
        """Get SMS/messaging configuration."""
        return {
            'enabled': self.config.getboolean('SMS', 'enabled'),
            'chat_id': self.config.get('SMS', 'chat_id'),  # Changed from phone_number to chat_id
            'provider': self.config.get('SMS', 'provider'),
            'api_key': self.config.get('SMS', 'api_key')
        }

    def get_general_config(self) -> Dict[str, int]:
        """Get general configuration values."""
        return {
            'test_interval': self.config.getint('General', 'test_interval'),
            'jitter_range': self.config.getint('General', 'jitter_range')
        }
