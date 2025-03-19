# src/dashboard/pages/portfolio.py
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import logging
from .. import utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_pnl_charts():
    """
    Fetches daily PnL data from utils.get_daily_pnl_data(),
    creates two Plotly figures:
      1) bar chart for last 7 days,
      2) line chart for cumulative PnL over entire history.
    Returns them as dcc.Graph components.
    """
    df_pnl = utils.get_daily_pnl_data()
    if df_pnl.empty:
        # If there's no data, return placeholder graphs
        return (
            dcc.Graph(figure=go.Figure().update_layout(title="No Daily PnL Data Found")),
            dcc.Graph(figure=go.Figure().update_layout(title="No Cumulative PnL Data Found"))
        )

    # ============= BAR CHART: LAST 7 DAYS =============
    # We only want the last 7 rows
    df_last7 = df_pnl.tail(7)

    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=[d.strftime('%Y-%m-%d') for d in df_last7['date']],
        y=df_last7['daily_pnl'],
        marker_color=[
            'green' if val >= 0 else 'red'
            for val in df_last7['daily_pnl']
        ]
    ))
    bar_fig.update_layout(
        title="Daily PnL (Past 7 Days)",
        xaxis_title="Date",
        yaxis_title="PnL",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white"
    )

    # ============= LINE CHART: CUMULATIVE PnL =============
    # We'll compute a cumulative sum across the entire date range
    df_pnl['cumulative_pnl'] = df_pnl['daily_pnl'].cumsum()

    line_fig = go.Figure()
    line_fig.add_trace(go.Scatter(
        x=df_pnl['date'],
        y=df_pnl['cumulative_pnl'],
        mode='lines+markers',
        line=dict(color='cyan', width=2),
        name="Cumulative PnL"
    ))
    line_fig.update_layout(
        title="Cumulative PnL (All History)",
        xaxis_title="Date",
        yaxis_title="PnL",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="white"
    )

    return (
        dcc.Graph(figure=bar_fig),
        dcc.Graph(figure=line_fig)
    )

# The actual page layout
layout = dbc.Container([
    html.H1("Portfolio", className="text-center my-4"),
    html.P("Below is your recent Daily PnL (7 days) and your entire cumulative PnL over the course of trading."),

    # Create the two charts
    html.Div(
        children=generate_pnl_charts(),
        style={"marginBottom": "30px"}
    ),

    # In the future, you can add more tables/charts here, e.g. holdings info
], fluid=True)
