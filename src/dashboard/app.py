# src/dashboard/app.py
from dash import Dash, html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
from . import utils, components
import logging
import os
from threading import Timer
import requests
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Output, Input, State  # Import Output, Input, State
from flask import Flask, render_template_string
from bokeh.embed import file_html
from bokeh.resources import CDN

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"], suppress_callback_exceptions=True)
# Cryptos to track
cryptos = ["BTC", "ETH"]


# Add Flask server
server = app.server


@server.route("/bokeh_plot/<crypto_symbol>")
def bokeh_plot(crypto_symbol):
    df, bokeh_plots = components.get_crypto_data_and_graphs(crypto_symbol)

    # Get the Bokeh figure
    price_script, price_div = bokeh_plots["price_script"], bokeh_plots["price_div"]
    volume_script, volume_div = bokeh_plots["volume_script"], bokeh_plots["volume_div"]

    # Generate full HTML page
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{crypto_symbol} Chart</title>
        {CDN.render()}  <!-- Add Bokeh resources -->
    </head>
    <body style="background-color: black; color: white;">
        <h1 style="text-align: center;">{crypto_symbol} Price Chart</h1>
        {price_div}
        {price_script}
        <h2 style="text-align: center;">Trading Volume</h2>
        {volume_div}
        {volume_script}
    </body>
    </html>
    """
    return render_template_string(html_content)

# Create crypto cards with links
crypto_cards = dbc.Row(
    [
        dbc.Col(
            html.A(
                components.generate_crypto_card(asset),
                href=f"/crypto/{asset}",
                style={"textDecoration": "none", "color": "inherit"},
                className="bg-dark text-white border-light"
            ),
            width="auto"
        )
        for asset in cryptos
    ]
)

# Sidebar navigation
sidebar = dbc.Nav(
    [
        dbc.NavLink("Overview", href="/", id="overview-link", className="nav-link"),
        dbc.NavLink("Market Data", href="/market", id="market-link", className="nav-link"),
        dbc.NavLink("Portfolio", href="/portfolio", id="portfolio-link", className="nav-link"),
        dbc.NavLink("About", href="/about", id="about-link", className="nav-link"),
    ],
    vertical=True,
    pills=True,
    className="bg-dark p-3",
    id="sidebar",  # Add an ID to the sidebar
    style={"width": "200px", "height": "100vh", "position": "fixed", "top": "0", "left": "-200px",
           "transition": "left 0.5s"}  # Initially hidden off-screen
)

# Hamburger menu button
hamburger_button = html.Button(
    html.I(className="fas fa-bars"),  # Use Font Awesome hamburger icon
    id="hamburger-button",
    className="bg-dark text-white border-0 p-2",
    style={"position": "fixed", "top": "10px", "left": "10px", "zIndex": "1000"}
)

# Main content area that will be updated by the callback
content = html.Div(id="page-content", style={"marginLeft": "20px", "padding": "20px"},
                   className="bg-dark")  # initially no margin left

# Add to app layout
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),  # Track URL changes
    hamburger_button,  # Add hamburger button
    sidebar,  # Sidebar remains dark
    html.Div(id="page-content", className="bg-dark text-white",
             style={"marginLeft": "200px", "width": "calc(100% - 200px)", "transition": "margin-left 0.5s"}),  # Auto width
    dcc.Store(id="init-trigger", data={}),  # Store to persist state
    dcc.Store(id='crypto-data-store')  # Store for crypto data
], fluid=True, className="bg-dark text-white")


# Callback to toggle the sidebar visibility
@app.callback(
    Output("sidebar", "style"),
    Output("page-content", "style"),
    Input("hamburger-button", "n_clicks"),
    State("sidebar", "style"),
    State("page-content", "style"),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, sidebar_style, page_content_style):
    if n_clicks is None:
        return sidebar_style, page_content_style

    if sidebar_style["left"] == "-200px":
        new_sidebar_style = sidebar_style.copy()
        new_sidebar_style["left"] = "0px"
        new_page_content_style = page_content_style.copy()
        new_page_content_style["marginLeft"] = "220px"
        return new_sidebar_style, new_page_content_style

    else:
        new_sidebar_style = sidebar_style.copy()
        new_sidebar_style["left"] = "-200px"
        new_page_content_style = page_content_style.copy()
        new_page_content_style["marginLeft"] = "20px"
        return new_sidebar_style, new_page_content_style


# Define the layout for crypto-specific pages
def crypto_page_layout(crypto_symbol):
    """
    Embeds the Bokeh candlestick and volume charts into the Dash layout using an iframe.
    """
    return dbc.Container(
        [
            html.H1(f"{crypto_symbol} Details", style={'color': 'white', 'textAlign': 'center'}),

            # Embed Bokeh plot using an iframe
            html.Iframe(
                src=f"/bokeh_plot/{crypto_symbol}",
                style={"width": "100%", "height": "700px", "border": "none"}
            ),

            html.Br(),
            dcc.Link("Back to Home", href="/", style={'color': 'white'}),
        ],
        fluid=True,
        className="p-0 m-0 bg-dark text-white",
        style={"width": "100vw", "maxWidth": "100%", "padding": "0px", "margin": "0px"}
    )

# Callback to handle page changes
@app.callback(
    Output("page-content", "children"),
    Output('crypto-data-store', 'data'),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def display_page(pathname):
    logging.info(f"pathname: {pathname}")
    trigger_id = ctx.triggered_id
    if trigger_id == "url":
        if pathname == "/":
            return dbc.Container([
                html.H1("Crypto Dashboard Overview", style={'color': 'white'}),
                crypto_cards,
            ], className="bg-dark"), {}
        elif pathname == "/market":
            return html.Div([html.H1("Market Data", style={'color': 'white'})], className="bg-dark"), {}
        elif pathname == "/portfolio":
            return html.Div([html.H1("Portfolio", style={'color': 'white'})], className="bg-dark"), {}
        elif pathname == "/about":
            return html.Div([html.H1("About", style={'color': 'white'})], className="bg-dark"), {}
        elif pathname.startswith("/crypto/"):
            crypto_symbol = pathname.split("/crypto/")[1]
            if crypto_symbol in cryptos:
                # Call the functions from the components file
                df, bokeh_plots = components.get_crypto_data_and_graphs(crypto_symbol)
                if not df.empty:
                    return crypto_page_layout(crypto_symbol), df.to_dict('records')
                else:
                    return html.Div([html.H1("No data found", style={'color': 'white'})], className="bg-dark"), {}
            else:
                return html.Div([html.H1("404 Page Not Found", style={'color': 'white'})], className="bg-dark"), {}
        else:
            return html.Div([html.H1("404 Page Not Found", style={'color': 'white'})], className="bg-dark"), {}
    else:
        return html.Div([html.H1("404 Page Not Found", style={'color': 'white'})], className="bg-dark"), {}


if __name__ == "__main__":
    port = utils.find_available_port()
    Timer(1, utils.open_browser, args=[port]).start()
    app.run_server(debug=True, port=port, use_reloader=False)