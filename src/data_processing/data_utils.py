import os
import glob
import pandas as pd
from decimal import Decimal, getcontext

# Set the precision you need
getcontext().prec = 28

def load_historical_data(ticker, data_interval, start_date=None, end_date=None, ohlc_interval=None):
    """
    Loads cryptocurrency market data from Parquet files, optionally resamples to OHLC data.

    Args:
        ticker (str): The cryptocurrency ticker symbol (e.g., 'BTC-USD').
        data_interval (str): The interval of the data files (e.g., '1s', '1min').
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
    if not isinstance(data_interval, str) or not data_interval:
        raise ValueError("data_interval must be a non-empty string.")
    if start_date is not None and not isinstance(start_date, str):
        raise ValueError("start_date must be a string or None.")
    if end_date is not None and not isinstance(end_date, str):
        raise ValueError("end_date must be a string or None.")
    if ohlc_interval is not None and not isinstance(ohlc_interval, str):
        raise ValueError("ohlc_interval must be a string or None.")

    # Define data path pattern
    path_pattern = os.path.join(project_root, 'data', ticker, data_interval, '*.parquet')
    files = glob.glob(path_pattern)

    df_list = []

    for file in files:
        date = os.path.basename(file).split('.')[0]

        # Load file if within date range or if no date range is specified
        if (start_date is None or end_date is None) or (start_date <= date <= end_date):
            df = pd.read_parquet(file)
            df_list.append(df)

    # Check if any data was loaded
    if not df_list:
        print(f"No data found for {ticker} in the specified date range.")
        return pd.DataFrame()  # Return empty DataFrame if no data

    # Concatenate all dataframes
    combined_df = pd.concat(df_list)

    # Ensure all types are correct
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], utc=True)

    #combined_df['price_bid'] = pd.to_numeric(combined_df['price_bid'], errors='coerce')
    #combined_df['price_ask'] = pd.to_numeric(combined_df['price_ask'], errors='coerce')
    #combined_df['bid_inclusive_of_sell_spread'] = pd.to_numeric(combined_df['bid_inclusive_of_sell_spread'],
    #                                                            errors='coerce')
    #combined_df['sell_spread'] = pd.to_numeric(combined_df['sell_spread'], errors='coerce')
    #combined_df['ask_inclusive_of_buy_spread'] = pd.to_numeric(combined_df['ask_inclusive_of_buy_spread'],
    #                                                           errors='coerce')
    #combined_df['buy_spread'] = pd.to_numeric(combined_df['buy_spread'], errors='coerce')

    # Drop specified columns
    columns_to_drop = ['quantity', 'side_bid', 'side_ask', 'date']
    combined_df = combined_df.drop(columns=columns_to_drop,
                                   errors='ignore')  # errors ignore will ignore columns that may have been removed when resampled

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

    else:
        return combined_df.reset_index(drop=True)