# src/dashboard/components.py
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import logging
from . import utils
# Configure logging if not already done in the main app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def generate_sparkline(asset_code):
    """Fetch historical price data and create a sparkline chart."""
    try:
        # Simulating historical data (replace with real-time data fetching)
        price_history = utils.fetch_daily_price(asset_code)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=price_history, mode="lines", line=dict(color="lightgreen", width=2), fill="none"))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=50,
            width=100
        )
        return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "50px", "width": "100px"})
    except Exception as e:
        logging.error(f"Error generating sparkline for {asset_code}: {e}")
        return "N/A"
def generate_crypto_card(asset_code):
    """Create a card layout for a cryptocurrency."""
    price = utils.fetch_asset_price(asset_code)
    percent_change, _ = utils.fetch_daily_changes(asset_code, price)
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(asset_code, style={"fontWeight": "bold", "fontSize": "16px"}),
                generate_sparkline(asset_code)
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
            html.Div([
                html.Div(f"${price:,.6f}" if price < 1 else f"${price:,.2f}", style={"fontSize": "14px"}),
                html.Div(f"{percent_change:.2f}%", style={"color": "green" if percent_change > 0 else "red", "fontSize": "14px"}),
            ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "5px"})
        ])
    , className="mb-3 shadow-sm", style={"width": "250px", "padding": "10px"})