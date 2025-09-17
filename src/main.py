import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from src.utils import load_feed
from src.utils import gtfs_denormalize, gtfs_get_longest_stop_pattern, gtfs_get_fake_disruptions, get_route_color

pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)

feed = load_feed()
disruptions = gtfs_get_fake_disruptions(feed)
timetable = gtfs_denormalize(feed)
timetable = gtfs_get_longest_stop_pattern(timetable)

fig = px.scatter_map(
    disruptions.merge(feed.stops),
    lat="stop_lat",
    lon="stop_lon",
    hover_name="stop_name",
    color="color",
    color_discrete_map="identity",
    map_style="carto-positron" # basic, carto-positron, carto-darkmatter
)
fig.update_traces(marker=dict(size=15))
fig.update_layout(
    showlegend=True,autosize=True, coloraxis_showscale=False, margin=dict(t=0, b=0, l=0, r=0))

for name, stops in timetable.groupby("route_short_name"):
    stops = stops.sort_values("stop_sequence")
    parts = [p.strip() for p in stops["route_long_name"].iloc[0].split("-")]
    long_trimmed = f"{parts[0]} – {parts[-1]}"

    fig.add_scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="lines",
        line=dict(width=3, color=get_route_color(name)),
        name=f"{name}",#{long_trimmed}
        showlegend=True
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
#
if __name__ == "__main__":
    app.run(debug=True)
