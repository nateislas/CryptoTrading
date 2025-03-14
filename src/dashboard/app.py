# src/dashboard/app.py
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc
from . import utils, components, callbacks
import logging
import os
from threading import Timer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Cryptos to track
cryptos = ["BTC", "ETH"]

# Add crypto cards to layout
crypto_cards = dbc.Row([dbc.Col(components.generate_crypto_card(asset), width="auto") for asset in cryptos])

# Sidebar navigation
sidebar = dbc.Nav(
    [
        dbc.NavLink("Overview", id="overview-link", active=True, className="nav-link"),
        dbc.NavLink("Market Data", id="market-link", className="nav-link"),
        dbc.NavLink("Portfolio", id="portfolio-link", className="nav-link"),
        dbc.NavLink("About", id="about-link", className="nav-link"),
        dbc.Button("Toggle Dark Mode", id="toggle-theme", className="mt-3 btn btn-primary"),
    ],
    vertical=True,
    pills=True,
    className="bg-dark p-3",
    style={"width": "200px", "height": "100vh", "position": "fixed", "top": "0", "left": "0"}
)

# Main content
content = dbc.Container([
    html.H1("Robinhood Crypto Quant Lab", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Account Overview", className="card-title"),
                    html.P(id="account-number"),
                    html.P(id="buying-power", className="text-success"),
                ])
            ], className="mb-4 shadow-sm")
        ], width=4),
    ]),

    crypto_cards,  # Render cryptocurrency cards dynamically

    html.H2("Live Market Data"),
    dbc.Button("Toggle % / $ Change", id="toggle-change", className="mb-3", n_clicks=0),
    dash_table.DataTable(
        id="market-table",
        columns=[
            {"name": "Asset", "id": "asset"},
            {"name": "Price (USD)", "id": "price"},
            {"name": "Change", "id": "change"}
        ],
        data=[],
        style_table={"overflowX": "auto", "width": "80%", "margin": "auto"},
        style_cell={
            "textAlign": "center",
            "backgroundColor": "#2c2c2c",
            "color": "white",
            "padding": "5px",  # Reduce padding for smaller height
            "height": "20px",  # Reduce row height
        },
        style_header={
            "backgroundColor": "#4f4f4f",
            "fontWeight": "bold",
            "padding": "5px"
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#3a3a3a"}
        ]
    ),

    dcc.Interval(id="interval-update", interval=60000, n_intervals=0)
], fluid=True, style={"marginLeft": "220px", "padding": "20px"})

# Add to app layout
app.layout = html.Div([
    sidebar,
    content,
    dcc.Store(id="init-trigger", data={})  # Ensure store exists
])

# Register callbacks
callbacks.register_callbacks(app)

if __name__ == "__main__":
    port = utils.find_available_port()
    Timer(1, utils.open_browser, args=[port]).start()
    app.run_server(debug=True, port=port, use_reloader=False)