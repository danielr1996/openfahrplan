from dash import html, dcc, register_page
from openfahrplan.lib.display import get_route_type_label, sort_route_names, get_route_color, zoom_from_bounds
import pandas as pd
import plotly.graph_objects as go
from openfahrplan import feed
register_page(__name__, path="/stations")
stops = feed.stops
def combo_label(row):
    has_parent = pd.notna(row["parent_station"])
    has_type = float(row["location_type"]) > 0 if pd.notna(row["location_type"]) else False
    if not has_type and not has_parent: return "Stop"
    if not has_type and has_parent:     return "Platform"
    if has_type and not has_parent:     return "Station"
    return "-1"

stops["combo_label"] = stops.apply(combo_label, axis=1)

colors = {
    "Stop": "#1f77b4",
    "Platform": "#2ca02c",
    "Station": "#ff7f0e",
}
zoom,center = zoom_from_bounds(stops)
fig = go.Figure()

for label, group in stops.groupby("combo_label"):
    fig.add_trace(go.Scattermap(
        lat=group["stop_lat"],
        lon=group["stop_lon"],
        mode="markers",
        marker=dict(color=colors[label], size=10),
        text=group["stop_name"],
        name=label,
        hoverinfo="text"
    ))

fig.update_layout(map=dict(zoom=zoom,center=center),map_style="carto-positron", margin=dict(l=0,r=0,t=0,b=0))
layout = html.Div(
    style={"height": "100vh"},
    children=[
        dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
    ]
)
