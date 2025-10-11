import logging

import dash
from dash import html, dcc, register_page, Output, Input
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from openfahrplan.lib.display import zoom_from_bounds, map_style
from openfahrplan import feed

register_page(__name__, path="/stations")
layout = html.Div(
    className="h-full",
    children=[
        html.Div(
            className="flex gap-3 items-end flex-wrap p-2",
            children=[
                dcc.Dropdown(
                    id="station",
                    value="de:09564:510:1:1",
                    search_value="Nürnberg Hbf",
                    placeholder="Haltestelle...",
                    style={"minWidth": 400},
                ),
            ],
        ),
        dcc.Loading(
            id="stations-loading",
            overlay_style={"height": "100%"},
            parent_style={"height": "100%"},
            style={"height": "100%"},
        )

    ]
)


@dash.callback(
    Output("station", "options"),
    Input("station", "search_value"),
)
def update_stop_options(search_value):
    if not search_value:
        raise PreventUpdate
    res = (feed.gtfs_find_station(search_value)[
        ["stop_id", "stop_name", "location_type", "parent_station", "score"]].rename(
        columns={"stop_name": "label", "stop_id": "value"}))
    return res[["value", "label"]].to_dict("records")


@dash.callback(
    Output("stations-loading", "children"),
    Input("station", "value"),
)
def update_output(station):
    if not station:
        logging.warning("stations update prevented update because stations is empty")
        raise PreventUpdate
    stops = feed.gtfs_find_related_stops(station)
    fig = go.Figure()
    zoom, center = zoom_from_bounds(stops)
    fig.add_trace(go.Scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        text=stops["stop_name"] + " (" + stops["stop_id"] + ")",
        hoverinfo="text",
        marker=dict(size=map_style["marker_size"], color=map_style["marker_color"]),
    ))

    fig.update_layout(
        map=dict(zoom=zoom, center=center),
        margin=dict(l=0, r=0, t=0, b=0),
        map_style=map_style["layer_style"],
    )
    return dcc.Graph(figure=fig, style={"height": "100%"},config={"displayModeBar":False})
