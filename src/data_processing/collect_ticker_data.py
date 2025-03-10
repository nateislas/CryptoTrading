"""
Script for collecting cryptocurrency data from the Robinhood Crypto API using asynchronous I/O.

This script fetches bid and ask prices at specified intervals and saves the data to Parquet files.
The data is collected in batches to optimize performance and minimize API rate limits.

Dependencies:
- asyncio: For asynchronous execution.
- aiohttp: For making non-blocking HTTP requests.
- pandas: For data manipulation and storage.
- logging: For logging events and errors.
- os: For file and directory management.
- time: For time-related functions.
- datetime: For handling timestamps.
- nest_asyncio: To allow nested event loops (needed for Jupyter notebooks).
- glob: For handling file patterns.
- argparse: For command-line argument parsing.

Modules:
- CryptoAPITrading: A custom API access module for Robinhood Crypto API.

Usage:
    python collect_ticker_data.py --ticker BTC-USD --interval 1m --batch_size 250
"""

import asyncio
import aiohttp
import pandas as pd
import logging
import os
import time
from datetime import datetime
from src.robinhood_api.api_access import CryptoAPITrading
import nest_asyncio
import glob
import argparse

# Allow nested event loops (useful for Jupyter notebooks).
nest_asyncio.apply()

# Configure logging for the script.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Interval options for API calls (in seconds).
INTERVAL_SECONDS = {'1s': 1, '1m': 60, '5m': 300, '30m': 1800}

# Number of data points to collect per batch before saving.
BATCH_SIZE = 250  # Adjustable based on memory and performance needs.

async def get_price(session, client, ticker):
    """
    Asynchronously fetches the latest bid and ask prices for a given ticker.

    Args:
        session (aiohttp.ClientSession): An active HTTP session for making requests.
        client (CryptoAPITrading): An instance of the Robinhood Crypto API client.
        ticker (str): The cryptocurrency ticker symbol (e.g., 'BTC-USD').

    Returns:
        dict or None: A dictionary containing price data if successful, or None if an error occurs.
    """
    try:
        loop = asyncio.get_event_loop()
        # Run API call in executor to avoid blocking the event loop.
        response = await loop.run_in_executor(
            None, client.market_data.get_estimated_price, ticker, "both", 1.0
        )
        if 'error_code' in response:
            logging.error(f"Error: {response['error_code']}")
            return None
        return response
    except Exception as e:
        logging.error(f"Exception for {ticker}: {e}")
        return None

async def collect_data_async(client, ticker, batch_size, interval='1s'):
    """
    Asynchronously collects a batch of price data for a given ticker.

    Args:
        client (CryptoAPITrading): An instance of the Robinhood Crypto API client.
        ticker (str): The cryptocurrency ticker symbol.
        batch_size (int): Number of data points to collect per batch.
        interval (str): Time interval between API calls (e.g., '1s', '1m').

    Returns:
        list: A list of dictionaries containing the collected price data.
    """
    interval_seconds = INTERVAL_SECONDS[interval]
    batch_results = []
    async with aiohttp.ClientSession() as session:
        for _ in range(batch_size):
            task = asyncio.create_task(get_price(session, client, ticker))
            result = await task
            batch_results.append(result)
            await asyncio.sleep(interval_seconds)  # Pause between API calls.
    return batch_results


