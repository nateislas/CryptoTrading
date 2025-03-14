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
- argparse: For command-line argument parsing.
- fastparquet: For writing Parquet files with SNAPPY compression.

Modules:
- src.robinhood_api.api_access: Contains the CryptoAPITrading class to access Robinhood Crypto API.

Usage:
    python collect_ticker_data.py --ticker BTC-USD --interval 1m --batch_size 250
"""

import nest_asyncio
import asyncio
import aiohttp
import pandas as pd
import logging
import os
from datetime import datetime
import argparse
import gc
from fastparquet import write

from src.robinhood_api.api_access import CryptoAPITrading

# Allow nested event loops (useful for Jupyter notebooks).
nest_asyncio.apply()

# Interval options for API calls (in seconds).
INTERVAL_SECONDS = {'1s': 1, '1m': 60, '5m': 300, '30m': 1800}

# Default number of data points to collect per batch.
BATCH_SIZE = 185


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
    interval_seconds = INTERVAL_SECONDS.get(interval, 1)
    batch_results = []
    async with aiohttp.ClientSession() as session:
        for _ in range(batch_size):
            response = await get_price(session, client, ticker)
            if response:
                batch_results.append(response)
            await asyncio.sleep(interval_seconds)  # Spread out requests
    return batch_results


def append_to_parquet(file_path, df):
    """
    Append data to a Parquet file efficiently using Fastparquet.

    Args:
        file_path (str): Full path to the Parquet file.
        df (pandas.DataFrame): DataFrame to append.
    """
    if os.path.exists(file_path):
        # If file exists, append to it
        write(file_path, df, append=True, compression='SNAPPY', file_scheme="simple")
    else:
        # Otherwise, create a new file
        write(file_path, df, compression='SNAPPY', file_scheme="simple")


def save_to_parquet(results, ticker, interval, start_new_day):
    """
    Saves the collected data to Parquet files with efficient compression.
    If start_new_day is True (meaning we've detected a day rollover),
    this function saves all prior day data separately and keeps only
    the new day's data for the final write.

    Args:
        results (list): List of dictionaries containing price data.
        ticker (str): The cryptocurrency ticker symbol.
        interval (str): Time interval for data collection (e.g., '1s', '1m').
        start_new_day (bool): Flag indicating if a new day has started.

    Returns:
        None
    """
    if not results:
        return

    # Build bid/ask DataFrames -- *only* the columns you need
    bid_data = pd.DataFrame([r['results'][0] for r in results if r is not None])
    ask_data = pd.DataFrame([r['results'][1] for r in results if r is not None])

    # Merge on common columns
    df = pd.merge(bid_data, ask_data,
                  on=['timestamp', 'symbol', 'quantity'],
                  suffixes=('_bid', '_ask'))

    # Ensure timestamp is in datetime format with UTC timezone
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Create a 'date' column to split data by day
    df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    unique_dates = df['date'].unique()

    # Define data directory and create it if it doesn't exist
    project_root = os.path.abspath(os.path.join(os.getcwd()))
    folder = os.path.join(project_root, 'data', ticker, interval)
    os.makedirs(folder, exist_ok=True)

    # ----------------------------------------------------
    # NEW LOGIC:
    # Always handle all days except the last (if multiple),
    # so previous days get correctly written to their files.
    # ----------------------------------------------------

    # If we either detect a new day or have multiple dates,
    # handle all old dates first (unique_dates[:-1])
    # Then we'll handle the final (current) date last.
    if start_new_day or len(unique_dates) > 1:
        # Save each date except the last one
        for date in unique_dates[:-1]:
            prev_day_df = df[df['date'] == date]
            prev_file_path = os.path.join(folder, f"{date}.parquet")

            # If file exists, merge it to avoid duplicates
            if os.path.exists(prev_file_path):
                existing_df = pd.read_parquet(prev_file_path)
                prev_day_df = pd.concat([existing_df, prev_day_df]).drop_duplicates().reset_index(drop=True)

            # Append (or create) to parquet
            append_to_parquet(prev_file_path, prev_day_df)
            logging.info(f"Data saved for {ticker} on {date}: {prev_file_path}")

        # Keep only the last date in df for final save
        df = df[df['date'] == unique_dates[-1]]

    # ----------------------------------------------------
    # Final step: write remaining (last date) data
    # ----------------------------------------------------
    current_date_str = df['date'].iloc[-1]  # the final date in the batch
    file_path = os.path.join(folder, f"{current_date_str}.parquet")

    # Merge with existing file to avoid duplicates
    if os.path.exists(file_path):
        existing_df = pd.read_parquet(file_path)
        df = pd.concat([existing_df, df]).drop_duplicates().reset_index(drop=True)

    append_to_parquet(file_path, df)
    logging.info(f"Data saved successfully for {ticker} on {current_date_str}: {file_path}")

async def writer(queue, ticker, interval):
    """
    Asynchronous writer that consumes batches from the queue
    and writes them to disk, handling day boundaries.
    """
    current_day = datetime.utcnow().strftime("%Y-%m-%d")

    while True:
        item = await queue.get()
        if item is None:
            # "Poison pill" to signal shutdown
            queue.task_done()
            break

        batch_results, batch_day = item
        # Check if we've rolled over to a new day
        start_new_day = (batch_day != current_day)

        # Write batch to disk
        save_to_parquet(batch_results, ticker, interval, start_new_day)

        # If a new day has started, update current_day
        if start_new_day:
            current_day = batch_day

        queue.task_done()
        # Force garbage collection after writing
        gc.collect()


async def collect_data_continuous(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Continuously collects data in batches and places them on an async queue
    so that the writer can consume them without using excess memory.

    Args:
        client (CryptoAPITrading): API client for data retrieval.
        ticker (str): Cryptocurrency ticker symbol.
        interval (str): Data collection interval (default: '1s').
        batch_size (int): Number of data points per batch.

    Returns:
        None
    """
    # Create a limited-size queue to avoid large in-memory buildup
    queue = asyncio.Queue(maxsize=5)

    # Create the writer task which will continuously consume from queue
    writer_task = asyncio.create_task(writer(queue, ticker, interval))

    try:
        while True:
            # Collect a batch of data
            batch_results = await collect_data_async(client, ticker, batch_size, interval)
            logging.info(f"Collected a batch of {len(batch_results)} data points for {ticker}.")

            # Determine the day associated with this batch
            batch_day = datetime.utcnow().strftime("%Y-%m-%d")

            # Offload the batch to the writer
            await queue.put((batch_results, batch_day))

            # Brief sleep to yield control
            await asyncio.sleep(0.1)
    finally:
        # Put a "poison pill" to signal the writer to exit
        await queue.put(None)
        # Wait for the writer to finish
        await writer_task


def start_collection(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Entry point for data collection. Schedules the continuous collector
    using asyncio.run().

    Args:
        client (CryptoAPITrading): API client instance.
        ticker (str): Cryptocurrency ticker symbol.
        interval (str): Data collection interval.
        batch_size (int): Batch size for data collection.

    Returns:
        None
    """
    # Set up the log filename
    log_filename = f"{ticker}_{interval}.log"
    log_path = os.path.join(os.getcwd(), "logs")  # Ensure logs are stored in a dedicated folder
    os.makedirs(log_path, exist_ok=True)  # Create logs folder if it doesn't exist
    log_file = os.path.join(log_path, log_filename)

    # Configure logging to file + console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='a'),  # Append mode to continue logging
            logging.StreamHandler()  # Still log to console
        ]
    )

    logging.info(f"Starting data collection for {ticker} with interval {interval} and batch size {batch_size}")

    asyncio.run(collect_data_continuous(client, ticker, interval, batch_size))


if __name__ == '__main__':

    # Command-line interface for specifying ticker, interval, and batch size.
    parser = argparse.ArgumentParser(description='Collect ticker data continuously.')
    parser.add_argument('--ticker', type=str, required=True,
                        help='The ticker symbol to collect data for (e.g., BTC-USD).')
    parser.add_argument('--interval', type=str, default='1s',
                        help='The interval for data collection (e.g., 1s, 1m).')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE,
                        help='Batch size for data collection.')

    args = parser.parse_args()

    # Initialize the API client and start data collection.
    client = CryptoAPITrading()
    start_collection(client, args.ticker, interval=args.interval, batch_size=args.batch_size)
