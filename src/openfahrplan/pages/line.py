import plotly.graph_objects as go
from dash import html, dcc, register_page

from openfahrplan import timetable
from urllib.parse import unquote
import pandas as pd
from openfahrplan.lib.display import zoom_from_bounds, get_route_color, map_style

register_page(__name__, path_template="/lines/<route_short_name>")


def layout(route_short_name=None, **kwargs):
    fig = go.Figure()
    route_short_name = unquote(route_short_name)
    route = (
        timetable.query("route_short_name == @route_short_name and direction_id == 1")
        .sort_values(["trip_id", "stop_sequence"])
    )
    stops = route.drop_duplicates("stop_id")
    zoom, center = zoom_from_bounds(stops)

    fig.add_trace(go.Scattermap(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        text=stops["stop_name"],
        name="Haltestellen",
        hoverinfo="text",
        showlegend=False,
        marker=dict(size=map_style["marker_size"], color=map_style["marker_color"]),
    ))
    fig.update_layout(
        map=dict(zoom=zoom, center=center),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(itemsizing="constant"),
        map_style=map_style["layer_style"],
    )

    route["dep_td"] = pd.to_timedelta(route["departure_time"], errors="coerce")
    trip_order = route.groupby("trip_id")["dep_td"].min().sort_values().index

    # pattern hash -> {stop_ids, trip_ids}
    patterns = {}

    for tid, g in (
            route.set_index("trip_id")
                    .loc[trip_order]
                    .reset_index()
                    .groupby("trip_id", sort=False)
    ):
        stop_ids = tuple(g["stop_id"].tolist())
        key = hash(stop_ids)
        if key not in patterns:
            patterns[key] = {"stop_ids": stop_ids, "trip_ids": []}
        patterns[key]["trip_ids"].append(tid)

    for pattern in patterns.values():
        g = route[route["trip_id"].isin(pattern["trip_ids"])].sort_values("stop_sequence").drop_duplicates("stop_id")

        dep = g["departure_time"].iloc[0]
        arr = g["arrival_time"].iloc[-1]
        dep_td = pd.to_timedelta(dep)
        arr_td = pd.to_timedelta(arr)
        dep_wrapped = f"{int((dep_td.total_seconds() % 86400) // 3600):02}:{int((dep_td.total_seconds() % 3600) // 60):02}"
        arr_wrapped = f"{int((arr_td.total_seconds() % 86400) // 3600):02}:{int((arr_td.total_seconds() % 3600) // 60):02}"
        diff = pd.to_timedelta(arr) - pd.to_timedelta(dep)
        trip_ids = ", ".join(pattern["trip_ids"])
        name = f"{dep_wrapped} - {arr_wrapped} ({(pd.to_datetime('2262-04-11') + diff).strftime('%H:%M')}) [{trip_ids}]"

        fig.add_trace(go.Scattermap(
            lat=g["stop_lat"],
            lon=g["stop_lon"],
            mode="lines",
            # name=name,
            line=dict(color=get_route_color(route_short_name), width=map_style["line_width"]),
            hoverinfo="skip",
            showlegend=False
        ))

    return dcc.Loading(
        overlay_style={"height": "100%"},
        parent_style={"height": "100%"},
        style={"height": "100%"},
        id="loading",
        children=[
            dcc.Graph(
                figure=fig,
                className="h-full",
                config={"displayModeBar": False},
            )
        ],
    )
