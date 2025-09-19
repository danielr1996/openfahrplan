import dash
import plotly.express as px
import plotly.graph_objects
from init.feed import feed
from dash import Dash, html, dcc, callback, Output, Input, dash_table
from lib.lib import get_route_type_label

from src.utils import gtfs_get_fake_disruptions, get_route_color, gtfs_get_longest_stop_pattern

dash.register_page(__name__, path="/explore")

initdf = (
    feed.routes
    .merge(feed.trips)
    .merge(feed.stop_times)
    .merge(feed.stops)
    # .merge(gtfs_get_fake_disruptions(feed))
)
routes_labels = initdf["route_short_name"].drop_duplicates().squeeze()
stop_labels = initdf["stop_name"].drop_duplicates().squeeze()
route_type_labels = initdf["route_type"].drop_duplicates().squeeze()
column_labels = initdf.columns
layout = html.Div([
    # TODO: enforce that either one route or one station is selected
    dcc.Dropdown(
        id="route_short_name",
        options=[{"label": c, "value": c} for c in routes_labels],
        value=["U3"],
        placeholder="Select a route",
        multi=True
    ),
    dcc.Dropdown(
        id="stop_name",
        options=[{"label": c, "value": c} for c in stop_labels],
        value=[],
        placeholder="Select a stop",
        multi=True
    ),
    dcc.Dropdown(
        id="route_type",
        options=[{"label": get_route_type_label(c), "value": c} for c in route_type_labels],
        value=route_type_labels,
        placeholder="Select a type",
        multi=True
    ),
    # dcc.Slider(0, 100, 5, value=100, id='sample-fraction'),
    html.Br(),
    dcc.Graph(id="graph"),
    dash_table.DataTable(
        id="table",
        columns=[{"name": col, "id": col} for col in initdf.columns],
        # data=initdf.head(1).to_dict("records"),
        page_size=20,  # shows up to 5 rows per page
        sort_action="native",  # enable sorting
        filter_action="native",  # enable filtering
        style_table={"overflowX": "auto"},
        style_cell={"padding": "8px", "textAlign": "left"},
        style_header={"fontWeight": "bold"},
        merge_duplicate_headers=True,
    )
])


@dash.callback(
    Output("table", "data"),
    Output("graph", "figure"),
    # Input("sample-fraction","value"),
    Input("route_short_name", "value"),
    Input("route_type", "value"),
    Input("stop_name", "value"),
)
def update_table(route_short_name, route_type,stop_name):
    if not route_short_name:
        route_short_name = routes_labels
    if not route_type:
        route_type = route_type_labels
    if not stop_name :
        stop_name = stop_labels
    df = initdf
    df = df.query("route_short_name in @route_short_name and route_type in @route_type and stop_name in @stop_name")
    # df = df.sample(frac=fraction/100)
    fig = px.scatter_map(
        df,
        lat="stop_lat",
        lon="stop_lon",
        # hover_name="stop_name",
        # color="color",
        # color_discrete_map="identity",
        # map_style="carto-positron" # basic, carto-positron, carto-darkmatter
    )
    #     fig.update_traces(marker=dict(size=15))
    #     fig.update_layout(
    #         showlegend=True,autosize=True, coloraxis_showscale=False, margin=dict(t=0, b=0, l=0, r=0))
    #
    # df = df.drop_duplicates(["trip_id","stop_sequence"]).sort_values(by=["trip_id","stop_sequence"])
    # for name, trip in df.groupby("trip_id"):
    #     df = df.sort_values(by=["trip_id","stop_sequence"])
    df = gtfs_get_longest_stop_pattern(df)
    for name, trip in df.groupby("route_short_name"):
        trip = trip.sort_values("stop_sequence")
        fig.add_scattermap(
            lat=trip["stop_lat"],
            lon=trip["stop_lon"],
            mode="lines",
            # line=dict(width=3, color=get_route_color(name)),
            name=f"{name}",#{long_trimmed}
            showlegend=True
        )
    return  df.to_dict("records"),fig
