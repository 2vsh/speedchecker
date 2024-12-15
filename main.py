import speedtest
import time
import csv
import os
import random
import logging
from datetime import datetime
from typing import Dict, Any

from config_handler import ConfigHandler
from sms_handler import SMSHandler
from first_run import FirstRunHandler

def console_print(message: str, config_handler: ConfigHandler) -> None:
    """Print to console only if not in headless mode."""
    if not config_handler.get_general_config()['headless']:
        print(message)

def get_random_user_agent() -> str:
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    return random.choice(agents)

def perform_speed_test(config_handler: ConfigHandler, sms_handler: SMSHandler) -> Dict[str, Any]:
    try:
        console_print("Starting speed test...", config_handler)
        logging.info("Starting speed test...")
        
        # Get thresholds from config
        thresholds = config_handler.get_thresholds()
        
        # Configure speedtest with custom settings
        st = speedtest.Speedtest(secure=True)
        st.user_agent = get_random_user_agent()
        
        console_print("Getting server list...", config_handler)
        logging.info("Getting server list...")
        best_server = st.get_best_server()
        logging.info(f"Selected server: {best_server['name']}, {best_server['country']}")
        console_print(f"Selected server: {best_server['name']}, {best_server['country']}", config_handler)
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Test download speed
        console_print("Testing download speed...", config_handler)
        logging.info("Testing download speed...")
        download_speed = st.download() / 1_000_000
        if download_speed < thresholds['download_speed']:
            sms_handler.send_alert(
                f"Low download speed detected: {download_speed:.2f} Mbps "
                f"(threshold: {thresholds['download_speed']} Mbps)"
            )
        
        # Verify download speed
        if download_speed < 0.1:
            logging.warning("Suspicious download speed detected, retrying...")
            time.sleep(1)
            download_speed = st.download() / 1_000_000
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Test upload speed
        console_print("Testing upload speed...", config_handler)
        logging.info("Testing upload speed...")
        upload_speed = st.upload() / 1_000_000
        if upload_speed < thresholds['upload_speed']:
            sms_handler.send_alert(
                f"Low upload speed detected: {upload_speed:.2f} Mbps "
                f"(threshold: {thresholds['upload_speed']} Mbps)"
            )
        
        # Verify upload speed
        if upload_speed < 0.1:
            logging.warning("Suspicious upload speed detected, retrying...")
            time.sleep(1)
            upload_speed = st.upload() / 1_000_000
        
        # Get ping/jitter and server info
        results = st.results
        ping = results.ping
        
        # Check ping threshold
        if ping > thresholds['ping']:
            sms_handler.send_alert(
                f"High ping detected: {ping:.2f} ms "
                f"(threshold: {thresholds['ping']} ms)"
            )
        
        # Verify ping is reasonable
        if ping > 1000 or ping < 1:
            logging.warning("Suspicious ping detected, using previous server ping")
            ping = best_server['latency']
        
        test_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'download': round(download_speed, 2),
            'upload': round(upload_speed, 2),
            'ping': round(ping, 2),
            'isp': results.client['isp'],
            'server_location': f"{results.server['name']}, {results.server['country']}",
            'server_id': results.server['id']
        }
        
        if all(v > 0 for v in [test_results['download'], test_results['upload'], test_results['ping']]):
            console_print(f"Test completed successfully: Download: {test_results['download']} Mbps, "
                       f"Upload: {test_results['upload']} Mbps, Ping: {test_results['ping']} ms", config_handler)
            logging.info(f"Test completed successfully: Download: {test_results['download']} Mbps, "
                        f"Upload: {test_results['upload']} Mbps, Ping: {test_results['ping']} ms")
            return test_results
        else:
            raise ValueError("Invalid speed test results detected")
            
    except Exception as e:
        console_print(f"Error during speed test: {str(e)}", config_handler)
        logging.error(f"Error during speed test: {str(e)}")
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'download': -1,
            'upload': -1,
            'ping': -1,
            'isp': 'Error',
            'server_location': 'Error',
            'server_id': -1
        }

def save_to_csv(data: Dict[str, Any], config_handler: ConfigHandler) -> None:
    try:
        csv_file = os.path.join('Data', 'network_metrics.csv')
        file_exists = os.path.exists(csv_file)
        
        fieldnames = ['timestamp', 'download', 'upload', 'ping', 'isp', 'server_location', 'server_id']
        
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
                logging.info("Created new CSV file with headers")
            writer.writerow(data)
            logging.info("Successfully wrote data to CSV")
            console_print(f"Data saved to {csv_file}", config_handler)
            
    except Exception as e:
        console_print(f"Error saving to CSV: {str(e)}", config_handler)
        logging.error(f"Error saving to CSV: {str(e)}")

def main() -> None:
    # Initialize configuration first to handle headless mode
    config_handler = ConfigHandler()
    
    console_print("Starting Network Speed Monitor...", config_handler)
    
    # Initialize first run
    init_status = FirstRunHandler.initialize()
    if not init_status['success']:
        console_print(f"Initialization failed: {init_status['messages']}", config_handler)
        logging.error("Initialization failed")
        return

    # Check dependencies
    dep_status = FirstRunHandler.check_dependencies()
    if not dep_status['success']:
        console_print(f"Dependency check failed: {dep_status['messages']}", config_handler)
        logging.error("Dependency check failed")
        return
    
    # Initialize SMS handler
    sms_handler = SMSHandler(config_handler.get_sms_config())
    
    # Get general configuration
    general_config = config_handler.get_general_config()
    
    console_print("Network monitoring started", config_handler)
    logging.info("Network monitoring started")
    
    while True:
        try:
            # Add configured jitter to the timing
            jitter = random.uniform(-general_config['jitter_range'], general_config['jitter_range'])
            
            # Perform speed test and save results
            results = perform_speed_test(config_handler, sms_handler)
            
            # Only save results if they're valid
            if results['download'] > 0:
                save_to_csv(results, config_handler)
                next_test = general_config['test_interval'] + jitter
            else:
                console_print("Invalid results detected, retrying in 5 minutes...", config_handler)
                logging.warning("Invalid results detected, retrying in 5 minutes...")
                next_test = 300  # 5 minutes
            
            console_print(f"Waiting approximately {next_test/60:.2f} minutes for next test", config_handler)
            logging.info(f"Waiting approximately {next_test/60:.2f} minutes for next test")
            time.sleep(next_test)
            
        except Exception as e:
            console_print(f"Error in main loop: {str(e)}", config_handler)
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait 1 minute before retrying
            continue

if __name__ == "__main__":
    main()
