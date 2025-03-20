import nest_asyncio
import asyncio
import pandas as pd
import logging
import os
import glob
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime, timedelta
import argparse
import gc
from src.robinhood_api.api_access import CryptoAPITrading

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Interval options for API calls (in seconds)
INTERVAL_SECONDS = {'1s': 1, '1m': 60, '5m': 300, '30m': 1800}

# Default number of data points to collect per batch.
BATCH_SIZE = 250


def consolidate_parquet_files_partitioned(ticker):
    """
    Merges all Parquet files in the temp folder that belong to previous days
    into partitioned files (year/month/day) for faster queries.

    Expects filenames in the format:
        batch_YYYY-MM-DD_HHMMSS.parquet
    where YYYY-MM-DD is the UTC date for that file.

    Partitioned files are saved in data/{ticker}/.
    """
    project_root = os.getcwd()
    temp_folder = os.path.join(project_root, "data", ticker, "temp")

    if not os.path.exists(temp_folder):
        logging.getLogger(ticker).info(f"Error: {temp_folder} does not exist.")
        return

    # Collect all parquet files in the temp folder
    parquet_files_all = sorted(glob.glob(os.path.join(temp_folder, "*.parquet")))
    if not parquet_files_all:
        logging.getLogger(ticker).info(f"No Parquet files found in {temp_folder}. Skipping consolidation.")
        return

    logging.getLogger(ticker).info(f"Found {len(parquet_files_all)} total files in {temp_folder}.")

    # We'll keep only files with a date less than today's UTC date
    today_utc_date = datetime.utcnow().date()
    files_to_consolidate = []

    for filepath in parquet_files_all:
        filename = os.path.basename(filepath)  # e.g. "batch_2023-04-26_123456.parquet"
        parts = filename.split("_")
        # We expect [ "batch", "YYYY-MM-DD", "HHMMSS.parquet" ]
        if len(parts) < 3:
            continue  # Skip any file that doesn't match the pattern

        file_date_str = parts[1]  # e.g. "2023-04-26"
        try:
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
        except ValueError:
            # If we can't parse that date, skip this file
            continue

        # If the file's date is strictly before today's date, we will consolidate it
        if file_date < today_utc_date:
            files_to_consolidate.append(filepath)

    if not files_to_consolidate:
        logging.getLogger(ticker).info("No files to consolidate for previous day.")
        return

    logging.getLogger(ticker).info(f"Consolidating {len(files_to_consolidate)} file(s) from {temp_folder}...")

    # Read them all into one DataFrame
    df_list = [pd.read_parquet(fp) for fp in files_to_consolidate]
    df = pd.concat(df_list, ignore_index=True)

    # Drop columns that aren't needed
    columns_to_drop = ['quantity', 'side_bid', 'side_ask']
    df.drop(columns=columns_to_drop, errors='ignore', inplace=True)

    # Rename columns as needed
    df.rename(columns={
        'price_bid': 'bid price',
        'price_ask': 'ask price',
        'timestamp': 'Date'
    }, inplace=True)

    # Ensure 'Date' column exists and is properly typed
    if 'Date' not in df.columns:
        logging.getLogger(ticker).error("Error: 'Date' column missing in consolidated data. Skipping consolidation.")
        return

    df['Date'] = pd.to_datetime(df['Date'], utc=True)
    df['Date'] = df['Date'].dt.tz_localize(None)
    df['Date'] = df['Date'].astype('datetime64[us]')

    # Create partition columns based on the 'Date'
    df['year'] = df['Date'].dt.year
    df['month'] = df['Date'].dt.month
    df['day'] = df['Date'].dt.day

    # Reorder columns
    desired_column_order = [
        'Date', 'symbol', 'bid price', 'bid_inclusive_of_sell_spread',
        'sell_spread', 'ask price', 'ask_inclusive_of_buy_spread', 'buy_spread',
        'year', 'month', 'day'
    ]
    # Only keep columns that actually exist
    df = df[[c for c in desired_column_order if c in df.columns]]

    # Convert certain columns to float32 if they exist
    float_cols = [
        'bid price', 'bid_inclusive_of_sell_spread', 'sell_spread',
        'ask price', 'ask_inclusive_of_buy_spread', 'buy_spread'
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = df[col].astype(np.float32)

    # Write to partitioned dataset under data/{ticker}/
    partitioned_output_path = os.path.join(project_root, "data", ticker)
    os.makedirs(partitioned_output_path, exist_ok=True)

    arrow_table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(
        arrow_table,
        root_path=partitioned_output_path,
        partition_cols=['year', 'month', 'day'],
        compression='SNAPPY'
    )

    # Remove consolidated files from temp
    for fp in files_to_consolidate:
        os.remove(fp)

    logging.getLogger(ticker).info(f"Partitioned data saved in {partitioned_output_path}")


async def get_price(client, ticker):
    """
    Asynchronously calls client.market_data.get_estimated_price() to avoid blocking.
    """
    try:
        loop = asyncio.get_running_loop()
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
    """
    Collects a batch of data for a given ticker.
    """
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
    Converts batch results to a DataFrame and then splits it by day (UTC). Each group
    is saved as its own Parquet file in data/{ticker}/temp/.

    If a single batch spans multiple days (e.g., crosses midnight UTC), you'll get multiple
    output files, each containing only one date's data.

    File naming example:
        batch_20230424_093210.parquet
            ^^^^^^^^   ^^^^^^
            YYYYMMDD   HHMMSS
    """
    if not results:
        return

    # Build DataFrame from the combined bid/ask results
    bid_data = pd.DataFrame([r["results"][0] for r in results if r is not None])
    ask_data = pd.DataFrame([r["results"][1] for r in results if r is not None])
    df = pd.merge(bid_data, ask_data, on=["timestamp", "symbol", "quantity"], suffixes=("_bid", "_ask"))

    # Drop columns you don't need
    df.drop(columns=["quantity", "side_bid", "side_ask"], inplace=True)

    # Convert timestamp to UTC datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Create a separate column for the date (YYYY-MM-DD in UTC)
    df["date"] = df["timestamp"].dt.strftime("%Y-%m-%d")

    # Create the temp folder if it doesn't exist yet
    project_root = os.getcwd()
    temp_folder = os.path.join(project_root, "data", ticker, "temp")
    os.makedirs(temp_folder, exist_ok=True)

    # Group the data by the date column so each day’s records are separate
    for date_str, date_df in df.groupby("date"):
        # A file name that includes the day and a time stamp
        file_name = f"batch_{date_str}_{pd.Timestamp.utcnow().strftime('%H%M%S')}.parquet"
        file_path = os.path.join(temp_folder, file_name)

        date_df.to_parquet(file_path, compression="snappy", index=False)
        logging.getLogger(ticker).info(f"Saved daily batch for {ticker} — {date_str}: {file_path}")

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
        gc.collect()


async def collect_data_continuous(client, ticker, interval='1s', batch_size=BATCH_SIZE):
    """
    Continuously collects data for a given ticker and pushes each batch to a writer queue.
    """
    queue = asyncio.Queue(maxsize=5)
    writer_task = asyncio.create_task(writer(queue, ticker, interval))
    try:
        while True:
            batch_results = await collect_data_async(client, ticker, batch_size, interval)
            logging.getLogger(ticker).info(f"Collected a batch of {len(batch_results)} data points for {ticker}.")
            batch_day = datetime.utcnow().strftime("%Y-%m-%d")
            await queue.put((batch_results, batch_day))
            await asyncio.sleep(0.1)
    finally:
        await queue.put(None)
        await writer_task


async def new_day_watcher(tickers):
    """
    Waits until the next UTC midnight and then triggers consolidation for all tickers.
    Runs continuously to consolidate at the start of every new day.
    """
    while True:
        now = datetime.utcnow()
        tomorrow = now.date() + timedelta(days=1)
        next_midnight = datetime.combine(tomorrow, datetime.min.time())
        seconds_to_midnight = (next_midnight - now).total_seconds()
        logging.getLogger().info(
            f"New day watcher sleeping for {seconds_to_midnight:.0f} seconds until next consolidation...")
        await asyncio.sleep(seconds_to_midnight + 10)  # Add a small buffer.
        logging.getLogger().info("New day detected. Starting consolidation for all tickers...")
        for ticker in tickers:
            consolidate_parquet_files_partitioned(ticker)
        logging.getLogger().info("Consolidation complete for all tickers.")


async def main_collection(client, tickers, interval, batch_size):
    """
    Starts both the continuous data collection tasks for all tickers and the new day watcher concurrently.
    """
    data_tasks = [
        asyncio.create_task(collect_data_continuous(client, ticker, interval, batch_size))
        for ticker in tickers
    ]
    watcher_task = asyncio.create_task(new_day_watcher(tickers))
    await asyncio.gather(*data_tasks, watcher_task)


def start_collection(client, tickers, interval='1s', batch_size=BATCH_SIZE):
    """
    Configures logging and starts the asynchronous event loop.
    Logs are only written to files, not to the console.
    """
    log_path = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_path, exist_ok=True)

    root_logger = logging.getLogger()

    # Remove all existing handlers (console handlers)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(logging.INFO)

    for ticker in tickers:
        logger = logging.getLogger(ticker)

        # Remove previous handlers to avoid duplicates
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.setLevel(logging.INFO)
        log_file = os.path.join(log_path, f"{ticker}_{interval}.log")
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        logger.info(f"Configured logger for {ticker}")

    root_logger.info(
        f"Starting data collection for tickers: {', '.join(tickers)} with interval {interval} and batch size {batch_size}"
    )

    try:
        asyncio.run(main_collection(client, tickers, interval, batch_size))
    except KeyboardInterrupt:
        root_logger.info("Data collection interrupted. Exiting.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collect ticker data continuously.')
    parser.add_argument('--tickers', type=str, required=True,
                        help='Comma-separated ticker symbols (e.g., BTC-USD,ETH-USD)')
    parser.add_argument('--interval', type=str, default='1s',
                        help='Data collection interval (e.g., 1s, 1m)')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE,
                        help='Batch size for data collection.')
    args = parser.parse_args()

    tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    client = CryptoAPITrading()
    start_collection(client, tickers, interval=args.interval, batch_size=args.batch_size)