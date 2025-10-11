
import pandas as pd
import math, re

map_style = {
    "marker_size": 10,
    "marker_color":"#666666",
    "line_width":4,
    "line_color":"#666666",
    "layer_style": "carto-voyager",
}

route_colors = {
    "U1": "#114273",
    "U2": "#fa0004",
    "U3": "#227e7f",
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
    if re.match(r"^IC", short_name):
        return "#787878"
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

def build_route_map_data(feed, res):
    """
    Convert a RAPTOR result into structured map data.
    Returns:
      {
        "segments": [ { "lat": [...], "lon": [...], "color": str, "name": str, "type": "trip"|"walk" } ],
        "stops": DataFrame with columns: stop_id, stop_name, stop_lat, stop_lon, time, hover
      }
    """
    if not res or not res.get("legs"):
        return {"segments": [], "stops": feed.stops.iloc[0:0].copy()}

    _TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")
    def _parse(t):
        if t is None: return None
        s = str(t)
        if not _TIME.match(s): return None
        h,m,x = map(int, s.split(":"))
        return h*3600 + m*60 + x
    def _fmt(sec):
        if sec is None or math.isinf(sec): return None
        sec = int(sec); h = sec//3600; m = (sec%3600)//60; s = sec%60
        return f"{h:02d}:{m:02d}:{s:02d}"
    def _leg_coords(trip_id, a, b):
        g = (feed.stop_times.loc[feed.stop_times["trip_id"] == trip_id,
        ["stop_id","stop_sequence","arrival_time","departure_time"]]
             .sort_values("stop_sequence").reset_index(drop=True))
        ia = g.index[g["stop_id"] == a]
        ib = g.index[g["stop_id"] == b]
        if len(ia)==0 or len(ib)==0:
            return [], [], [], []
        ia, ib = int(ia[0]), int(ib[-1])
        seg = g.iloc[ia:ib+1].copy()
        stop_ids = seg["stop_id"].tolist()
        times = [None]*len(stop_ids)
        if len(times) > 0:
            times[0] = _parse(seg.iloc[0]["departure_time"]) or _parse(seg.iloc[0]["arrival_time"])
            for i in range(1, len(times)):
                times[i] = _parse(seg.iloc[i]["arrival_time"]) or _parse(seg.iloc[i]["departure_time"])
        coords = seg.merge(
            feed.stops[["stop_id","stop_lat","stop_lon"]].drop_duplicates("stop_id"),
            on="stop_id", how="left"
        )
        return coords["stop_lat"].tolist(), coords["stop_lon"].tolist(), stop_ids, times
    def _dashed_segment(a_lat, a_lon, b_lat, b_lon, parts=10):
        lat=[]; lon=[]
        for i in range(parts):
            t0 = i/parts
            t1 = i/parts + 0.5/parts
            lat += [a_lat + (b_lat-a_lat)*t0, a_lat + (b_lat-a_lat)*t1, None]
            lon += [a_lon + (b_lon-a_lon)*t0, a_lon + (b_lon-a_lon)*t1, None]
        return lat, lon

    stops_idx = (feed.stops[["stop_id","stop_name","stop_lat","stop_lon"]]
                 .drop_duplicates("stop_id").set_index("stop_id"))
    stop_time_sec = {}
    segments = []
    grouped = []
    cur = None

    for kind, x, a, b in res["legs"]:
        if kind == "trip":
            trip_id = x
            route_id = feed.trips.loc[feed.trips["trip_id"] == trip_id, "route_id"].iloc[0]
            route_row = feed.routes.loc[feed.routes["route_id"] == route_id].iloc[0]
            route_name = (str(route_row.get("route_short_name"))
                          if pd.notna(route_row.get("route_short_name"))
                          else str(route_row.get("route_long_name")))
            color = get_route_color(route_name)
            lat, lon, stop_ids, times = _leg_coords(trip_id, a, b)
            if not lat:
                continue
            for sid, t in zip(stop_ids, times):
                if t is not None and sid not in stop_time_sec:
                    stop_time_sec[sid] = t
            if cur and cur["route_id"] == route_id:
                if cur["lat"] and cur["lon"] and lat:
                    if cur["lat"][-1] == lat[0] and cur["lon"][-1] == lon[0]:
                        lat = lat[1:]; lon = lon[1:]
                cur["lat"].extend(lat); cur["lon"].extend(lon)
            else:
                if cur:
                    grouped.append(cur)
                cur = {"route_id": route_id, "name": route_name, "color": color,
                       "lat": lat[:], "lon": lon[:]}
        elif kind == "walk":
            if cur:
                grouped.append(cur); cur = None
            if a in stops_idx.index and b in stops_idx.index:
                a_lat, a_lon = stops_idx.at[a,"stop_lat"], stops_idx.at[a,"stop_lon"]
                b_lat, b_lon = stops_idx.at[b,"stop_lat"], stops_idx.at[b,"stop_lon"]
                lat, lon = _dashed_segment(a_lat, a_lon, b_lat, b_lon, parts=12)
                segments.append({"lat": lat, "lon": lon, "color": "#9E9E9E",
                                 "name": "Walk", "type": "walk"})
            dur = int(x)
            if a in stop_time_sec and b not in stop_time_sec:
                stop_time_sec[b] = stop_time_sec[a] + dur
    if cur:
        grouped.append(cur)

    for g in grouped:
        segments.append({"lat": g["lat"], "lon": g["lon"],
                         "color": g["color"], "name": g["name"], "type": "trip"})

    path_ids = [sid for sid in res.get("stops", []) if sid in stops_idx.index]
    sp = stops_idx.loc[path_ids].reset_index()
    sp["time"] = sp["stop_id"].map(stop_time_sec).map(lambda v: _fmt(v) if pd.notna(v) else None)
    sp["hover"] = sp.apply(lambda r: f"{r['stop_name']}<br>{r['time']}" if r["time"] else r["stop_name"], axis=1)

    return {"segments": segments, "stops": sp}
