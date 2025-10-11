from dash import html, dcc, register_page
from urllib.parse import quote
from openfahrplan import feed
from openfahrplan.lib.display import get_route_type_label, sort_route_names, get_route_color

register_page(__name__, path="/lines")

groups = feed.routes.groupby("route_type")["route_short_name"].unique()

layout = html.Div(className="m-4", children=[
    html.Strong(className="", children=f"Alle Linien ({len(feed.routes["route_short_name"].unique())})"),
    *[html.Details(className="mt-4",open=True, children=[
        html.Summary(className="mb-2",children=html.Strong(className="mb-8", children=f"{get_route_type_label(route_type)} ({len(routes)})")),
        html.Ul(className=" flex flex-wrap gap-2", children=[
            html.Li(className="rounded-md px-2 py-1 text-white", style={"background-color": get_route_color(route)},
                    children=dcc.Link(route, href=f"/lines/{quote(route)}")) for route in sort_route_names(routes)])
    ]) for route_type, routes in groups.items()],
])
