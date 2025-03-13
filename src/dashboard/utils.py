# src/dashboard/utils.py
import os
from src.robinhood_api.api_access import CryptoAPITrading
import logging
import webbrowser
import socket
import pandas as pd
from fastparquet import ParquetFile
import datetime
# Configure logging if not already done in the main app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = CryptoAPITrading()
# Function to open a browser tab
def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}/")
# Function to find an available port
def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

# Fetch account details
def fetch_account_details():
    try:
        account_details = client.account.get_account()
        return account_details.get("account_number", "N/A"), float(account_details.get("buying_power", "0"))
    except Exception as e:
        logging.error(f"Error fetching account details: {e}")
        return "N/A", 0.0

# Fetch real-time asset price
def fetch_asset_price(asset_code):
    try:
        price_data = client.market_data.get_estimated_price(f"{asset_code}-USD", "both", 1.0)
        return float(price_data["results"][0]["price"]) if price_data and "results" in price_data else None
    except Exception as e:
        logging.error(f"Error fetching price for {asset_code}: {e}")
        return None
def fetch_daily_changes(asset_code, current_price):
    try:
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        project_root = os.path.abspath(os.path.join(os.getcwd()))
        folder = os.path.join(project_root, 'data', f"{asset_code}-USD", "1s")
        file_path = os.path.join(folder, f"{today}.parquet")
        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None, None
        # Load the Parquet file
        pf = ParquetFile(file_path)
        # Read only the 'price_bid' column along with 'timestamp'
        df = pf.to_pandas(columns=['price_bid', 'timestamp'])  # Assuming 'timestamp' is your datetime column
        # Convert 'timestamp' to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        # Resample the data into 1-minute intervals and calculate OHLC
        df = df['price_bid'].resample('1min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        if not df.empty:
            open_price = float(df['open'][0])  # Fetch the open price for the first minute of the day
            percent_change = ((current_price - open_price) / open_price) * 100
            dollar_change = current_price - open_price
            return round(percent_change, 2), round(dollar_change, 2)
    except Exception as e:
        logging.error(f"Error fetching daily changes for {asset_code}: {e}")
        return None, None
def fetch_daily_price(asset_code):
    try:
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        project_root = os.path.abspath(os.path.join(os.getcwd()))
        folder = os.path.join(project_root, 'data', f"{asset_code}-USD", "1s")
        file_path = os.path.join(folder, f"{today}.parquet")
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None
        # Load the Parquet file
        pf = ParquetFile(file_path)
        # Read only the 'price_bid' column and assume timestamp is available for indexing
        df = pf.to_pandas(columns=['price_bid', 'timestamp'])  # Assuming 'timestamp' is your datetime column
        # Convert 'timestamp' to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        # Resample the data into 1-minute intervals and calculate OHLC
        ohlc_data = df['price_bid'].resample('1min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        # Extract and return the 'close' column
        close_prices = ohlc_data['close'].values
        return close_prices
    except Exception as e:
        logging.error(f"Error fetching daily price for {asset_code}: {e}")
        return None