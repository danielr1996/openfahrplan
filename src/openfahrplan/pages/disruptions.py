from dash import html, dcc, register_page
from openfahrplan.lib.display import zoom_from_bounds, map_style
from openfahrplan import feed, data_folder

import plotly.graph_objects as go

register_page(__name__, path="/disruptions")
def map_disruptions(stops, alerts):
    import pandas as pd
    mapping = pd.read_parquet(data_folder / "mapping" / "mapping.parquet")
    # normalize dtypes to string (preserves <NA>)
    stops = stops.copy()
    mapping = mapping.copy()
    stops["stop_id"] = stops["stop_id"].astype("string")
    mapping["vgn_id"] = mapping["vgn_id"].astype("string")
    mapping["de_id"]  = mapping["de_id"].astype("string")
    alerts["stop_id"] = alerts["stop_id"].astype("string")

    agg = (
        alerts.groupby("stop_id", dropna=True).agg(
            disruption_text = ("header", lambda s: " | ".join(pd.unique(s.dropna()))),
            disruption_type = ("cause",  lambda s: sorted(set(s.dropna()))),
            disruption_effect = ("effect", lambda s: sorted(set(s.dropna()))),
        )
        .rename_axis("de_id")
        .reset_index()
    )
    agg["de_id"] = agg["de_id"].astype("string")

    out = (
        stops.merge(mapping, left_on="stop_id", right_on="vgn_id", how="left")
        .merge(agg, on="de_id", how="left")
    )
    return out[out[["disruption_text", "disruption_type", "disruption_effect"]].notna().any(axis=1)]

alerts = feed.gtfs_get_disruptions()
stops = map_disruptions(feed.stops, alerts)

zoom,center=zoom_from_bounds(stops,padding=0.3)

fig = go.Figure()
fig.add_trace(go.Scattermap(
    lat=stops["stop_lat"],
    lon=stops["stop_lon"],
    mode="markers",
    text=stops["stop_name"] + " (" + stops["stop_id"] + ")",
    hoverinfo="text",
    marker=dict(size=map_style["marker_size"]*1.3, color="#f73c00"),
))

fig.update_layout(
    map=dict(zoom=zoom, center=center),
    margin=dict(l=0, r=0, t=0, b=0),
    map_style=map_style["layer_style"],
)

layout = html.Div([
    html.Div(
        style={"height": "100vh"},
        children=[
            dcc.Graph(figure=fig, style={"height": "100%"},config={"displayModeBar": False})
        ]
    )
])
