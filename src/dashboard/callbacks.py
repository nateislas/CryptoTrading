# src/dashboard/callbacks.py
from dash.dependencies import Input, Output, State
from dash import html, dcc  # Import dcc as well, since it is used
import dash_bootstrap_components as dbc  # Import dash_bootstrap_components as dbc
from . import utils
from . import components
cryptos = ['BTC', 'ETH']

def register_callbacks(app, components):
    @app.callback(
        [Output("account-number", "children"),
        Output("buying-power", "children")],
        Input("init-trigger", "data")  # Triggers once when page loads
    )
    def load_account_info(_):
        account_number, buying_power = utils.fetch_account_details()
        return f"Account Number: {account_number}", f"Buying Power: ${buying_power:,.2f}"
    # Callback to update market data
    @app.callback(
        Output("market-table", "data"),
        Input("interval-update", "n_intervals"),
        State("toggle-change", "n_clicks")
    )
    def update_market_data(n, toggle_clicks):
        use_percent = toggle_clicks % 2 == 0  # Toggle between % and $ change
        market_data = []
        for asset in cryptos:
            price = utils.fetch_asset_price(asset)
            percent_change, dollar_change = utils.fetch_daily_changes(asset, price) if price else (None, None)
            change_display = f"{percent_change:.2f}%" if use_percent else f"${dollar_change:,.2f}"
            market_data.append({
                "asset": asset,
                "price": f"${price:,.2f}" if price else "N/A",
                "change": change_display if percent_change is not None else "N/A"
            })
        return market_data
    @app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")]
    )
    def render_page_content(pathname):
        if pathname == "/":
            return html.Div([
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
                components.portfolio_value_chart(),
                html.H3("Current Holdings"),
                components.holdings_table(),
                dbc.Row([dbc.Col(components.generate_crypto_card(asset)) for asset in cryptos])
            ])
        elif pathname == "/market":
            return html.Div([
                html.H2("Live Market Data"),
                dbc.Button("Toggle % / $ Change", id="toggle-change", className="mb-3", n_clicks=0),
                components.market_data_table(),
                dcc.Interval(id="interval-update", interval=60000, n_intervals=0)
            ])
        elif pathname == "/portfolio":
            return html.Div([
                html.H2("Portfolio"),
                html.P("This is the Portfolio page content.")
            ])
        elif pathname == "/about":
            return html.Div([
                html.H2("About"),
                html.P("This is the About page content.")
            ])
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )
    @app.callback(
        [Output(f"{page}-link", "active") for page in ["overview", "market", "portfolio", "about"]],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        if pathname == "/":
            # Treat page 1 as the homepage / index
            return True, False, False, False
        elif pathname == "/market":
            return False, True, False, False