import os
import requests
import time
from prometheus_client import Gauge, start_http_server
from datetime import datetime

# Default configuration
DEFAULT_ADDRESS = "NQ97+H1NR+S3X0+CVFQ+VJ9Y+9A0Y+FRQN+Q6EU+D0PL"
DEFAULT_INTERVAL = 300  # 300 seconds (5 minutes)

# Get environment variables for address and interval (if not set, use defaults)
address = os.getenv("NIMIQ_ADDRESS", DEFAULT_ADDRESS)
interval = int(os.getenv("FETCH_INTERVAL", DEFAULT_INTERVAL))

# Construct the API URL
url = f"https://v2.nimiqwatch.com/api/v2/registration/{address}"

# Prometheus metrics
total_stake_gauge = Gauge('total_stake', 'Total stake of all stakers')
staker_stake_gauge = Gauge('staker_stake', 'Stake amount for each staker', ['staker_address'])
total_stakers_gauge = Gauge('total_stakers', 'Total number of stakers')
current_nimiq_price_gauge = Gauge('current_nimiq_price', 'Current Nimiq price in USD')

def log(message):
    """Helper function to log messages with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def fetch_nimiq_price():
    """Fetch the current Nimiq price from CoinGecko API."""
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=nimiq-2&vs_currencies=usd")
        response.raise_for_status()
        return response.json().get("nimiq-2", {}).get("usd")
    except requests.exceptions.RequestException as e:
        log(f"Error fetching Nimiq price: {e}")
        return None

def fetch_registration_data(api_url):
    """Fetch registration data from the given API URL."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log(f"Error fetching data: {e}")
        return None

def process_data(data):
    """Process the data and update Prometheus metrics."""
    try:
        # Ensure that 'stakers' is present at the top level of the response
        stakers = data.get("stakers", [])
        if not stakers:
            log("No stakers found in the data.")
            return
        
        total_stake = 0
        stakes = []  # List to store all stake amounts for calculating min/max
        
        # Update total stakers count
        total_stakers_gauge.set(len(stakers))
        
        # Update individual staker stakes and calculate total stake
        for staker in stakers:
            stake = staker["stake"]
            stakes.append(stake)
            total_stake += stake
            staker_stake_gauge.labels(staker["address"]).set(stake)
        
        # Calculate the highest and lowest stake
        highest_stake = max(stakes)
        lowest_stake = min(stakes)

        # Update total stake gauge
        total_stake_gauge.set(total_stake)
        log(f"Total stake: {total_stake} across {len(stakers)} stakers")
        log(f"Highest stake: {highest_stake}")
        log(f"Lowest stake: {lowest_stake}")
    
    except KeyError as e:
        log(f"Missing expected key in the data: {e}")
    except Exception as e:
        log(f"Error processing data: {e}")

def main():
    # Log the configured address and interval at startup
    log(f"Starting Pre staking Nimiq Prometheus exporter")
    log(f"Fetching from address: {address}")
    log(f"Fetch interval: {interval} seconds")

    # Start the Prometheus metrics server on port 8000
    start_http_server(8000)
    
    while True:
        # Log that we're scraping the data
        log("Scraping data...")
        
        # Fetch registration data
        data = fetch_registration_data(url)
        
        if data:
            # Process the data and update Prometheus metrics
            process_data(data)
        
        # Fetch the current Nimiq price
        price = fetch_nimiq_price()
        if price:
            # Update the current Nimiq price gauge
            current_nimiq_price_gauge.set(price)
            log(f"Current Nimiq price: ${price}")
        
        # Log when the next scrape will occur
        log(f"Next scrape in {interval} seconds")
        
        # Sleep for the configured interval before fetching again
        time.sleep(interval)

if __name__ == "__main__":
    main()
