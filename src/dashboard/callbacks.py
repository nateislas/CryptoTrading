from dash.dependencies import Input, Output, State
from . import utils
from . import components

cryptos = ['BTC', 'ETH']

def register_callbacks(app):
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