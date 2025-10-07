from dash import html,dcc, register_page
from urllib.parse import quote
from openfahrplan import feed
from openfahrplan.lib.display import get_route_type_label, sort_route_names, get_route_color

register_page(__name__, path="/")

groups = feed.routes.groupby("route_type")["route_short_name"].unique()

layout = html.Div(className="m-4",children=[
    html.Ul(children=[
        html.Li(className="pb-4",children=[
            html.Strong(className="pb-2",children=f"{get_route_type_label(route_type)} ({len(routes)})"),
            html.Ul(className="flex flex-wrap gap-2",children=[html.Li(className="rounded-md px-2 py-1 text-white",style={"background-color": get_route_color(route)},children=dcc.Link(route, href=f"/routes/{quote(route)}")) for route in sort_route_names(routes)])
        ])
        for route_type, routes in groups.items()
    ])
])