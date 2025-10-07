from rapidfuzz import process, fuzz, utils
import pandas as pd
import os
from pathlib import Path
import gtfs_kit as gk
import networkx as nx

def load_feed():
    base = Path(os.getenv("OPENFAHRPLAN_DATA_DIR", Path.cwd() / "data"))
    # TODO: handle conflicting ids across multiple gtfs datasets
    return gk.read_feed(base / "gtfs" / "vgn.zip",dist_units="km")

def gtfs_find_station(feed, query: str):
    """
    Given a user provided station name, finds all related stops and the parent using fuzzy search

    Args:
        feed: GTFS feed object from gtfs_kit.read_feed().
        query (str): User-provided station name.

    Returns:
        children: pd.DataFrame
            All related stops
        parent: pd.Series
            The parent of all related stops
    """
    match_name, score, idx = process.extractOne(
        query,
        feed.stops['stop_name'].tolist(),
        scorer=fuzz.WRatio,
        processor=utils.default_process
    )
    stop = feed.stops.iloc[idx]

    parent = feed.stops[feed.stops['stop_id'] == stop["parent_station"]].squeeze() if pd.notna(stop.parent_station) else stop
    # children = feed.stops[feed.stops['parent_station'] == parent["stop_id"]]
    return parent


def gtfs_build_graph(feed):
    stops = feed.stops
    stop_times = feed.stop_times
    parent = stops.get("parent_station")
    stops["parent"] = parent.fillna(stops["stop_id"]) if parent is not None else stops["stop_id"]
    stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
    stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
    parent_rows = stops[stops["stop_id"].isin(stops["parent"])][["stop_id","stop_lat","stop_lon"]].set_index("stop_id")
    child_means = stops.groupby("parent", as_index=True)[["stop_lat","stop_lon"]].mean()
    coords = child_means.combine_first(parent_rows).reset_index().rename(columns={"index":"parent"})
    coords = coords.rename(columns={"parent":"pid"})
    st = stop_times.merge(stops[["stop_id","parent"]], on="stop_id", how="left")
    st["parent"] = st["parent"].fillna(st["stop_id"])
    st["stop_sequence"] = pd.to_numeric(st["stop_sequence"], errors="coerce")
    st = st.sort_values(["trip_id","stop_sequence"])
    st["next_parent"] = st.groupby("trip_id")["parent"].shift(-1)

    edges = (st.loc[(st["parent"].notna()) & (st["next_parent"].notna()) & (st["parent"] != st["next_parent"]),
    ["parent","next_parent"]]
             .drop_duplicates())
    G = nx.DiGraph()
    G.add_nodes_from(coords["pid"])
    G.add_edges_from(edges.itertuples(index=False, name=None))  # unweighted

    coord_map = coords.set_index("pid")[["stop_lat","stop_lon"]].to_dict(orient="index")
    return G, coord_map

def gtfs_build_graph2(feed):
    G = nx.Graph()
    G.add_edge("GAS", "Plärrer", weight=1,route="U3")
    G.add_edge("Plärrer", "Klinikum", weight=1,route="U1")
    G.add_edge("GAS","Maxi",weight=2,route="35")
    G.add_edge("Maxi","Klinikum",weight=1,route="U1")
    G.add_edge("Klinikum", "BFB", weight=2,route="172")
    path =nx.shortest_path(G, "GAS", "BFB", weight="weight")
    legs = []
    for u, v in zip(path, path[1:]):
        data = G[u][v]           # edge attribute dict
        legs.append({"from": u, "to": v, "route": data["route"], "weight": data["weight"]})

    for leg in legs:
        print(f'{leg["route"]}: {leg["from"]} → {leg["to"]} (weight={leg["weight"]})')
    print(path)