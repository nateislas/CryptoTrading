from dash.dependencies import Input, Output, State
from dash import html, dcc
import dash_bootstrap_components as dbc
import logging
from . import utils, components

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of cryptos to track; adjust as needed.
cryptos = ["BTC", "ETH"]

def register_callbacks(app):
    # Callback to load account details when the app initializes.
    @app.callback(
        [Output("account-number", "children"),
         Output("buying-power", "children")],
        Input("init-trigger", "data")
    )
    def load_account_info(_):
        account_number, buying_power = utils.fetch_account_details()
        return f"Account Number: {account_number}", f"Buying Power: ${buying_power:,.2f}"

    # Callback to update the market data table every minute.
    @app.callback(
        Output("market-table", "children"),
        Input("interval-update", "n_intervals")
    )
    def update_market_data(n_intervals):
        table_rows = []
        for asset in cryptos:
            price = utils.fetch_asset_price(asset)
            if price is not None:
                percent_change, _ = utils.fetch_daily_changes(asset, price)
                change_display = f"{percent_change:.2f}%" if percent_change is not None else "N/A"
                row = html.Tr([
                    html.Td(asset),
                    html.Td(f"${price:,.2f}"),
                    html.Td(change_display)
                ])
                table_rows.append(row)
        table_header = html.Thead(
            html.Tr([html.Th("Asset"), html.Th("Price"), html.Th("Change")])
        )
        table_body = html.Tbody(table_rows)
        return dbc.Table([table_header, table_body], bordered=True, dark=True, hover=True, responsive=True)

    # (Optional) Additional callbacks for other interactive components can be added here.
    # For example, you might add callbacks for switching chart types, filtering data, etc.
