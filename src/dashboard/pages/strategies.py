# src/dashboard/pages/strategies.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_strategies_data():
    """
    Placeholder: returns a list of dictionaries, each representing
    a running (or recently active) strategy.

    Real code might query a database, parse logs, or use an internal data structure.
    """
    # Example hard-coded data for illustration
    return [
        {
            "name": "Mean Reversion BTC",
            "status": "Running",
            "last_signal": "BUY @ 10:05 am",
            "pnl": 123.45,
            "start_time": "2023-03-01 09:00",
        },
        {
            "name": "Trend ETH",
            "status": "Stopped",
            "last_signal": "SELL @ 14:20 pm",
            "pnl": -45.30,
            "start_time": "2023-04-10 07:30",
        },
    ]


def strategies_table():
    """
    Generates a table summarizing each strategy's status, PnL, and last signal.
    """
    data = get_strategies_data()
    table_header = html.Thead(
        html.Tr([
            html.Th("Strategy Name"),
            html.Th("Status"),
            html.Th("Last Signal"),
            html.Th("PnL"),
            html.Th("Start Time")
        ])
    )

    rows = []
    for strat in data:
        row = html.Tr([
            html.Td(strat["name"]),
            html.Td(strat["status"]),
            html.Td(strat["last_signal"]),
            html.Td(f"${strat['pnl']:.2f}"),
            html.Td(strat["start_time"]),
        ])
        rows.append(row)

    table_body = html.Tbody(rows)

    return dbc.Table([table_header, table_body],
                     bordered=True, dark=True, hover=True, responsive=True)


def layout():
    """
    Build the full layout for the Strategies page.
    """
    return dbc.Container([
        html.H1("Strategies", className="text-center my-4"),
        html.P("Monitor the status and performance of your automated strategies."),

        # A table to summarize each strategy
        strategies_table(),

        html.Hr(),

        # Add more sections for logs, recent trades, or charts, e.g.:
        html.H2("Recent Trades (Example Placeholder)"),
        dcc.Markdown("Here you could load recent trades from a log file or database."),

        # Potentially, you can add a chart for each strategy's PnL or equity curve
        # e.g. create a placeholder figure
        html.H2("Strategy Performance Over Time (Placeholder)"),
        dcc.Graph(figure=go.Figure().update_layout(
            title="Equity Curve or PnL Over Time",
            template="plotly_dark"
        )),

    ], fluid=True)


# Or if you prefer not to have a function named layout, you can define it directly:
layout = layout()