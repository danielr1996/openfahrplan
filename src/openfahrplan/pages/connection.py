from dash import html, dcc, register_page
from urllib.parse import quote
from openfahrplan import feed
from openfahrplan.lib.display import get_route_type_label, sort_route_names, get_route_color, zoom_from_bounds
from openfahrplan import graph
from openfahrplan.lib.gtfs import gtfs_find_station
import networkx as nx
import pandas as pd
import plotly.graph_objects as go

register_page(__name__, path="/connection")
origin = gtfs_find_station(feed, "Gustav Adolf Straße")["stop_id"]
dest = gtfs_find_station(feed, "Selb")["stop_id"]
connection = nx.shortest_path(graph, origin, dest)
stops = feed.stops.query("stop_id in @connection").copy()
stops["stop_id"] = pd.Categorical(stops["stop_id"], categories=connection, ordered=True)
stops = stops.sort_values("stop_id")
fig = go.Figure()
zoom, center = zoom_from_bounds(stops)
fig.add_trace(go.Scattermap(
    lat=stops["stop_lat"],
    lon=stops["stop_lon"],
    mode="lines+markers",
    text=stops["stop_name"],
    # name="Haltestellen",
    hoverinfo="text",
    marker=dict(color="gray",size=10)
))
fig.update_layout(
    map=dict(zoom=zoom, center=center),
    margin=dict(l=0, r=0, t=0, b=0),
    # legend=dict(itemsizing="constant"),
    # map_style="carto-positron"
)
layout = html.Div(
    style={"height": "100vh"},
    children=[
        dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
    ]
)
