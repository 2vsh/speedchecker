import speedtest
import time
import csv
import os
import random
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_monitor.log'),
        logging.StreamHandler()
    ]
)

def get_random_user_agent() -> str:
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    return random.choice(agents)

def perform_speed_test() -> Dict[str, Any]:
    try:
        logging.info("Starting speed test...")
        
        # Configure speedtest with custom settings
        st = speedtest.Speedtest(secure=True, timeout=30)  # Added timeout
        
        # Use random user agent
        st.user_agent = get_random_user_agent()
        
        logging.info("Getting server list...")
        # Get best server directly instead of random selection
        best_server = st.get_best_server()
        logging.info(f"Selected server: {best_server['name']}, {best_server['country']}")
        
        # Add small random delay to appear more like natural traffic
        time.sleep(random.uniform(0.5, 1.5))
        
        logging.info("Testing download speed...")
        download_speed = st.download() / 1_000_000
        
        # Verify download speed is reasonable, retry if not
        if download_speed < 0.1:  # Less than 0.1 Mbps is suspicious
            logging.warning("Suspicious download speed detected, retrying...")
            time.sleep(1)
            download_speed = st.download() / 1_000_000
        
        # Small delay between tests
        time.sleep(random.uniform(0.5, 1.5))
        
        logging.info("Testing upload speed...")
        upload_speed = st.upload() / 1_000_000
        
        # Verify upload speed is reasonable, retry if not
        if upload_speed < 0.1:  # Less than 0.1 Mbps is suspicious
            logging.warning("Suspicious upload speed detected, retrying...")
            time.sleep(1)
            upload_speed = st.upload() / 1_000_000
        
        # Get ping/jitter and server info
        results = st.results
        
        # Verify ping is reasonable (typical range 5-500ms)
        ping = results.ping
        if ping > 1000 or ping < 1:  # Suspicious ping values
            logging.warning("Suspicious ping detected, using previous server ping")
            ping = best_server['latency']  # Use the initial server ping test instead
        
        test_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'download': round(download_speed, 2),
            'upload': round(upload_speed, 2),
            'ping': round(ping, 2),
            'isp': results.client['isp'],
            'server_location': f"{results.server['name']}, {results.server['country']}",
            'server_id': results.server['id']
        }
        
        # Validate results before logging
        if all(v > 0 for v in [test_results['download'], test_results['upload'], test_results['ping']]):
            logging.info(f"Test completed successfully: Download: {test_results['download']} Mbps, Upload: {test_results['upload']} Mbps, Ping: {test_results['ping']} ms")
            return test_results
        else:
            raise ValueError("Invalid speed test results detected")
            
    except speedtest.ConfigRetrievalError as e:
        logging.error(f"Failed to retrieve speedtest configuration: {str(e)}")
    except speedtest.NoMatchedServers as e:
        logging.error(f"No matched servers: {str(e)}")
    except speedtest.SpeedtestBestServerFailure as e:
        logging.error(f"Failed to find best server: {str(e)}")
    except speedtest.InvalidServerIDType as e:
        logging.error(f"Invalid server ID: {str(e)}")
    except Exception as e:
        logging.error(f"Error during speed test: {str(e)}")
    
    # Return error results if any exception occurred
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'download': -1,
        'upload': -1,
        'ping': -1,
        'isp': 'Error',
        'server_location': 'Error',
        'server_id': -1
    }

def save_to_csv(data: Dict[str, Any]) -> None:
    try:
        # Create Data directory if it doesn't exist
        if not os.path.exists('Data'):
            os.makedirs('Data')
            logging.info("Created Data directory")
        
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
            
    except Exception as e:
        logging.error(f"Error saving to CSV: {str(e)}")

def main() -> None:
    logging.info("Network monitoring started")
    
    # Create Data directory at startup
    if not os.path.exists('Data'):
        os.makedirs('Data')
        logging.info("Created Data directory at startup")
    
    while True:
        try:
            # Add some randomness to the exact timing
            jitter = random.uniform(-60, 60)  # ±1 minute jitter
            
            # Perform speed test and save results
            results = perform_speed_test()
            
            # Only save results if they're valid
            if results['download'] > 0:
                save_to_csv(results)
                next_test = 1200 + jitter  # ~20 minutes
            else:
                logging.warning("Invalid results detected, retrying in 5 minutes...")
                next_test = 300  # 5 minutes
            
            logging.info(f"Waiting approximately {next_test/60:.2f} minutes for next test")
            time.sleep(next_test)
            
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait 1 minute before retrying
            continue

if __name__ == "__main__":
    main()
