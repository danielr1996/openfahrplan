from rapidfuzz import process, fuzz, utils
import pandas as pd
import os
from pathlib import Path
import gtfs_kit as gk

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