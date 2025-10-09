import logging

import dash
from dash import html, dcc, register_page, Output, Input
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from openfahrplan.lib.display import zoom_from_bounds, build_route_map_data
from openfahrplan.lib.raptor import raptor_route
from openfahrplan import feed, raptor_index
from openfahrplan.lib.display import map_style
register_page(__name__, path="/connection")
layout = html.Div(
    style={"height": "100vh"},
    children=[
        html.Div([
            dcc.Dropdown(
                id={"type": "station", "key": "from"},
                placeholder="Von...",
                value="de:09564:510:1:1",
                search_value="Nürnberg Hbf",
                style={"minWidth": 400}
            ),
            dcc.Dropdown(
                id={"type": "station", "key": "to"},
                placeholder="Nach...",
                value="de:09564:704:10:2",
                search_value="Nürnberg Plärrer",
                style={"minWidth": 400}
            ),
        ], style={"display": "flex", "gap": "12px", "alignItems": "end"}),

        dcc.Loading(overlay_style={"height": "100%"}, parent_style={"height": "100%"}, style={"height": "100%"},
                    id="loading", children=[html.Div(id="graph-container", style={"height": "100%"})], type="default"),
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
    Output("graph-container", "children"),
    Input({"type": "station", "key": "from"}, "value"),
    Input({"type": "station", "key": "to"}, "value"),
)
def update_output(stop_from, stop_to):
    if not stop_from or not stop_to:
        raise PreventUpdate

    res = raptor_route(raptor_index, stop_from, stop_to)

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
                showlegend=False
            ))

    sp = data["stops"]
    if not sp.empty:
        fig.add_trace(go.Scattermap(
            lat=sp["stop_lat"], lon=sp["stop_lon"],
            mode="markers",
            marker=dict(size=map_style["marker_size"], color=map_style["marker_color"]),
            text=sp["hover"],
            hoverinfo="text",
            showlegend=False
        ))

    fig.update_layout(map_style=map_style["layer_style"],
                      margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(zoom=zoom, center=center),
                      showlegend=True)

    return dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
