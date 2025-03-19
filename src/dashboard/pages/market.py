from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("Market Data", className="text-center my-4"),
    html.Div("Real-time market data for a broader set of cryptocurrencies."),
    # Future: Add a table or charts (e.g., a live market table) here
], fluid=True)
