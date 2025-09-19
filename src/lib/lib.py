ROUTE_TYPE_LABELS = {
    0: "Tram",
    1: "Subway",
    2: "Rail",
    3: "Bus",
    4: "Ferry",
    5: "Cable Car",
    6: "Gondola",
    7: "Funicular"
}


def get_route_type_label(route_type: int) -> str:
    return ROUTE_TYPE_LABELS.get(route_type, f"Other({route_type})")