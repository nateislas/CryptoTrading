from dash import Dash, dcc, html, Output, Input
import dash_bootstrap_components as dbc
from flask import Flask
import logging
from threading import Timer
from src.dashboard import utils  # For open_browser and port utilities
# Import page layouts from our modular pages
from src.dashboard.pages import overview, market, portfolio, about, strategies
# Register additional callbacks from our callbacks module
from src.dashboard import callbacks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a Flask server and initialize the Dash app with Bootstrap and Font Awesome
server = Flask(__name__)
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)

# Main layout: a Location for URL routing and a two-column layout (sidebar and page-content)
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    dbc.Row([
        dbc.Col(overview.sidebar, width=2),  # Sidebar navigation shared by all pages
        dbc.Col(html.Div(id="page-content"), width=10)
    ])
], fluid=True)

# Callback for multi-page routing
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname is None or pathname in ["/", "/overview"]:
        return overview.layout
    elif pathname == "/market":
        return market.layout
    elif pathname == "/portfolio":
        return portfolio.layout
    elif pathname == "/about":
        return about.layout
    elif pathname == "/strategies":
        return strategies.layout
    else:
        return html.H1("404: Page not found", style={'textAlign': 'center'})

callbacks.register_callbacks(app)

if __name__ == "__main__":
    port = utils.find_available_port()
    Timer(1, utils.open_browser, args=[port]).start()
    app.run_server(debug=True, port=port, use_reloader=False)