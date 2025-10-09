from dash import html, dcc, register_page
import plotly.graph_objects as go
from openfahrplan import feed
import numpy as np
#
# You found a secret page. Keep it a secret!
#
register_page(__name__, path="/transfers")
st = feed.stops[["stop_id","stop_lat","stop_lon"]].rename(
    columns={"stop_lat":"lat","stop_lon":"lon"}
)

tf = (feed.transfers
      .merge(st.add_suffix("_from"), left_on="from_stop_id", right_on="stop_id_from", how="left")
      .merge(st.add_suffix("_to"),   left_on="to_stop_id",   right_on="stop_id_to",   how="left")
      .dropna(subset=["lat_from","lon_from","lat_to","lon_to"])
      )

# build polyline arrays with NaN separators (one segment per transfer)
n = len(tf)
lats = np.empty(n*3); lons = np.empty(n*3); texts = np.empty(n*3, dtype=object)
lats[0::3] = tf["lat_from"].to_numpy()
lats[1::3] = tf["lat_to"].to_numpy()
lats[2::3] = np.nan
lons[0::3] = tf["lon_from"].to_numpy()
lons[1::3] = tf["lon_to"].to_numpy()
lons[2::3] = np.nan
texts[0::3] = (tf["from_stop_id"] + " → " + tf["to_stop_id"]).to_numpy()
texts[1::3] = texts[0::3]
texts[2::3] = None

fig = go.Figure()
fig.add_trace(go.Scattermap(
    lat=lats, lon=lons, mode="lines",
    name="Transfers",
    text=texts, hoverinfo="text"
))
# optional: draw endpoints
fig.add_trace(go.Scattermap(
    lat=np.r_[tf["lat_from"], tf["lat_to"]],
    lon=np.r_[tf["lon_from"], tf["lon_to"]],
    mode="markers",
    name="Stops",
    text=np.r_[tf["from_stop_id"], tf["to_stop_id"]],
    hoverinfo="text"
))

fig.update_layout(map_style="carto-positron", margin=dict(l=0,r=0,t=0,b=0))
layout = html.Div(
    style={"height": "100vh"},
    children=[
        dcc.Graph(figure=fig, style={"height": "100%"}, config={"displayModeBar": False})
    ]
)
