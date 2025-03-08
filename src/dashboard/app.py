from src.robinhood_api.api_access import CryptoAPITrading
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import logging
import webbrowser
from threading import Timer
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to find an available port
def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def fetch_account_details(client):
    """Fetches account details and handles potential errors."""
    try:
        account_details = client.account.get_account()
        if account_details:
            account_number = account_details.get("account_number", "N/A")
            buying_power = float(account_details.get("buying_power", "0"))
            return account_number, buying_power
        else:
            logging.error("Failed to fetch account details.")
            return "N/A", 0.0
    except Exception as e:
        logging.error(f"An error occurred while fetching account details: {e}")
        return "N/A", 0.0

def fetch_holdings(client):
    """Fetches holdings and handles potential errors."""
    try:
        holdings_data = client.account.get_holdings()
        if holdings_data and "results" in holdings_data:
            return holdings_data["results"]
        else:
            logging.error("Failed to fetch holdings data.")
            return []
    except Exception as e:
        logging.error(f"An error occurred while fetching holdings: {e}")
        return []

def fetch_asset_price(client, asset_code):
    """Fetches the price for a single asset and handles potential errors."""
    try:
        price_data = client.market_data.get_estimated_price(f"{asset_code}-USD", "both", 1.0)
        if price_data and "results" in price_data and len(price_data["results"]) > 0:
            price_info = price_data["results"][0]
            if "price" in price_info:
                return float(price_info["price"])
            else:
                logging.error(f"Price info is invalid for {asset_code}.")
                return None
        else:
            logging.error(f"Failed to fetch price data for {asset_code}.")
            return None
    except Exception as e:
        logging.error(f"An error occurred while fetching price for {asset_code}: {e}")
        return None

# Initialize Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create an instance of the CryptoAPITrading which accesses the Robinhood API
client = CryptoAPITrading()

# Fetch account details
account_number, buying_power = fetch_account_details(client)

# App layout with a dark gray background
app.layout = dbc.Container([
    html.H1(
        "Trading Dashboard",
        className="text-center my-4",
        style={"fontWeight": "bold", "color": "white"}
    ),

    dbc.Card([
        dbc.CardBody([
            html.H3(f"Account Number: {account_number}", className="card-title", style={"color": "white"}),
            html.H3(f"Buying Power: ${buying_power:,.2f}", className="card-text text-success"),
        ])
    ], className="mb-4 shadow-sm", style={"backgroundColor": "#2c2c2c", "border": "none"}),

    html.H2("Holdings", className="my-4", style={"color": "white"}),

    dash_table.DataTable(
        id="holdings-table",
        columns=[
            {"name": "Asset Code", "id": "asset_code"},
            {"name": "Quantity", "id": "total_quantity"},
            {"name": "Price (USD)", "id": "price"}
        ],
        data=[],
        style_table={"overflowX": "auto", "border": "1px solid #ddd", "boxShadow": "0px 2px 5px rgba(0, 0, 0, 0.5)"},
        style_cell={
            "textAlign": "center",
            "padding": "10px",
            "fontFamily": "Arial, sans-serif",
            "backgroundColor": "#2c2c2c",
            "color": "white",
        },
        style_header={
            "backgroundColor": "#4f4f4f",
            "fontWeight": "bold",
            "borderBottom": "1px solid #ccc",
            "fontSize": "16px",
            "color": "white",
        },
        style_data={
            "backgroundColor": "#3a3a3a",
            "borderBottom": "1px solid #555",
            "fontSize": "14px",
            "color": "white",
        },
    ),

    # Interval component to trigger updates every 10 seconds
    dcc.Interval(
        id="interval-component",
        interval= 1000,  # 10 seconds in milliseconds
        n_intervals=0
    )
], fluid=True, style={"backgroundColor": "#1c1c1c", "padding": "20px"})

# Callback to update holdings table every 10 seconds
@app.callback(
    Output("holdings-table", "data"),
    Input("interval-component", "n_intervals")
)
def update_holdings(n):
    # Fetch holdings from the API
    holdings = fetch_holdings(client)
    # Add price for each asset
    updated_data = []
    for asset in holdings:
        asset_code = asset["asset_code"]
        quantity = float(asset["total_quantity"])

        # Fetch price for the asset
        price = fetch_asset_price(client,asset_code)

        updated_data.append({
            "asset_code": asset_code,
            "total_quantity": quantity,
            "price": f"${price:,.2f}" if price else "N/A"
        })
    return updated_data

# Function to open a browser tab
def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

# Run the app with dynamic port and automatic browser tab
if __name__ == "__main__":
    port = find_available_port()
    Timer(1, open_browser, args=[port]).start()
    app.run_server(debug=True, port=port)