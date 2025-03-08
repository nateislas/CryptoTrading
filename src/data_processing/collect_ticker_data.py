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

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Interval in seconds: change this to control the pause between API calls.
INTERVAL_SECONDS = {'1s': 1, '1m': 60, '5m': 300, '30m': 1800}

# How many data points to collect per batch before saving
BATCH_SIZE = 5  # You can adjust this based on memory/performance

async def get_price(session, client, ticker):
    try:
        loop = asyncio.get_event_loop()
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
    """Collect a batch of data points asynchronously."""
    interval_seconds = INTERVAL_SECONDS[interval]
    batch_results = []
    async with aiohttp.ClientSession() as session:
        for _ in range(batch_size):
            # Start a new task for each API call
            task = asyncio.create_task(get_price(session, client, ticker))
            result = await task
            batch_results.append(result)
            await asyncio.sleep(interval_seconds)
    return batch_results

def save_to_parquet(results, ticker):
    bid_data = pd.DataFrame([res['results'][0] for res in results if res is not None])
    ask_data = pd.DataFrame([res['results'][1] for res in results if res is not None])

    df = pd.merge(bid_data, ask_data, on=['timestamp', 'symbol', 'quantity'], suffixes=('_bid', '_ask'))

    # Convert timestamp to datetime object if not already
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Set project root explicitly to the parent directory of the current working directory
    project_root = os.path.abspath(os.path.join(os.getcwd()))

    # Define the correct folder path relative to the project root
    folder = os.path.join(project_root, 'data', ticker)
    os.makedirs(folder, exist_ok=True)

    # Use current date to partition data
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    file_path = os.path.join(folder, f"{date_str}.parquet")

    # Append if file exists, otherwise create new
    if os.path.exists(file_path):
        existing_df = pd.read_parquet(file_path)
        df = pd.concat([existing_df, df]).drop_duplicates().reset_index(drop=True)

    # Save DataFrame with efficient compression
    df.to_parquet(file_path, index=False, compression='snappy')

    logging.info(f"Data saved successfully for {ticker}: {file_path}")

async def collect_data_continuous(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Continuously collect data in batches and flush to disk when the batch grows too large
    or when the day changes.
    """
    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    all_results = []  # Accumulate results in memory for a batch

    while True:
        # Collect one batch of data
        batch_results = await collect_data_async(client, ticker, batch_size, interval)
        all_results.extend(batch_results)
        logging.info(f"Collected batch of {len(batch_results)} data points for {ticker}.")

        # Check if the day has changed (UTC) or if we have a lot of data accumulated.
        new_day = datetime.utcnow().strftime("%Y-%m-%d")
        if new_day != current_day or len(all_results) >= (batch_size * 2):
            # Save accumulated data to disk
            save_to_parquet(all_results, ticker)
            all_results = []  # Reset batch memory
            current_day = new_day

        # Optionally, you can insert a small sleep here to yield control.
        await asyncio.sleep(0.1)

def start_collection(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Wrapper to run the continuous collection coroutine.
    """
    asyncio.run(collect_data_continuous(client, ticker, interval, batch_size))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collect ticker data continuously.')
    parser.add_argument('--ticker', type=str, required=True, help='The ticker symbol to collect data for (e.g., BTC-USD).')
    parser.add_argument('--interval', type=str, default='1s', help='The interval for data collection (e.g., 1s, 1m).')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE, help='Batch size for data collection.')

    args = parser.parse_args()

    client = CryptoAPITrading()
    start_collection(client, args.ticker, interval=args.interval, batch_size=args.batch_size)