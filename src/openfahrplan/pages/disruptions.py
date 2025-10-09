# from dash import html, dcc, callback, Output, Input, register_page
# from openfahrplan import feed
# from openfahrplan.lib.display import zoom_from_bounds
#
# import plotly.express as px
#
# from openfahrplan.lib.disruptions import gtfs_get_disruptions
#
# register_page(__name__, path="/disruptions")
#
#
# disruptions = gtfs_get_disruptions(feed)
# stops = feed.stops.merge(disruptions)
# stops["label"] = stops["disruptions"].apply(
#     lambda arr: "Störungen: " + ", ".join(map(str, arr)) if isinstance(arr, (list, tuple)) else "Störungen: " + str(arr)
# )
# zoom,center=zoom_from_bounds(stops)
# fig = px.scatter_map(
#     stops,
#     lat="stop_lat",
#     lon="stop_lon",
#     hover_name="label",
#     text="stop_name",
#     zoom=zoom,
#     color="color",
#     color_discrete_map="identity",
#     map_style="carto-positron" # basic, carto-positron, carto-darkmatter
# )
#
# fig.update_traces(marker=dict(size=15))
# fig.update_layout(
#     showlegend=True,
#     coloraxis_showscale=True,
#     margin=dict(t=0, b=0, l=0, r=0)
# )
#
# layout = html.Div([
#     html.Div(
#         style={"height": "100vh"},
#         children=[
#             dcc.Graph(figure=fig, style={"height": "100%"},config={"displayModeBar": False})
#         ]
#     )
# ])