# src/dashboard/components.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from src.robinhood_api.api_access import CryptoAPITrading  # Import your API class
from src.data_processing.data_utils import load_historical_data  # Import your data loading function
import datetime
import logging
import requests
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.io import curdoc, reset_output
from bokeh.document import Document
from bokeh.models import HoverTool
from bokeh.document import Document
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.plotting import figure
from bokeh.embed import components
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the API client globally
api_trading_client = CryptoAPITrading()


def generate_crypto_card(ticker):
    """Generates a crypto card for the dashboard."""
    try:
        # Fetch real-time price data
        best_bid_ask = api_trading_client.market_data.get_best_bid_ask(f"{ticker}-USD")
        current_price = float(best_bid_ask['results'][0]['price'])

        # Fetch historical data for 24-hour change
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        today_str = now.strftime('%Y-%m-%d')

        historical_data = load_historical_data(ticker=f"{ticker}-USD", start_date=yesterday_str, end_date=today_str,
                                               data_interval='1s', ohlc_interval='1min')

        if not historical_data.empty:
            open_price_24h_ago = historical_data['open'].iloc[0]
            percent_change = ((current_price - open_price_24h_ago) / open_price_24h_ago) * 100
        else:
            percent_change = 0.0  # Default to 0 if no historical data
            logging.warning(f"No historical data found for {ticker}. Setting percent change to 0.")

        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H5(ticker, className="card-title", style={"fontSize": "16px"}),
                        html.Div(f"${current_price:.2f}", className="card-text", style={"fontSize": "18px"}),
                        html.Div(f"{percent_change:.2f}%",
                                 style={"color": "green" if percent_change > 0 else "red", "fontSize": "14px"}),
                    ]
                )
            ],
            style={"width": "18rem", "margin": "10px"},
        )
    except Exception as e:
        logging.error(f"Error generating card for {ticker}: {e}")
        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H5(ticker, className="card-title", style={"fontSize": "16px"}),
                        html.Div("Error fetching data", className="card-text",
                                 style={"fontSize": "18px", "color": "red"}),
                    ]
                )
            ],
            style={"width": "18rem", "margin": "10px"},
        )
    return card

def get_polygon_data(crypto_symbol, start_date, end_date, api_key):
    """Fetches and processes data from Polygon.io for a given crypto symbol."""
    symbol = f"X:{crypto_symbol}USD"  # Crypto symbol (BASE-QUOTE)
    multiplier = 1
    timespan = "minute"
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}?apiKey={api_key}"
    response = requests.get(url).json()
    if response.get('results'):
        df = pd.DataFrame(response["results"])
        df["Date"] = pd.to_datetime(df["t"], unit="ms")
        df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}, inplace=True)
        df = df[["Date", "open", "high", "low", "close", "volume"]]
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame()

def create_crypto_graph_bokeh(df):
    """
    Creates a Bokeh candlestick chart and volume bar chart for cryptocurrency price visualization.
    Uses only one HoverTool renderer on the candle bodies to avoid duplicate tooltips.
    """

    doc = Document()

    # Determine candle color
    df["color"] = np.where(df["close"] > df["open"], "green", "red")

    source = ColumnDataSource(df)

    # Candlestick width in ms
    if len(df) > 1:
        time_diffs = np.diff(df['Date'].astype(np.int64))
        avg_interval_ns = np.mean(time_diffs)
        w = avg_interval_ns / 1e6
    else:
        w = 60000

    # Price figure
    p_price = figure(
        x_axis_type="datetime",
        width=900,
        height=400,
        background_fill_color="black",
        border_fill_color="black",
        sizing_mode="stretch_width",
        toolbar_location="above",
        tools="xpan,xwheel_zoom,reset,save"
    )

    # Wick (segment). We'll keep this for visuals,
    # but not attach it to the hover tool.
    wick_glyph = p_price.segment(
        'Date', 'high', 'Date', 'low',
        source=source,
        color="white"
    )

    # Candle bodies (vbar). We'll attach the hover tool to this renderer.
    candle_bodies = p_price.vbar(
        x='Date',
        width=w,
        top='open',
        bottom='close',
        source=source,
        fill_color="color",
        line_color="color",
        alpha=0.8
    )

    # Create a hover tool for price chart, restricted to vbar only:
    hover_tool_price = HoverTool(
        tooltips=[
            ("Date", "@Date"),
            ("Open", "@open{0.2f}"),
            ("High", "@high{0.2f}"),
            ("Low", "@low{0.2f}"),
            ("Close", "@close{0.2f}")
        ],
        formatters={"@Date": "datetime"},
        mode="vline",
        show_arrow=True,
        renderers=[candle_bodies]  # <--- key to avoid duplicates
    )
    p_price.add_tools(hover_tool_price)

    p_price.title.text = "Crypto Price"
    p_price.xaxis.axis_label = "Date"
    p_price.yaxis.axis_label = "Price"
    p_price.grid.grid_line_alpha = 0.3

    # Volume figure (linked x-range)
    p_vol = figure(
        x_axis_type="datetime",
        width=900,
        height=150,
        background_fill_color="black",
        border_fill_color="black",
        sizing_mode="stretch_width",
        tools="xpan,xwheel_zoom,reset,save",
        x_range=p_price.x_range
    )

    vol_bars = p_vol.vbar(
        x="Date",
        top="volume",
        width=w,
        source=source,
        fill_color="color",
        line_color="color",
        alpha=0.8
    )

    # Hover tool for volume figure, restricted to the volume bars only
    hover_tool_volume = HoverTool(
        tooltips=[
            ("Date", "@Date"),
            ("Volume", "@volume{0.2f}")
        ],
        formatters={"@Date": "datetime"},
        mode="vline",
        show_arrow=True,
        renderers=[vol_bars]
    )
    p_vol.add_tools(hover_tool_volume)

    p_vol.title.text = "Trading Volume"
    p_vol.xaxis.axis_label = "Date"
    p_vol.yaxis.axis_label = "Volume"
    p_vol.grid.grid_line_alpha = 0.3

    # Add both plots to the Document
    doc.add_root(p_price)
    doc.add_root(p_vol)

    # Convert to script & div
    price_script, price_div = components(p_price, doc)
    volume_script, volume_div = components(p_vol, doc)

    # Clear the doc
    doc.clear()

    return price_script, price_div, volume_script, volume_div

def create_crypto_graph(df):
    """
    Bokeh version: Returns script/div pairs for candlestick and volume charts.
    """
    from bokeh.embed import components

    price_script, price_div, volume_script, volume_div = create_crypto_graph_bokeh(df)
    # We'll return them as a dictionary for convenience
    return {
        "price_script": price_script,
        "price_div": price_div,
        "volume_script": volume_script,
        "volume_div": volume_div
    }


def get_crypto_data_and_graphs(crypto_symbol):
    """
    Fetches crypto data and returns Bokeh script/div for both charts.
    """
    # Read API key from file
    with open('src/robinhood_api/keys/polygon_key.txt', 'r') as file:
        api_key = file.read().strip()

    yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    # Assume you have get_polygon_data that returns a DataFrame
    df = get_polygon_data(crypto_symbol=crypto_symbol,
                          start_date=yesterday,
                          end_date=yesterday,
                          api_key=api_key)

    bokeh_plots = create_crypto_graph(df)  # returns a dict of script/div
    return df, bokeh_plots