from dotenv import load_dotenv
load_dotenv()

import os

from openfahrplan.lib.gtfs import load_feed
from openfahrplan.lib.display import zoom_from_bounds
from openfahrplan.lib.disruptions import gtfs_get_disruptions
from dash import dcc, html
import dash
import plotly.express as px

feed = load_feed()
disruptions = gtfs_get_disruptions(feed)
stops = feed.stops.merge(disruptions)
stops["label"] = stops["disruptions"].apply(
    lambda arr: "Störungen: " + ", ".join(map(str, arr)) if isinstance(arr, (list, tuple)) else "Störungen: " + str(arr)
)
fig = px.scatter_map(
    stops,
    lat="stop_lat",
    lon="stop_lon",
    hover_name="label",
    text="stop_name",
    zoom=zoom_from_bounds(stops),
    color="color",
    color_discrete_map="identity",
    map_style="carto-positron" # basic, carto-positron, carto-darkmatter
)

fig.update_traces(marker=dict(size=15))
fig.update_layout(
    showlegend=True,
    coloraxis_showscale=True,
    margin=dict(t=0, b=0, l=0, r=0)
)

app = dash.Dash(__name__)
app.title = "OpenFahrplan"
app._favicon = "favicon.png"
app.layout = html.Div(
    style={"height": "100vh"},
    children=[
        dcc.Graph(figure=fig, style={"height": "100%"},config={"displayModeBar": False})
    ]
)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
    )