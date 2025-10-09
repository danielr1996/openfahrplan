import plotly.graph_objects as go
from dash import html, dcc, register_page

from openfahrplan import  timetable
from urllib.parse import unquote
import pandas as pd
from openfahrplan.lib.display import zoom_from_bounds, get_route_color, map_style

register_page(__name__, path_template="/routes/<route_short_name>")

def layout(route_short_name=None, **kwargs):
    fig = go.Figure()
    route_short_name = unquote(route_short_name)
    route = timetable.query("route_short_name == @route_short_name and direction_id == 1").sort_values(["trip_id","stop_sequence"])
    stops = route.drop_duplicates("stop_id")
    zoom,center = zoom_from_bounds(stops)
    fig.add_trace(go.Scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        text=stops["stop_name"],
        name="Haltestellen",
        hoverinfo="text",
        marker=dict(size=map_style["marker_size"], color=map_style["marker_color"]),

    ))
    fig.update_layout(
        map=dict(zoom=zoom,center=center),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(itemsizing="constant"),
        map_style=map_style["layer_style"]
    )
    route["dep_td"] = pd.to_timedelta(route["departure_time"], errors="coerce")
    trip_order = (
        route.groupby("trip_id")["dep_td"]
        .min()
        .sort_values()
        .index
    )
    for tid, g in (route.set_index("trip_id")
            .loc[trip_order]
            .reset_index()
            .groupby("trip_id", sort=False)):
        dep = g["departure_time"].iloc[0]
        arr = g["arrival_time"].iloc[-1]
        dep_td = pd.to_timedelta(dep)
        arr_td = pd.to_timedelta(arr)

        dep_wrapped = f"{int((dep_td.total_seconds() % 86400) // 3600):02}:{int((dep_td.total_seconds() % 3600) // 60):02}"
        arr_wrapped = f"{int((arr_td.total_seconds() % 86400) // 3600):02}:{int((arr_td.total_seconds() % 3600) // 60):02}"
        diff = pd.to_timedelta(arr) - pd.to_timedelta(dep)
        fig.add_trace(go.Scattermap(
            lat=g["stop_lat"],
            lon=g["stop_lon"],
            mode="lines",
            name=f"{dep_wrapped} - {arr_wrapped} ({(pd.to_datetime('2262-04-11') + diff).strftime('%H:%M')})",
            line=dict(color=get_route_color(route_short_name), width=map_style["line_width"]),
            hoverinfo="skip",
        ))
    return html.Div([
        html.Div(
            style={"height": "100vh"},
            children=[
                dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
            ]
        )
    ])
