import dash
from dash import html, dcc, register_page, Output, Input
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from openfahrplan.lib.display import zoom_from_bounds
from openfahrplan.lib.gtfs import gtfs_find_related_stops, gtfs_find_station
from openfahrplan import feed

register_page(__name__, path="/stations")
layout = html.Div(
    style={"height": "100vh"},
    children=[
        html.Div([
            dcc.Dropdown(
                id="station",
                value="de:09564:510:1:1",
                search_value="Nürnberg Hbf",
                placeholder="Haltestelle...",
                style={"minWidth": 400},
            ),

        ], style={"display": "flex", "gap": "12px", "alignItems": "end"}),
        html.Div(id="stations-graph-container", style={"height": "100%"}),

    ]
)


@dash.callback(
    Output("station", "options"),
    Input("station", "search_value"),
)
def update_stop_options(search_value):
    if not search_value:
        raise PreventUpdate
    res = (gtfs_find_station(feed, search_value)[
               ["stop_id", "stop_name", "location_type", "parent_station", "score"]].rename(
        columns={"stop_name": "label", "stop_id": "value"}))
    return res[["value", "label"]].to_dict("records")


@dash.callback(
    Output("stations-graph-container", "children"),
    Input("station", "value"),
)
def update_output(station):
    if not station:
        raise PreventUpdate
    stops = gtfs_find_related_stops(feed, station)
    fig = go.Figure()
    zoom, center = zoom_from_bounds(stops)
    fig.add_trace(go.Scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        text=stops["stop_name"],
        hoverinfo="text",
        marker=dict(color="gray", size=10)
    ))
    fig.update_layout(
        map=dict(zoom=zoom, center=center),
        margin=dict(l=0, r=0, t=0, b=0),
        map_style="carto-voyager-nolabels",
    )
    return dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
