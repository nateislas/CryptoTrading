import nest_asyncio
import asyncio
import aiohttp
import pandas as pd
import logging
import os
from datetime import datetime
import argparse
import gc
from src.robinhood_api.api_access import CryptoAPITrading

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Interval options for API calls (in seconds).
INTERVAL_SECONDS = {'1s': 1, '1m': 60, '5m': 300, '30m': 1800}

# Default number of data points to collect per batch.
BATCH_SIZE = 250

async def get_price(client, ticker):
    """
    Calls the old client.market_data.get_estimated_price(...) in a background executor
    to avoid blocking the event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        # The same call your old script made successfully:
        response = await loop.run_in_executor(
            None,
            client.market_data.get_estimated_price,
            ticker,
            "both",
            1.0
        )
        if "error_code" in response:
            logging.getLogger(ticker).error(f"Robinhood error for {ticker}: {response['error_code']}")
            return None
        return response
    except Exception as e:
        logging.getLogger(ticker).error(f"Exception for {ticker}: {e}")
        return None

async def collect_data_async(client, ticker, batch_size, interval):
    interval_seconds = INTERVAL_SECONDS.get(interval, 1)
    batch_results = []
    for _ in range(batch_size):
        response = await get_price(client, ticker)
        if response:
            batch_results.append(response)
        await asyncio.sleep(interval_seconds)
    return batch_results

def save_to_parquet(results, ticker, interval):
    """
    Splits the batch by date and saves each subset separately in the correct date folder.
    """
    if not results:
        return

    # Convert results to DataFrame.
    # Note: Adjust this if the response format changes when using multiple tickers.
    bid_data = pd.DataFrame([r["results"][0] for r in results if r is not None])
    ask_data = pd.DataFrame([r["results"][1] for r in results if r is not None])
    df = pd.merge(bid_data, ask_data, on=["timestamp", "symbol", "quantity"], suffixes=("_bid", "_ask"))

    # Drop unnecessary columns.
    df.drop(columns=["quantity", "side_bid", "side_ask"], inplace=True)

    # Ensure timestamp is in UTC and extract date.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")

    project_root = os.getcwd()

    # Use groupby to process each unique date.
    for date, date_df in df.groupby("date"):
        date_folder = os.path.join(project_root, "data", ticker, interval, date)
        os.makedirs(date_folder, exist_ok=True)
        batch_filename = os.path.join(date_folder, f"batch_{pd.Timestamp.utcnow().strftime('%H%M%S')}.parquet")
        date_df.to_parquet(batch_filename, compression="snappy", index=False)
        logging.getLogger(ticker).info(f"Saved batch for {ticker} on {date}: {batch_filename}")

async def writer(queue, ticker, interval):
    """
    Asynchronous writer that consumes batches from the queue and writes them to disk.
    """
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        batch_results, batch_day = item
        save_to_parquet(batch_results, ticker, interval)
        queue.task_done()
        # Optionally remove forced garbage collection if not needed.
        gc.collect()

async def collect_data_continuous(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    # Create a limited-size queue to avoid large in-memory buildup
    queue = asyncio.Queue(maxsize=5)
    # Create the writer task which will continuously consume from queue
    writer_task = asyncio.create_task(writer(queue, ticker, interval))

    try:
        while True:
            # Collect a batch of data (now returns a list, not using a queue)
            batch_results = await collect_data_async(client, ticker, batch_size, interval)
            logging.getLogger(ticker).info(f"Collected a batch of {len(batch_results)} data points for {ticker}.")

            # Determine the day associated with this batch
            batch_day = datetime.utcnow().strftime("%Y-%m-%d")
            # Offload the batch to the writer
            await queue.put((batch_results, batch_day))
            # Brief sleep to yield control
            await asyncio.sleep(0.1)
    finally:
        # Signal the writer to exit
        await queue.put(None)
        await writer_task

async def main_collection(client, tickers, interval, batch_size):
    """
    Runs data collection concurrently for all tickers.
    """
    tasks = []
    for ticker in tickers:
        logging.getLogger(ticker).info(f"Starting collection for ticker {ticker}")
        tasks.append(collect_data_continuous(client, ticker, interval, batch_size))
    await asyncio.gather(*tasks)

def start_collection(client, tickers, interval='1s', batch_size=BATCH_SIZE):
    log_path = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_path, exist_ok=True)

    # Set the root logger to INFO so that all child loggers will at least log INFO.
    # (We won't call basicConfig again.)
    logging.getLogger().setLevel(logging.INFO)

    # Also attach a StreamHandler to the root logger so we see logs in console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(console_handler)

    # Create a dedicated logger for each ticker
    for ticker in tickers:
        logger = logging.getLogger(ticker)  # named logger for this ticker
        logger.setLevel(logging.INFO)       # or logging.DEBUG, etc.

        # Set up a FileHandler for this ticker
        log_file = os.path.join(log_path, f"{ticker}_{interval}.log")
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        # Attach the FileHandler to this ticker's logger
        logger.addHandler(file_handler)

        # Log an initial message
        logger.info(f"Configured logger for {ticker}")

    # Then inside main_collection or collect_data..., use the named logger:
    # e.g.: logging.getLogger(ticker).info("Starting data collection...")
    logging.getLogger().info(f"Starting data collection for tickers: {', '.join(tickers)} "
                             f"with interval {interval} and batch size {batch_size}")

    asyncio.run(main_collection(client, tickers, interval, batch_size))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collect ticker data continuously.')
    # Accept comma-separated tickers.
    parser.add_argument('--tickers', type=str, required=True,
                        help='Comma-separated ticker symbols to collect data for (e.g., BTC-USD,ETH-USD)')
    parser.add_argument('--interval', type=str, default='1s',
                        help='Data collection interval (e.g., 1s, 1m)')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE,
                        help='Batch size for data collection.')

    args = parser.parse_args()

    # Split tickers by comma and strip whitespace.
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    client = CryptoAPITrading()
    start_collection(client, tickers, interval=args.interval, batch_size=args.batch_size)