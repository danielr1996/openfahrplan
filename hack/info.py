from itertools import count

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

def info(feed):
    print(f"OpenFahrplan @ {', '.join(f'{row.agency_name} ({row.agency_url})' for _, row in feed.agency.iterrows())}")

    print("Available Routes: ")
    counts = feed.routes.drop_duplicates(subset=["route_short_name"]) \
        .groupby("route_type")["route_short_name"] \
        .count()

    for rtype, count in counts.items():
        print(f"    {get_route_type_label(rtype)}: {count}")