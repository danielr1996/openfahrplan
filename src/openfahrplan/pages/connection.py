import dash
from dash import html, dcc, register_page, Output,Input
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from openfahrplan.lib.display import zoom_from_bounds, build_route_map_data
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
)
def update_output(stop_from,stop_to):
    if not stop_from or not stop_to:
        raise PreventUpdate

    res = raptor_route(raptor_index,stop_from, stop_to)

    if res is None:
        raise PreventUpdate
    data = build_route_map_data(feed,res)
    zoom,center = zoom_from_bounds(data["stops"])
    fig = go.Figure()

    for seg in data["segments"]:
        if seg["type"] == "trip":
            fig.add_trace(go.Scattermap(
                lat=seg["lat"], lon=seg["lon"],
                mode="lines+markers",
                marker=dict(size=6, opacity=0),
                line=dict(color=seg["color"], width=4),
                text=[seg["name"]]*len(seg["lat"]),
                hovertemplate="%{text}<extra></extra>",
                name=seg["name"]
            ))
        else:
            fig.add_trace(go.Scattermap(
                lat=seg["lat"], lon=seg["lon"],
                mode="lines",
                line=dict(color=seg["color"], width=3),
                text=[seg["name"]]*len(seg["lat"]),
                hovertemplate="%{text}<extra></extra>",
                name="Walk",
                showlegend=False
            ))

    sp = data["stops"]
    if not sp.empty:
        fig.add_trace(go.Scattermap(
            lat=sp["stop_lat"], lon=sp["stop_lon"],
            mode="markers",
            marker=dict(size=8, color="#666666"),
            text=sp["hover"],
            hoverinfo="text",
            name="Stops",
            showlegend=False
        ))

    fig.update_layout(map_style="carto-positron",
                      margin=dict(l=0, r=0, t=0, b=0),
                      map=dict(zoom=zoom, center=center),
                      showlegend=True)

    return dcc.Graph(figure=fig,style={"height": "100%"}, config={"displayModeBar": False})
