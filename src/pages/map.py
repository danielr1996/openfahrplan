import dash
from dash import Dash, html, dcc, callback, Output, Input, register_page
register_page(__name__,path="/map")
import json
layout =  html.Div([
    html.H2("Map")
])
