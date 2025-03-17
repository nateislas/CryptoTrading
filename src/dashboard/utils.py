# src/dashboard/utils.py
import os
from src.robinhood_api.api_access import CryptoAPITrading
from src.data_processing.data_utils import load_historical_data
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
    """
    Fetches the daily percentage and dollar change for the given asset.

    Args:
        asset_code (str): The cryptocurrency ticker symbol (e.g., 'BTC').
        current_price (float): The current market price of the asset.

    Returns:
        tuple: (percent_change, dollar_change) rounded to 2 decimals, or (None, None) if data is unavailable.
    """
    try:
        today = datetime.datetime.today().strftime('%Y-%m-%d')

        # Call load_historical_data to get resampled 1-minute OHLC data
        ohlc_data = load_historical_data(
            ticker=f"{asset_code}-USD",
            data_interval="1s",
            start_date=today,
            end_date=today,
            ohlc_interval="1min"
        )

        # If no data was returned
        if ohlc_data.empty:
            logging.error(f"No data found for {asset_code} on {today}")
            return None, None

        # Get the first open price of the day
        open_price = float(ohlc_data['open'].iloc[0])

        # Calculate percentage and dollar change
        percent_change = ((current_price - open_price) / open_price) * 100
        dollar_change = current_price - open_price

        return round(percent_change, 2), round(dollar_change, 2)

    except Exception as e:
        logging.error(f"Error fetching daily changes for {asset_code}: {e}")
        return None, None


def fetch_daily_price(asset_code):
    """
    Fetches the daily price data for the given asset using the load_historical_data function.

    Args:
        asset_code (str): The cryptocurrency ticker symbol (e.g., 'BTC').

    Returns:
        np.ndarray or None: Array of closing prices if data is available, otherwise None.
    """
    try:
        today = datetime.datetime.today().strftime('%Y-%m-%d')

        # Call load_historical_data to get resampled 1-minute OHLC data
        ohlc_data = load_historical_data(
            ticker=f"{asset_code}-USD",
            data_interval="1s",
            start_date=today,
            end_date=today,
            ohlc_interval="1min"
        )

        # If no data was returned
        if ohlc_data.empty:
            logging.error(f"No data found for {asset_code} on {today}")
            return None

        # Extract and return the 'close' prices
        return ohlc_data['close'].values

    except Exception as e:
        logging.error(f"Error fetching daily price for {asset_code}: {e}")
        return None

def fetch_holdings():
    """
    Fetches the holdings information from the api

    Returns:
            A list of dictionaries, where each dictionary represents a holding.
            Each dictionary will contain:
                - asset_code (str): The crypto symbol (e.g., "BTC").
                - total_quantity (str): The total quantity held.
                - quantity_available_for_trading (str): The quantity available for trading.
    """
    try:
        holdings_data = client.account.get_holdings()
        # check if the data has results
        if "results" in holdings_data:
            holdings_list = holdings_data["results"]
            return holdings_list
        else:
            logging.warning("No results field in get_holdings data.")
            return []
    except Exception as e:
        logging.error(f"Error fetching holdings: {e}")
        return []