def save_to_parquet(results, ticker, interval, start_new_day):
    """
    Saves the collected data to Parquet files with efficient compression.
    If start_new_day is True, splits the data to save the previous day to a separate file.

    Args:
        results (list): List of dictionaries containing price data.
        ticker (str): The cryptocurrency ticker symbol.
        interval (str): Time interval for data collection (e.g., '1s', '1m').
        start_new_day (bool): Flag indicating if a new day has started.

    Returns:
        None
    """
    # Extract bid and ask data into separate DataFrames.
    bid_data = pd.DataFrame([res['results'][0] for res in results if res is not None])
    ask_data = pd.DataFrame([res['results'][1] for res in results if res is not None])

    # Merge bid and ask data on common columns.
    df = pd.merge(bid_data, ask_data, on=['timestamp', 'symbol', 'quantity'], suffixes=('_bid', '_ask'))

    # Ensure timestamp is in datetime format with UTC timezone.
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Define data directory and create if it doesn't exist.
    project_root = os.path.abspath(os.path.join(os.getcwd()))
    folder = os.path.join(project_root, 'data', ticker, interval)
    os.makedirs(folder, exist_ok=True)

    # Extract unique dates from the timestamp column.
    df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    unique_dates = df['date'].unique()

    # Handle the case where a new day has started.
    if start_new_day and len(unique_dates) > 1:
        # Save previous day's data to a separate file.
        for date in unique_dates[:-1]:
            previous_day_df = df[df['date'] == date]
            previous_file_path = os.path.join(folder, f"{date}.parquet")

            # Append if file exists, otherwise create new.
            if os.path.exists(previous_file_path):
                existing_df = pd.read_parquet(previous_file_path)
                previous_day_df = pd.concat([existing_df, previous_day_df]).drop_duplicates().reset_index(drop=True)

            # Save to Parquet with Snappy compression.
            previous_day_df.to_parquet(previous_file_path, index=False, compression='snappy')
            logging.info(f"Data saved for {ticker} on {date}: {previous_file_path}")

        # Keep only the current day's data.
        df = df[df['date'] == unique_dates[-1]]

    # Define file path based on current date.
    current_date_str = unique_dates[-1]
    file_path = os.path.join(folder, f"{current_date_str}.parquet")

    # Append data if file exists; otherwise, create a new file.
    if os.path.exists(file_path):
        existing_df = pd.read_parquet(file_path)
        df = pd.concat([existing_df, df]).drop_duplicates().reset_index(drop=True)

    # Save current day's data to Parquet with Snappy compression.
    df.to_parquet(file_path, index=False, compression='snappy')

    logging.info(f"Data saved successfully for {ticker} on {current_date_str}: {file_path}")

async def collect_data_continuous(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Continuously collects data and saves it to disk periodically.

    Args:
        client (CryptoAPITrading): API client for data retrieval.
        ticker (str): Cryptocurrency ticker symbol.
        interval (str): Data collection interval (default: '1s').
        batch_size (int): Number of data points per batch.

    Returns:
        None
    """
    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    all_results = []

    while True:
        # Collect a batch of data.
        batch_results = await collect_data_async(client, ticker, batch_size, interval)
        all_results.extend(batch_results)
        logging.info(f"Collected batch of {len(batch_results)} data points for {ticker}.")

        # Save data if the day changes or if batch size is large.
        new_day = datetime.utcnow().strftime("%Y-%m-%d")
        start_new_day = (new_day != current_day)
        if start_new_day or len(all_results) >= batch_size:
            save_to_parquet(all_results, ticker, interval, start_new_day)
            all_results = []  # Clear batch after saving.
            current_day = new_day

        await asyncio.sleep(0.1)  # Yield control briefly.

def start_collection(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Entry point for data collection.

    Args:
        client (CryptoAPITrading): API client instance.
        ticker (str): Cryptocurrency ticker symbol.
        interval (str): Data collection interval.
        batch_size (int): Batch size for data collection.

    Returns:
        None
    """
    asyncio.run(collect_data_continuous(client, ticker, interval, batch_size))

if __name__ == '__main__':
    # Command-line interface for specifying ticker, interval, and batch size.
    parser = argparse.ArgumentParser(description='Collect ticker data continuously.')
    parser.add_argument('--ticker', type=str, required=True, help='The ticker symbol to collect data for (e.g., BTC-USD).')
    parser.add_argument('--interval', type=str, default='1s', help='The interval for data collection (e.g., 1s, 1m).')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE, help='Batch size for data collection.')

    args = parser.parse_args()

    # Initialize API client and start data collection.
    client = CryptoAPITrading()
    start_collection(client, args.ticker, interval=args.interval, batch_size=args.batch_size)