from dash import html, dcc
import dash_bootstrap_components as dbc

# Sidebar navigation shared by all pages
sidebar = dbc.Nav(
    [
        dbc.NavLink("Overview", href="/overview", active="exact"),
        dbc.NavLink("Strategies", href="/strategies", active="exact"),
        dbc.NavLink("Portfolio", href="/portfolio", active="exact"),
        dbc.NavLink("Market Data", href="/market", active="exact"),
        dbc.NavLink("About", href="/about", active="exact"),
    ],
    vertical=True,
    pills=True,
    className="bg-light p-3",
)

# Overview page layout – add your charts, tables, and cards here
layout = dbc.Container([
    html.H1("Overview", className="text-center my-4"),
    html.Div("Account summary, PnL, and holdings will be displayed here."),
    # Example: You can later add dcc.Graph components or other custom cards
], fluid=True)
