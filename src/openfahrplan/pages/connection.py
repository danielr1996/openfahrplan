import logging

import dash
from dash import html, dcc, register_page, Output, Input
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

from openfahrplan.lib.display import zoom_from_bounds, build_route_map_data
from openfahrplan.lib.raptor import raptor_route
from openfahrplan import feed, raptor_index, data_folder
from openfahrplan.lib.display import map_style
from openfahrplan.lib.gtfs import map_disruptions

register_page(__name__, path="/connection")
times = [
    {"label": f"{h:02d}:{m:02d}", "value": f"{h:02d}:{m:02d}:00"}
    for h in range(24)
    for m in (0, 30)
]
layout = html.Div(
    className="h-full flex flex-col",
    children=[
        html.Div(
            className="flex gap-3 items-end flex-wrap p-2",
            children=[
                dcc.Dropdown(
                    id={"type": "station", "key": "from"},
                    placeholder="Von...",
                    value="de:09564:654:11:1",
                    search_value="Nürnberg Gustav-Adolf-Str.",
                    style={"minWidth": 400}
                ),
                dcc.Dropdown(
                    id={"type": "station", "key": "to"},
                    placeholder="Nach...",
                    value="de:09564:704:10:2",
                    search_value="Nürnberg Plärrer",
                    style={"minWidth": 400}
                ),
                dcc.Dropdown(
                    id="time_dropdown",
                    options=times,
                    value="08:00:00",
                    clearable=False,
                    style={"width": 100}
                )
            ], ),

        dcc.Loading(
            id="connection-loading",
            className="grow",
            overlay_style={"height": "100%"},
            parent_style={"height": "100%"},
            style={"height": "100%"},
        ),
    ]
)


@dash.callback(
    Output({"type": "station", "key": dash.MATCH}, "options"),
    Input({"type": "station", "key": dash.MATCH}, "search_value"),
)
def update_stop_options(search_value):
    if not search_value:
        raise PreventUpdate
    res = (feed.gtfs_find_station(search_value)[
        ["stop_id", "stop_name", "location_type", "parent_station", "score"]].rename(
        columns={"stop_name": "label", "stop_id": "value"}))
    return res[["value", "label"]].to_dict("records")


@dash.callback(
    Output("connection-loading", "children"),
    Input({"type": "station", "key": "from"}, "value"),
    Input({"type": "station", "key": "to"}, "value"),
    Input("time_dropdown", "value"),
)
def update_output(stop_from, stop_to,time):
    if not stop_from or not stop_to:
        raise PreventUpdate

    res = raptor_route(raptor_index, stop_from, stop_to,departure_time=time)

    if res is None:
        logging.warning("connections callbacked prevented update because raptor didnt return a result")
        raise PreventUpdate
    data = build_route_map_data(feed, res)
    zoom, center = zoom_from_bounds(data["stops"])
    fig = go.Figure()

    for seg in data["segments"]:
        if seg["type"] == "trip":
            fig.add_trace(go.Scattermap(
                lat=seg["lat"], lon=seg["lon"],
                mode="lines",
                line=dict(color=seg["color"], width=map_style["line_width"]),
                name=seg["name"]
            ))
        else:
            fig.add_trace(go.Scattermap(
                lat=seg["lat"], lon=seg["lon"],
                mode="lines",
                line=dict(color=seg["color"], width=map_style["line_width"]),
                # hoverinfo="skip",
                text=[seg["name"]] * len(seg["lat"]),
                hovertemplate="%{text}<extra></extra>",
                name="Walk",
                showlegend=False
            ))

    all_stops = data["stops"]
    alerts = feed.gtfs_get_disruptions()
    affected_stops = map_disruptions(data_folder, all_stops, alerts)
    if not all_stops.empty:
        fig.add_trace(go.Scattermap(
            lat=all_stops["stop_lat"], lon=all_stops["stop_lon"],
            mode="markers",
            marker=dict(size=map_style["marker_size"], color=map_style["marker_color"]),
            text=all_stops["hover"],
            hoverinfo="text",
            showlegend=False
        ))
    fig.add_trace(go.Scattermap(
        lat=affected_stops["stop_lat"], lon=affected_stops["stop_lon"],
        mode="markers",
        marker=dict(size=map_style["marker_size"] - 2, color="#f73c6a"),
        text=affected_stops["hover"],
        hoverinfo="text",
        showlegend=False
    ))

    fig.update_layout(map_style=map_style["layer_style"],
                      margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(zoom=zoom, center=center),
                      showlegend=True)

    return dcc.Graph(figure=fig, className="h-full", config={"displayModeBar": False})
