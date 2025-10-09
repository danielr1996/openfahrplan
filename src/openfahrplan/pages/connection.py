import dash
from dash import html, dcc, register_page, Output,Input
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
from openfahrplan.lib.display import zoom_from_bounds
from openfahrplan.lib.gtfs import gtfs_find_station
from openfahrplan.lib.raptor import raptor_route
from openfahrplan import feed, raptor_index

register_page(__name__, path="/connection")
layout = html.Div(
    style={"height": "100vh"},
    children=[
        html.Div([
            dcc.Dropdown(
                id={"type": "station", "key": "from"},
                placeholder="Von...",
                style={"minWidth": 400}
            ),
            dcc.Dropdown(
                id={"type": "station", "key": "to"},
                placeholder="Nach...",
                style={"minWidth": 400}
            ),
        ], style={"display": "flex", "gap": "12px", "alignItems": "end"}),
        html.Div(id="graph-container",style={"height":"100%"}),
    ]
)
@dash.callback(
    Output({"type": "station", "key": dash.MATCH}, "options"),
    Input({"type": "station", "key": dash.MATCH}, "search_value"),
)
def update_stop_options(search_value):
    if not search_value:
        raise PreventUpdate
    res = (gtfs_find_station(feed,search_value)[["stop_id","stop_name","location_type","parent_station","score"]].rename(columns={"stop_name":"label","stop_id": "value"}))
    return res[["value","label"]].to_dict("records")

@dash.callback(
    Output("graph-container", "children"),
    Input({"type": "station", "key": "from"}, "value"),
    Input({"type": "station", "key": "to"}, "value"),
    config_prevent_initial_callbacks=True
)
def update_output(stop_from,stop_to):
    if not stop_from or not stop_to:
        raise PreventUpdate

    res = raptor_route(raptor_index,stop_from, stop_to)
    print(res)

    if res is None:
        raise PreventUpdate

    fig = go.Figure()
    connection = res["stops"]
    stops = feed.stops.query("stop_id in @connection").copy()
    stops["stop_id"] = pd.Categorical(stops["stop_id"], categories=connection, ordered=True)
    stops = stops.sort_values("stop_id")
    zoom, center = zoom_from_bounds(stops)
    fig.add_trace(go.Scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="lines+markers",
        text=stops["stop_name"],
    hoverinfo="text",
    marker=dict(color="gray", size=10)
    ))
    fig.update_layout(
        map=dict(zoom=zoom, center=center),
        margin=dict(l=0, r=0, t=0, b=0),
    map_style="carto-voyager-nolabels",
    )
    return dcc.Graph(figure=fig,style={"height": "100%"}, config={"displayModeBar": False})
