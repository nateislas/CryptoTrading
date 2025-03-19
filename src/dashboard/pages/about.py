from dash import html, dcc
import dash_bootstrap_components as dbc
import os

# Function to load and read README.md
def load_readme():
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "README.md"))

    try:
        with open(readme_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "README.md file not found."

# Load README content
readme_content = load_readme()

# About page layout
layout = dbc.Container([
    html.H1("About", className="text-center my-4"),
    dcc.Markdown(readme_content, style={"whiteSpace": "pre-wrap"}),  # Displays README as markdown
], fluid=True)
