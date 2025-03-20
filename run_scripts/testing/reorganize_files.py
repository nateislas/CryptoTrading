import os
import glob
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa

def consolidate_parquet_files_partitioned(ticker):
    """
    Merges all Parquet batch files into partitioned files (year/month/day) for faster queries.

    Args:
        ticker (str): The cryptocurrency ticker symbol (e.g., 'BTC-USD').

    Saves:
        Partitioned Parquet files in `/data/{ticker}/year=YYYY/month=MM/day=DD/`.
    """
    project_root = "/home/jetbot/Workspace/CryptoTrading"
    base_folder = os.path.join(project_root, "data", ticker, '1s')

    # Ensure base folder exists
    if not os.path.exists(base_folder):
        print(f"❌ Error: {base_folder} does not exist.")
        return

    # Find all date-based subfolders
    date_folders = sorted([f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))])

    for date_str in date_folders:
        source_folder = os.path.join(base_folder, date_str)
        parquet_files = sorted(glob.glob(os.path.join(source_folder, "*.parquet")))

        if not parquet_files:
            print(f"⚠️ No Parquet files found in {source_folder}. Skipping...")
            continue

        print(f"📂 Processing {len(parquet_files)} files in {source_folder}...")

        # Read and merge all Parquet files in the date folder
        df_list = [pd.read_parquet(f) for f in parquet_files]
        df = pd.concat(df_list, ignore_index=True)

        # ✅ Drop unnecessary columns
        columns_to_drop = ['quantity', 'side_bid', 'side_ask', 'date']
        df = df.drop(columns=columns_to_drop, errors='ignore')

        # ✅ Rename columns
        df = df.rename(columns={
            'price_bid': 'bid price',
            'price_ask': 'ask price',
            'timestamp': 'Date'
        })

        # ✅ Ensure timestamps are correctly formatted
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], utc=True)    # Convert to UTC
            df['Date'] = df['Date'].dt.tz_localize(None)         # Remove timezone
            df['Date'] = df['Date'].astype('datetime64[us]')     # ✅ Force microsecond precision
            df['year'] = df['Date'].dt.year
            df['month'] = df['Date'].dt.month
            df['day'] = df['Date'].dt.day
        else:
            print(f"❌ Error: 'Date' column missing in {source_folder}. Skipping...")
            continue

        # ✅ Ensure partition columns exist
        for col in ["year", "month", "day"]:
            if col not in df.columns:
                raise KeyError(f"❌ Error: Column '{col}' is missing. Data partitioning requires it!")

        # ✅ Reorder columns
        desired_column_order = [
            'Date', 'symbol', 'bid price', 'bid_inclusive_of_sell_spread',
            'sell_spread', 'ask price', 'ask_inclusive_of_buy_spread', 'buy_spread',
            'year', 'month', 'day'
        ]
        df = df[[c for c in desired_column_order if c in df.columns]]

        # ✅ Convert numeric columns to float32
        cols_to_convert = ['bid price', 'bid_inclusive_of_sell_spread',
                           'sell_spread', 'ask price', 'ask_inclusive_of_buy_spread', 'buy_spread']
        df[cols_to_convert] = df[cols_to_convert].astype(np.float32)

        print(df.head())

        # ✅ Define partitioned output directory
        partitioned_output_path = os.path.join(base_folder, '..')
        os.makedirs(partitioned_output_path, exist_ok=True)

        # ✅ Convert DataFrame to Arrow Table
        arrow_table = pa.Table.from_pandas(df, preserve_index=False)

        # ✅ Write partitioned Parquet
        pq.write_to_dataset(
            arrow_table,
            root_path=partitioned_output_path,
            partition_cols=['year', 'month', 'day'],
            compression='SNAPPY'
        )

        # ✅ Remove old unpartitioned files
        for f in parquet_files:
            os.remove(f)
        os.rmdir(source_folder)

        print(f"✅ Partitioned data saved in {partitioned_output_path}")

# Run partitioning
consolidate_parquet_files_partitioned("ETH-USD")
consolidate_parquet_files_partitioned("BTC-USD")