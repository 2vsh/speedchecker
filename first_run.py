import os
import logging
from typing import Dict, Any
from config_handler import ConfigHandler

class FirstRunHandler:
    @staticmethod
    def initialize() -> Dict[str, Any]:
        """
        Perform first-run initialization tasks.
        Returns a dictionary with initialization status.
        """
        status = {
            'success': True,
            'messages': []
        }

        try:
            # Ensure Data directory exists
            if not os.path.exists('Data'):
                os.makedirs('Data')
                status['messages'].append("Created Data directory")
                logging.info("Created Data directory")

            # Initialize configuration
            config_handler = ConfigHandler()
            status['messages'].append("Configuration initialized")
            
            # Set up logging
            logging_setup = FirstRunHandler._setup_logging()
            status['messages'].extend(logging_setup['messages'])
            
            if not logging_setup['success']:
                status['success'] = False

        except Exception as e:
            status['success'] = False
            status['messages'].append(f"Error during initialization: {str(e)}")
            logging.error(f"First run initialization error: {str(e)}")

        return status

    @staticmethod
    def _setup_logging() -> Dict[str, Any]:
        """Set up logging configuration."""
        status = {
            'success': True,
            'messages': []
        }

        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('network_monitor.log'),
                    logging.StreamHandler()
                ]
            )
            status['messages'].append("Logging configuration initialized")
            logging.info("Logging system initialized")

        except Exception as e:
            status['success'] = False
            status['messages'].append(f"Error setting up logging: {str(e)}")
            print(f"Error setting up logging: {str(e)}")  # Fallback since logging might not be working

        return status

    @staticmethod
    def check_dependencies() -> Dict[str, Any]:
        """
        Check if all required dependencies are installed.
        Returns a dictionary with dependency check status.
        """
        status = {
            'success': True,
            'messages': []
        }

        required_packages = ['speedtest-cli', 'requests']
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                status['messages'].append(f"Package '{package}' is installed")
            except ImportError:
                status['success'] = False
                status['messages'].append(f"Missing required package: {package}")
                logging.error(f"Missing required package: {package}")

        return status
