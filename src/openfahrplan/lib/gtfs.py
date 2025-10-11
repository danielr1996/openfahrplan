import requests
import unicodedata, re
from rapidfuzz import process, fuzz
import pandas as pd
from pathlib import Path
from google.transit import gtfs_realtime_pb2 as gtfs_rt



class GTFSFeed:

    def __init__(self, data: Path,name: str = "vgn"):
        self._data = data
        # TODO: handle conflicting ids across multiple gtfs datasets
        folder = data / "parquet" / name
        glob = folder.glob("*.parquet")
        if not any(glob):
            raise Exception(f"No parquet files found in {folder}")
        for f in glob:
            name = f.stem
            df = pd.read_parquet(f)
            setattr(self, name, df)
        self._tables = [f.stem for f in glob]

    def __repr__(self):
        return f"<GTFSFeed tables={self._tables}>"

    def gtfs_find_station(feed, query: str, limit: int = 10) -> pd.DataFrame:
        def _norm(s: str) -> str:
            s = s.casefold()
            s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
            s = s.replace("ß", "ss")
            s = re.sub(r"[-_/.,]+", " ", s)
            s = re.sub(r"\bstr\.\b|\bstr\b|\bstraße\b", "strasse", s)
            return re.sub(r"\s+", " ", s).strip()

        stops = feed.stops.query("location_type == 0 or location_type.isna()").drop_duplicates(subset=["stop_name"])

        matches = process.extract(
            query,
            stops["stop_name"].tolist(),
            processor=_norm,
            scorer=fuzz.token_set_ratio,
            limit=limit,
        )
        if not matches:
            return stops.iloc[0:0].copy()

        match_rows = pd.DataFrame(matches, columns=["stop_name_match", "score", "idx"])
        match_rows["stop_id"] = stops.iloc[match_rows["idx"]]["stop_id"].values

        # merge score into original structure
        result = stops.merge(match_rows[["stop_id", "score"]], on="stop_id", how="inner")
        result = result.sort_values(["score", "stop_name"], ascending=[False, True]).reset_index(drop=True)
        return result

    def gtfs_reachable_transfers(feed, origin_stop_id: str, max_transfer_time: int = 300, include_origin: bool = False):
        """
        Return all stops reachable from `origin_stop_id` via transfers of type 1 or 2
        whose min_transfer_time <= max_transfer_time.
        Returns the full original stop structure (all columns from feed.stops).
        """
        from collections import defaultdict, deque
        import pandas as pd

        stops = feed.stops.drop_duplicates("stop_id").copy()

        # build undirected adjacency list
        G = defaultdict(set)
        tr = getattr(feed, "transfers", None)
        if tr is not None and not tr.empty:
            t = tr[["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"]].copy()
            t["transfer_type"] = t["transfer_type"].fillna(0).astype(int)
            t["min_transfer_time"] = t["min_transfer_time"].fillna(0).astype(int)
            allowed = t["transfer_type"].isin([1, 2]) & (t["min_transfer_time"] <= int(max_transfer_time))
            t = t[allowed]
            for a, b in t[["from_stop_id", "to_stop_id"]].itertuples(index=False, name=None):
                G[a].add(b)
                G[b].add(a)

        # ensure isolated stop exists
        for sid in stops["stop_id"]:
            G.setdefault(sid, set())

        # BFS search
        seen = set()
        q = deque()
        if origin_stop_id in G:
            seen.add(origin_stop_id)
            q.append(origin_stop_id)

        while q:
            u = q.popleft()
            for v in G[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)

        if not include_origin:
            seen.discard(origin_stop_id)

        # full stop structure for reachable stops
        out = stops[stops["stop_id"].isin(seen)].copy()
        return out.reset_index(drop=True)

    def gtfs_find_siblings(feed, stop_id: str, include_self: bool = False) -> pd.DataFrame:
        df = feed.stops.copy()

        # locate the stop
        row = df.loc[df["stop_id"] == stop_id]
        if row.empty:
            return df.iloc[0:0].copy()

        # determine parent id (normalize blanks to NaN)
        parent = row["parent_station"].iloc[0]
        parent_str = None if pd.isna(parent) or str(parent).strip() == "" else str(parent).strip()
        parent_id = parent_str or str(stop_id)

        # siblings = all children of the parent_id
        sib = df.loc[df["parent_station"].astype(str).str.strip() == parent_id].copy()

        if not include_self:
            sib = sib.loc[sib["stop_id"] != stop_id]

        return sib.reset_index(drop=True)

    def gtfs_find_matching_name_stops(feed, stop_id: str, include_self: bool = False) -> pd.DataFrame:
        """
        Return all stops whose stop_name is identical to the stop_name of the given stop_id.
        If include_self=False, the queried stop_id is excluded.
        """
        df = feed.stops.copy()

        # locate reference stop
        ref = df.loc[df["stop_id"] == stop_id]
        if ref.empty:
            return df.iloc[0:0].copy()

        name = ref["stop_name"].iloc[0]
        same = df.loc[df["stop_name"] == name].copy()

        if not include_self:
            same = same.loc[same["stop_id"] != stop_id]

        return same.reset_index(drop=True)

    def gtfs_find_related_stops(feed, stop_id: str) -> pd.DataFrame:
        stops = feed.stops.query(f"stop_id == @stop_id")
        possible_transfers = feed.gtfs_reachable_transfers(stop_id)
        siblings = feed.gtfs_find_siblings(stop_id)
        same_name = feed.gtfs_find_matching_name_stops(stop_id)
        if len(possible_transfers) > 0:
            stops = pd.concat([stops, possible_transfers], ignore_index=True)
        if len(siblings) > 0:
            stops = pd.concat([stops, siblings], ignore_index=True)
        if len(same_name) > 0:
            stops = pd.concat([stops, same_name], ignore_index=True)
        return stops.drop_duplicates()

    def _load_feed(self,feed_url: str="https://realtime.gtfs.de/realtime-free.pb"):
        r = requests.get(feed_url, timeout=15)
        r.raise_for_status()
        return r
        # class ResponseStub:
        #     def __init__(self, content: bytes):
        #         self.content = content
        #
        # with open(self._data / "feed.pb", "rb") as f:
        #     r = ResponseStub(f.read())
        #     return r
    def gtfs_get_disruptions(feed):
        r = feed._load_feed()
        f = gtfs_rt.FeedMessage()
        f.ParseFromString(r.content)
        tu_rows, vp_rows, al_rows = [], [], []

        for e in f.entity:
            if e.HasField("trip_update"):
                t = e.trip_update
                trip = t.trip.trip_id
                route = t.trip.route_id
                for stu in t.stop_time_update:
                    tu_rows.append({
                        "entity_id": e.id,
                        "trip_id": trip,
                        "route_id": route,
                        "stop_id": stu.stop_id,
                        "seq": stu.stop_sequence,
                        "arr_time": stu.arrival.time if stu.arrival.HasField("time") else None,
                        "dep_time": stu.departure.time if stu.departure.HasField("time") else None,
                        "schedule_rel": t.timestamp if t.HasField("timestamp") else None,
                    })
            if e.HasField("alert"):
                a = e.alert
                header = a.header_text.translation[0].text if a.header_text.translation else ""
                for ie in a.informed_entity:
                    al_rows.append({
                        "entity_id": e.id,
                        "stop_id": ie.stop_id or None,
                        "route_id": ie.route_id or None,
                        "trip_id": ie.trip.trip_id or None,
                        "agency_id": ie.agency_id or None,
                        "effect": int(a.effect),
                        "cause": int(a.cause),
                        "header": header,
                    })

        out = {}
        if tu_rows: out["trip_updates"] = pd.DataFrame.from_records(tu_rows)
        if al_rows: out["alerts"] = pd.DataFrame.from_records(al_rows)
        dfs = out
        alerts = dfs.get("alerts", pd.DataFrame(columns=["stop_id","header","cause","effect"]))
        alerts = alerts[alerts["stop_id"].notna()][["stop_id","header","cause","effect"]]
        return alerts

def map_disruptions(data_folder, stops, alerts):
    mapping = pd.read_parquet(data_folder / "mapping" / "mapping.parquet")
    # normalize dtypes to string (preserves <NA>)
    stops = stops.copy()
    mapping = mapping.copy()
    stops["stop_id"] = stops["stop_id"].astype("string")
    mapping["vgn_id"] = mapping["vgn_id"].astype("string")
    mapping["de_id"]  = mapping["de_id"].astype("string")
    alerts["stop_id"] = alerts["stop_id"].astype("string")

    agg = (
        alerts.groupby("stop_id", dropna=True).agg(
            disruption_text = ("header", lambda s: " | ".join(pd.unique(s.dropna()))),
            disruption_type = ("cause",  lambda s: sorted(set(s.dropna()))),
            disruption_effect = ("effect", lambda s: sorted(set(s.dropna()))),
        )
        .rename_axis("de_id")
        .reset_index()
    )
    agg["de_id"] = agg["de_id"].astype("string")

    out = (
        stops.merge(mapping, left_on="stop_id", right_on="vgn_id", how="left")
        .merge(agg, on="de_id", how="left")
    )
    return out[out[["disruption_text", "disruption_type", "disruption_effect"]].notna().any(axis=1)]
