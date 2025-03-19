from dash import html, dcc
import dash_bootstrap_components as dbc
from src.robinhood_api.api_access import CryptoAPITrading
from src.data_processing.data_utils import load_data
import datetime
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the API client
api_trading_client = CryptoAPITrading()

def generate_crypto_card(ticker):
    """
    Generates a card widget for the given crypto asset.
    """
    try:
        best_bid_ask = api_trading_client.market_data.get_best_bid_ask(f"{ticker}-USD")
        current_price = float(best_bid_ask['results'][0]['price'])
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        historical_data = load_data(
            ticker=f"{ticker}-USD",
            start_date=yesterday.strftime('%Y-%m-%d'),
            end_date=now.strftime('%Y-%m-%d'),
            ohlc_interval='1min'
        )
        if not historical_data.empty:
            open_price = historical_data['open'].iloc[0]
            percent_change = ((current_price - open_price) / open_price) * 100
        else:
            percent_change = 0.0
            logging.warning("No historical data found for %s", ticker)
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
            style={"width": "18rem", "margin": "10px"}
        )
        return card
    except Exception as e:
        logging.error("Error generating card for %s: %s", ticker, e)
        return dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H5(ticker, className="card-title", style={"fontSize": "16px"}),
                        html.Div("Error fetching data", className="card-text", style={"fontSize": "18px", "color": "red"}),
                    ]
                )
            ],
            style={"width": "18rem", "margin": "10px"}
        )

def create_crypto_graph_plotly(df, chart_type="candlestick"):
    """
    Creates Plotly graphs for the price (candlestick or line chart) and volume.
    Returns HTML snippets for embedding.
    """
    if chart_type == "candlestick":
        fig_price = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='green',
            decreasing_line_color='red'
        )])
    elif chart_type == "line":
        fig_price = go.Figure(data=[go.Scatter(
            x=df['Date'],
            y=df['close'],
            mode='lines',
            line=dict(color='cyan')
        )])
    else:
        fig_price = go.Figure()

    fig_price.update_layout(
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark"
    )

    colors = ['green' if row['close'] >= row['open'] else 'red' for _, row in df.iterrows()]
    fig_volume = go.Figure(data=[go.Bar(
        x=df['Date'],
        y=df['volume'],
        marker_color=colors
    )])
    fig_volume.update_layout(
        xaxis_title="Date",
        yaxis_title="Volume",
        template="plotly_dark"
    )

    price_html = pio.to_html(fig_price, full_html=False, include_plotlyjs='cdn')
    volume_html = pio.to_html(fig_volume, full_html=False, include_plotlyjs=False)
    return price_html, volume_html

def get_crypto_data_and_graphs(crypto_symbol, chart_type="candlestick"):
    """
    Retrieves historical data for the given asset and returns Plotly-generated HTML
    for both price and volume charts.
    """
    with open('src/robinhood_api/keys/polygon_key.txt', 'r') as file:
        api_key = file.read().strip()
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    df = load_data(
        ticker=f"{crypto_symbol}-USD",
        start_date=today,
        end_date=today,
        ohlc_interval="5min"
    )
    if 'volume' not in df.columns or df['volume'].isnull().all():
        df['volume'] = 100  # Fallback volume
    price_html, volume_html = create_crypto_graph_plotly(df, chart_type=chart_type)
    return df, {"price_html": price_html, "volume_html": volume_html}

def portfolio_value_chart():
    """
    Returns a placeholder Plotly chart for portfolio value.
    """
    fig = go.Figure()
    fig.update_layout(
        title="Portfolio Value",
        xaxis_title="Time",
        yaxis_title="Value",
        template="plotly_dark"
    )
    return dcc.Graph(figure=fig)

def holdings_table():
    """
    Returns a placeholder table of holdings.
    """
    table_header = html.Thead(
        html.Tr([html.Th("Asset"), html.Th("Quantity"), html.Th("Value")])
    )
    table_body = html.Tbody(
        [
            html.Tr([html.Td("BTC"), html.Td("0.5"), html.Td("$20,000")]),
            html.Tr([html.Td("ETH"), html.Td("10"), html.Td("$15,000")])
        ]
    )
    return dbc.Table(table_header + [table_body], bordered=True, dark=True, hover=True, responsive=True)

def market_data_table():
    """
    Returns a placeholder table for live market data.
    """
    table_header = html.Thead(
        html.Tr([html.Th("Asset"), html.Th("Price"), html.Th("Change")])
    )
    table_body = html.Tbody(
        [
            html.Tr([html.Td("BTC"), html.Td("$30,000"), html.Td("5%")]),
            html.Tr([html.Td("ETH"), html.Td("$2,000"), html.Td("3%")])
        ]
    )
    return dbc.Table(table_header + [table_body], bordered=True, dark=True, hover=True, responsive=True)
