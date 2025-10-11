from dash import dcc, register_page
register_page(__name__, path="/")
layout = dcc.Location(href="/lines",id="redirect")