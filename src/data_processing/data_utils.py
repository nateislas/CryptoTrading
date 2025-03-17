import os
import glob
import pandas as pd
from decimal import Decimal, getcontext

# Set the precision you need
getcontext().prec = 28

import os
import glob
import pandas as pd
import numpy as np

def load_historical_data(ticker, start_date=None, end_date=None, ohlc_interval=None):
    """
    Loads cryptocurrency market data from Parquet batch files stored by date folders.

    Args:
        ticker (str): The cryptocurrency ticker symbol (e.g., 'BTC-USD').
        start_date (str, optional): The start date for data retrieval (YYYY-MM-DD). Defaults to None.
        end_date (str, optional): The end date for data retrieval (YYYY-MM-DD). Defaults to None.
        ohlc_interval (str, optional): The interval for OHLC resampling (e.g., '1min', '5min'). If None, no resampling is performed. Defaults to None.

    Returns:
        pd.DataFrame: A DataFrame containing the loaded data, or an empty DataFrame if no data is found.
    """
    # Automatically determine the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Validate Inputs
    if not isinstance(ticker, str) or not ticker:
        raise ValueError("ticker must be a non-empty string.")
    if start_date is not None and not isinstance(start_date, str):
        raise ValueError("start_date must be a string or None.")
    if end_date is not None and not isinstance(end_date, str):
        raise ValueError("end_date must be a string or None.")
    if ohlc_interval is not None and not isinstance(ohlc_interval, str):
        raise ValueError("ohlc_interval must be a string or None.")

    # Define data directory pattern
    data_dir = os.path.join(project_root, 'data', ticker, '1s')
    if not os.path.exists(data_dir):
        print(f"No data directory found for {ticker} at interval {'1s'}.")
        return pd.DataFrame()

    # List all date-based folders
    date_folders = sorted([folder for folder in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, folder))])

    # Apply date filters if provided
    if start_date:
        date_folders = [folder for folder in date_folders if folder >= start_date]
    if end_date:
        date_folders = [folder for folder in date_folders if folder <= end_date]

    df_list = []

    # Iterate over date folders and load all batch files within each day
    for date_folder in date_folders:
        batch_files = glob.glob(os.path.join(data_dir, date_folder, "*.parquet"))
        if not batch_files:
            continue  # Skip folders with no files

        daily_df_list = [pd.read_parquet(batch) for batch in batch_files]
        daily_df = pd.concat(daily_df_list, ignore_index=True)

        df_list.append(daily_df)

    # Check if any data was loaded
    if not df_list:
        print(f"No data found for {ticker} in the specified date range.")
        return pd.DataFrame()

    # Concatenate all daily dataframes
    combined_df = pd.concat(df_list, ignore_index=True)

    # Ensure timestamps are correct
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], utc=True)

    # Drop specified columns
    columns_to_drop = ['quantity', 'side_bid', 'side_ask', 'date']
    combined_df = combined_df.drop(columns=columns_to_drop, errors='ignore')

    # Rename columns
    combined_df = combined_df.rename(columns={
        'price_bid': 'bid price',
        'price_ask': 'ask price',
        'timestamp': 'Date'
    })

    # Reorganize columns
    desired_column_order = [
        'Date',
        'symbol',
        'bid price',
        'bid_inclusive_of_sell_spread',
        'sell_spread',
        'ask price',
        'ask_inclusive_of_buy_spread',
        'buy_spread',
    ]

    # Get the columns that exist in the current DataFrame and are in the desired order list.
    present_columns = [col for col in desired_column_order if col in combined_df.columns]
    combined_df = combined_df[present_columns]

    # Sort data by 'Date' since batches are not necessarily saved in order
    combined_df = combined_df.sort_values(by='Date', ascending=True).reset_index(drop=True)

    # Define the columns to convert
    cols_to_convert = [
        'bid price', 'bid_inclusive_of_sell_spread',
        'sell_spread', 'ask price', 'ask_inclusive_of_buy_spread',
        'buy_spread'
    ]

    # Convert the columns to float64 for high precision
    combined_df[cols_to_convert] = combined_df[cols_to_convert].astype(np.float64)

    # Optionally resample to OHLC
    if ohlc_interval:
        if 'bid price' not in combined_df.columns:
            raise ValueError("bid price column must be in the dataset to resample")
        combined_df.set_index('Date', inplace=True)
        ohlc_df = combined_df['bid price'].resample(ohlc_interval).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
        )
        ohlc_df = ohlc_df.reset_index()
        return ohlc_df

    return combined_df.reset_index(drop=True)


import os
import pandas as pd
from datetime import datetime, timedelta

def load_trades(start_date=None, end_date=None):
    """
    Loads trade logs within a specified date range and calculates slippage.

    Args:
        start_date (str or None): Start date in 'YYYY-MM-DD' format. If None, loads all available data.
        end_date (str or None): End date in 'YYYY-MM-DD' format. If None, loads all available data.

    Returns:
        pd.DataFrame: DataFrame containing trade data with calculated slippage.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    logs_dir = os.path.join(project_root, "logs", "trade_execution")

    # Ensure directory exists
    if not os.path.exists(logs_dir):
        raise FileNotFoundError(f"Logs directory not found: {logs_dir}")

    # Parse date range
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_date = datetime.now()  # Default to today

    # Collect relevant files
    trade_files = []
    for file in os.listdir(logs_dir):
        if file.startswith("trade_log_") and file.endswith(".csv"):
            file_date_str = file.replace("trade_log_", "").replace(".csv", "")
            try:
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                if (not start_date or file_date >= start_date) and (file_date <= end_date):
                    trade_files.append(os.path.join(logs_dir, file))
            except ValueError:
                continue  # Skip files with incorrect naming formats

    if not trade_files:
        raise FileNotFoundError(f"No trade logs found in range {start_date} to {end_date}")

    # Load data
    trades = pd.concat([pd.read_csv(file) for file in trade_files], ignore_index=True)

    # Ensure datetime format
    trades["Buy Timestamp"] = pd.to_datetime(trades["Buy Timestamp"])
    trades["Sell Timestamp"] = pd.to_datetime(trades["Sell Timestamp"])

    # Calculate slippage
    trades["Estimated Slippage (Buy)"] = trades["Estimated Price (Buy)"] - trades["Best Ask (Buy)"]
    trades["Actual Slippage (Buy)"] = trades["Buy Price"] - trades["Best Ask (Buy)"]
    trades["Estimated Slippage (Sell)"] = trades["Estimated Price (Sell)"] - trades["Best Bid (Sell)"]
    trades["Actual Slippage (Sell)"] = trades["Sell Price"] - trades["Best Bid (Sell)"]

    trades["Trade Duration (s)"] = (trades["Sell Timestamp"] - trades["Buy Timestamp"]).dt.total_seconds()

    return trades