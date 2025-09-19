import dash
from dash import Dash, html, dcc, callback, Output, Input, register_page

register_page(__name__, path="/")
from init.feed import feed
import json



routes = feed.routes.drop_duplicates(subset=["route_short_name"]) \
    .groupby("route_type")["route_short_name"] \
    .count()
# print(routes)
layout = html.Div([
    html.H2("Agencies"),
    html.Ul(className="flex flex-row gap-4", children=[
        html.Li([dcc.Link(agency.agency_name, href=agency.agency_url)]) for agency in
        feed.agency.itertuples(index=False)
    ]),
    # html.H2("Routes"),
    # html.Ul(className="flex flex-row gap-4", children=[
    #     html.Li() for route,count in routes.items()
    # ])
])
