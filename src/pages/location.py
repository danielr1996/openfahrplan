import dash
from dash import Dash, html, dcc, callback, Output, Input, register_page
register_page(__name__,path="/location")
import json
layout =  html.Div([
    html.Button("Get location", id="geo-btn"),
    dcc.Store(id="geo"),
    html.Pre(id="geo-out")
])

dash.clientside_callback(
    "window.dash_clientside.clientside.get_location",
    Output("geo", "data"),
    Input("geo-btn", "n_clicks")
)

@callback(Output("geo-out", "children"), Input("geo", "data"))
def show_geo(data):
    if not data:
        return "Click the button."
    return json.dumps(data, indent=2)
