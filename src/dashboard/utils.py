import os
import socket
import webbrowser
import logging
from src.robinhood_api.api_access import CryptoAPITrading
from src.data_processing.data_utils import load_data
import os
import glob
import pandas as pd
import datetime
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the API client once
client = CryptoAPITrading()

def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def fetch_account_details():
    try:
        account_details = client.account.get_account()
        account_number = account_details.get("account_number", "N/A")
        buying_power = float(account_details.get("buying_power", "0"))
        return account_number, buying_power
    except Exception as e:
        logging.error("Error fetching account details: %s", e)
        return "N/A", 0.0

def fetch_asset_price(asset_code):
    try:
        price_data = client.market_data.get_estimated_price(f"{asset_code}-USD", "both", 1.0)
        if price_data and "results" in price_data:
            return float(price_data["results"][0]["price"])
        return None
    except Exception as e:
        logging.error("Error fetching price for %s: %s", asset_code, e)
        return None

def fetch_daily_changes(asset_code, current_price):
    """
    Returns the daily percent change and absolute dollar change.
    """
    try:
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        ohlc_data = load_data(
            ticker=f"{asset_code}-USD",
            start_date=today,
            end_date=today,
            ohlc_interval="1min"
        )
        if ohlc_data.empty:
            logging.error("No data found for %s on %s", asset_code, today)
            return None, None
        open_price = float(ohlc_data['open'].iloc[0])
        percent_change = ((current_price - open_price) / open_price) * 100
        dollar_change = current_price - open_price
        return round(percent_change, 2), round(dollar_change, 2)
    except Exception as e:
        logging.error("Error fetching daily changes for %s: %s", asset_code, e)
        return None, None

def fetch_holdings():
    """
    Retrieves the account holdings from the API.
    """
    try:
        holdings_data = client.account.get_holdings()
        if "results" in holdings_data:
            return holdings_data["results"]
        else:
            logging.warning("No 'results' field in holdings data.")
            return []
    except Exception as e:
        logging.error("Error fetching holdings: %s", e)
        return []

def calculate_daily_pnl():
    """
    Reads trade logs from disk, aggregates daily profit and loss, and returns
    the total PnL along with a Plotly bar chart.
    """
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        print(project_root)
        logs_dir = os.path.join(project_root, "logs", "trade_execution")
        if not os.path.exists(logs_dir):
            logging.warning("Logs directory not found: %s", logs_dir)
            return 0.0, go.Figure()
        csv_files = glob.glob(os.path.join(logs_dir, "*", "trades.csv"))
        if not csv_files:
            logging.warning("No trade logs found in: %s", logs_dir)
            return 0.0, go.Figure()
        daily_pnl = {}
        total_pnl = 0.0
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                closed_trades = df[df['status'] == 'CLOSED']
                date_str = os.path.basename(os.path.dirname(file))
                daily_pnl[date_str] = daily_pnl.get(date_str, 0) + closed_trades['pnl'].sum()
                total_pnl += closed_trades['pnl'].sum()
            except Exception as e:
                logging.error("Error processing file %s: %s", file, e)
        fig = go.Figure()
        for date, pnl in daily_pnl.items():
            fig.add_trace(go.Bar(
                x=[date],
                y=[pnl],
                marker_color='green' if pnl >= 0 else 'red'
            ))
        fig.update_layout(
            title='Daily PnL',
            xaxis_title='Date',
            yaxis_title='PnL',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )
        return round(total_pnl, 2), fig
    except Exception as e:
        logging.error("Error calculating daily PnL: %s", e)
        return 0.0, go.Figure()

# In src/dashboard/utils.py

def get_daily_pnl_data():
    """
    Reads trade logs, aggregates daily PnL, and returns
    a pandas DataFrame with columns ['date', 'daily_pnl'].
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    logs_dir = os.path.join(project_root, "logs", "trade_execution")

    # Dictionary to accumulate daily PnL keyed by date_str
    daily_pnl_dict = {}
    if not os.path.exists(logs_dir):
        logging.warning("Logs directory not found: %s", logs_dir)
        return pd.DataFrame(columns=["date", "daily_pnl"])

    csv_files = glob.glob(os.path.join(logs_dir, "*", "trades.csv"))
    if not csv_files:
        logging.warning("No trade logs found in: %s", logs_dir)
        return pd.DataFrame(columns=["date", "daily_pnl"])

    for file in csv_files:
        try:
            df = pd.read_csv(file)
            closed_trades = df[df['status'] == 'CLOSED']

            # The parent directory name might represent the date, e.g., logs/trade_execution/2023-03-25/trades.csv
            date_str = os.path.basename(os.path.dirname(file))

            daily_pnl_dict[date_str] = daily_pnl_dict.get(date_str, 0) + closed_trades['pnl'].sum()
        except Exception as e:
            logging.error("Error processing file %s: %s", file, e)

    # Convert the dict into a DataFrame, sorted by date
    daily_pnl_data = []
    for date_str, pnl_val in daily_pnl_dict.items():
        daily_pnl_data.append({
            "date": date_str,
            "daily_pnl": pnl_val
        })

    df_pnl = pd.DataFrame(daily_pnl_data)
    # Convert 'date' string to actual datetime if your folder names are date strings
    df_pnl['date'] = pd.to_datetime(df_pnl['date'], errors='coerce')
    df_pnl.sort_values(by='date', inplace=True)
    df_pnl.reset_index(drop=True, inplace=True)

    return df_pnl
