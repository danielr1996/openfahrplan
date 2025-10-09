
import re
import math

import pandas as pd

route_colors = {
    "U1": "#114273",
    "U2": "#fa0004",
    "U3": "#227e7f",
    # "RE/RB": "#03643b",
    "S1": "#650000",
    "S2": "#86c423",
    "S3": "#ff6600",
    "S4": "#051f4c",
    "S5": "#007dbf",
    "S6": "#8e9e42",
    "4": "#f2858d",
    "5": "#8f51a1",
    "6": "#ffd500",
    "7": "#99a7d4",
    "8": "#00baf1",
    "10": "#c65387",
    "11": "#f79545",
    "D": "#8a8a8a",
    "N1": "#f49f07",
    "N2": "#005fa2",
    "N3": "#e50480",
    "N4": "#b3cfe7",
    "N5": "#fccd00",
    "N6": "#e3171e",
    "N7": "#834c5e",
    "N8": "#7f75a4",
    "N9": "#c8d402",
    "N10": "#029cae",
    "N11": "#97388d",
    "N12": "#02a95f",
    "N13": "#e9501a",
    "N14": "#43591f",
    "N15": "#df92bd",
    "N17":"#ee6b4f",
    "N18":"#008dcc",
    "N20":"#79b930",
    "N21":"#e60280",
    "N60": "#007a50",
    "N61": "#a59ec5",
    "Elevator":"#f8cc46"
}

def get_route_color(short_name: str) -> str:
    if short_name in route_colors:
        return route_colors[short_name]
    if re.match(r"^RE", short_name):
        return "#03643b"
    if re.match(r"^RB", short_name):
        return "#03643b"
    return "#c02032"  # default

ROUTE_TYPE_LABELS = {
    0: "Tram",
    1: "U-Bahn",
    2: "Zug",
    3: "Bus",
    4: "Fähre",
    5: "Cable Car",
    6: "Gondel",
    7: "Funicular"
}

def get_route_type_label(route_type: int) -> str:
    return ROUTE_TYPE_LABELS.get(route_type, f"Other({route_type})")


def zoom_from_bounds(stops,padding=0.1):
    lat_min, lat_max = stops["stop_lat"].min(), stops["stop_lat"].max()
    lon_min, lon_max = stops["stop_lon"].min(), stops["stop_lon"].max()
    lat_span = max(1e-9, lat_max - lat_min) * (1 + padding)
    lon_span = max(1e-9, lon_max - lon_min) * (1 + padding)
    span = max(lat_span, lon_span)

    zoom = math.log2(360.0 / span)
    center = dict(lat=stops["stop_lat"].mean(), lon=stops["stop_lon"].mean())
    return max(0, min(20, zoom)), center

def sort_route_names(routes):
    df = pd.DataFrame({"route": routes})
    df[["prefix", "number", "suffix"]] = df["route"].str.extract(r"^([^\d]*)(\d*)(.*)$")
    df["number"] = pd.to_numeric(df["number"], errors="coerce")

    df = df.sort_values(
        by=["prefix", "number", "suffix"],
        key=lambda col: col.astype(str).str.lower() if col.name != "number" else col,
        na_position="last",
        ignore_index=True,
    )

    routes_sorted = df.apply(
        lambda row: (
                str(row["prefix"]) +
                ("" if pd.isna(row["number"]) else str(int(row["number"]))) +
                str(row["suffix"])
        ),
        axis=1
    ).tolist()
    return routes_sorted

def location_type_label(row):
    has_parent = pd.notna(row["parent_station"])
    has_type = float(row["location_type"]) > 0 if pd.notna(row["location_type"]) else False
    if not has_type and not has_parent: return "Stop"
    if not has_type and has_parent:     return "Platform"
    if has_type and not has_parent:     return "Station"
    return "-1"

