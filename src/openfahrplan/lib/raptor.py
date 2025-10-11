# raptor_fast.py
from collections import defaultdict, deque
import math, re, heapq, bisect
import numpy as np
import pandas as pd

from openfahrplan.lib.debug import timed

_TIME = re.compile(r"^\d{1,2}:\d{2}:\d{2}$")
def _parse_gtfs_time(t) -> float:
    if t is None: return math.inf
    try:
        if t != t: return math.inf
    except Exception:
        pass
    s = str(t)
    if not _TIME.match(s): return math.inf
    h, m, s2 = map(int, s.split(":"))
    return h*3600 + m*60 + s2

class RaptorIndex:
    """Precompute everything heavy once."""
    __slots__ = ("stop_ids","stop_to_idx","trips","stop2tripidx",
                 "events_dep","events_tid","events_idx","foot","nstops")

    @classmethod
    def from_feed(cls, feed):
        idx = cls()
        st = feed.stop_times[["trip_id","stop_id","arrival_time","departure_time","stop_sequence"]].copy()
        # parse and drop invalid
        st["arr_sec"] = st["arrival_time"].map(_parse_gtfs_time)
        st["dep_sec"] = st["departure_time"].map(_parse_gtfs_time)
        st = st[np.isfinite(st["arr_sec"]) & np.isfinite(st["dep_sec"])].copy()
        if st.empty:
            # empty index
            idx.stop_ids = pd.Index([])
            idx.stop_to_idx = {}
            idx.trips = {}
            idx.stop2tripidx = {}
            idx.events_dep = []
            idx.events_tid = []
            idx.events_idx = []
            idx.foot = {}
            idx.nstops = 0
            return idx

        # stable universe
        idx.stop_ids = pd.Index(feed.stops["stop_id"].unique())
        idx.stop_to_idx = {sid:i for i,sid in enumerate(idx.stop_ids)}
        st["stop_sequence"] = st["stop_sequence"].astype(int)
        st = st.sort_values(["trip_id","stop_sequence"])
        st["stop_i"] = st["stop_id"].map(idx.stop_to_idx)

        # trips as numpy
        trips = {}
        for tid, g in st.groupby("trip_id", sort=False):
            trips[tid] = {
                "stops": g["stop_i"].to_numpy(dtype=np.int32, copy=False),
                "arr":   g["arr_sec"].to_numpy(dtype=np.int64, copy=True),
                "dep":   g["dep_sec"].to_numpy(dtype=np.int64, copy=True),
            }
        idx.trips = trips

        # stop -> first index in trip
        stop2tripidx = defaultdict(list)
        for tid, tp in trips.items():
            seen = {}
            for i, si in enumerate(tp["stops"]):
                if si not in seen:
                    seen[si] = i
            for si, i0 in seen.items():
                stop2tripidx[si].append((tid, i0))
        idx.stop2tripidx = stop2tripidx

        # per-stop departure events for binary search
        nstops = len(idx.stop_ids)
        idx.nstops = nstops
        events_dep   = [np.empty(0, dtype=np.int64) for _ in range(nstops)]
        events_tid   = [np.empty(0, dtype=object)   for _ in range(nstops)]
        events_index = [np.empty(0, dtype=np.int32) for _ in range(nstops)]
        buckets = defaultdict(list)
        for tid, tp in trips.items():
            # only first boardable occurrence per stop
            seen = {}
            for i, si in enumerate(tp["stops"]):
                if si not in seen:
                    seen[si] = i
            for si, i0 in seen.items():
                buckets[si].append((tp["dep"][i0], tid, i0))
        for si, lst in buckets.items():
            lst.sort(key=lambda x: x[0])
            if lst:
                events_dep[si]   = np.fromiter((x[0] for x in lst), dtype=np.int64, count=len(lst))
                events_tid[si]   = np.array([x[1] for x in lst], dtype=object)
                events_index[si] = np.fromiter((x[2] for x in lst), dtype=np.int32, count=len(lst))
        idx.events_dep, idx.events_tid, idx.events_idx = events_dep, events_tid, events_index

        # footpaths from transfers.txt
        foot = defaultdict(list)
        for sid in feed.stops["stop_id"].drop_duplicates():
            i = idx.stop_to_idx.get(sid)
            if i is not None:
                foot[i].append((i, 0))
        tr = getattr(feed, "transfers", None)
        if tr is not None and not tr.empty:
            tr = tr[["from_stop_id","to_stop_id","transfer_type","min_transfer_time"]].copy()
            tr["transfer_type"] = tr["transfer_type"].fillna(0).astype(int)
            tr = tr[tr["transfer_type"] != 3]
            tr["min_transfer_time"] = tr["min_transfer_time"].fillna(0).astype(int)
            for a,b,w in tr[["from_stop_id","to_stop_id","min_transfer_time"]].itertuples(index=False, name=None):
                ia = idx.stop_to_idx.get(a); ib = idx.stop_to_idx.get(b)
                if ia is not None and ib is not None:
                    foot[ia].append((ib, int(w)))
        idx.foot = foot
        return idx

def raptor_route(index: RaptorIndex, start_stop_id, end_stop_id,
                 departure_time="08:00:00", max_rounds=8):
    if index.nstops == 0:
        return None
    s_idx = index.stop_to_idx.get(start_stop_id)
    t_idx = index.stop_to_idx.get(end_stop_id)
    if s_idx is None or t_idx is None:
        return None

    dep0 = _parse_gtfs_time(str(departure_time))
    INF = math.inf
    best_prev = [INF]*index.nstops
    best_prev[s_idx] = dep0
    parents = [dict() for _ in range(max_rounds+1)]

    def relax_footpaths(best, seeds):
        pq = []
        inq = [False]*index.nstops
        pred = {u: None for u in seeds}
        for u in seeds:
            if best[u] < INF and not inq[u]:
                heapq.heappush(pq, (best[u], u)); inq[u] = True
        improved = set()
        while pq:
            t,u = heapq.heappop(pq)
            if t > best[u]: continue
            improved.add(u)
            for v,w in index.foot.get(u, []):
                nt = t + w
                if nt < best[v]:
                    best[v] = nt
                    pred[v] = u
                    heapq.heappush(pq, (nt, v))
                    inq[v] = True
        return improved, pred

    # initial walk
    marked, pred0 = relax_footpaths(best_prev, {s_idx})
    for v,u in pred0.items():
        if u is not None:
            parents[1][v] = (u, None)

    for r in range(1, max_rounds+1):
        best_cur = best_prev[:]  # copy
        route_queue = {}

        # collect routes using per-stop departure events
        for si in marked:
            t_arr = best_prev[si]
            dep_arr = index.events_dep[si]
            if dep_arr.size == 0 or t_arr >= INF: continue
            pos = dep_arr.searchsorted(t_arr, side="left")
            if pos >= dep_arr.size: continue
            tid_arr = index.events_tid[si]; idx_arr = index.events_idx[si]
            for k in range(pos, dep_arr.size):
                tid = tid_arr[k]; j = int(idx_arr[k])
                prev = route_queue.get(tid)
                if prev is None or j < prev:
                    route_queue[tid] = j

        if not route_queue:
            break

        new_marked = set()
        for tid, j in route_queue.items():
            tp = index.trips[tid]
            stops_arr = tp["stops"]; arr = tp["arr"]
            prev_stop = int(stops_arr[j])
            for k in range(j+1, len(stops_arr)):
                v = int(stops_arr[k]); av = int(arr[k])
                if av < best_cur[v]:
                    best_cur[v] = av
                    parents[r][v] = (prev_stop, tid)
                    new_marked.add(v)
                prev_stop = v

        if not new_marked:
            best_prev = best_cur
            break

        fp_improved, pred = relax_footpaths(best_cur, new_marked)
        for v in fp_improved:
            if v in new_marked: continue
            u = pred.get(v)
            if u is not None and v not in parents[r]:
                parents[r][v] = (u, None)

        best_prev = best_cur
        marked = fp_improved
        if best_prev[t_idx] < INF:
            break

    if best_prev[t_idx] >= INF:
        return None

    # reconstruct
    stop_ids = index.stop_ids
    final_r = 0
    for rr in range(max_rounds, 0, -1):
        if t_idx in parents[rr]:
            final_r = rr; break
    path = deque([t_idx]); legs = deque()
    cur = t_idx; rr = final_r
    while cur != s_idx and rr > 0:
        if cur not in parents[rr]:
            rr -= 1; continue
        prev, via = parents[rr][cur]
        if via is None:
            legs.appendleft(("walk", best_prev[cur]-best_prev[prev], stop_ids[prev], stop_ids[cur]))
        else:
            legs.appendleft(("trip", via, stop_ids[prev], stop_ids[cur]))
        path.appendleft(prev); cur = prev
        if cur not in parents[rr]:
            rr -= 1

    # merge consecutive walks
    merged = []
    for leg in legs:
        if merged and leg[0]=="walk" and merged[-1][0]=="walk" and merged[-1][3]==leg[2]:
            k,t,a,b = merged.pop()
            merged.append(("walk", t+leg[1], a, leg[3]))
        else:
            merged.append(leg)

    return {
        "stops": [stop_ids[i] for i in path],
        "trips": [x[1] for x in merged if x[0]=="trip"],
        "legs": list(merged),
        "arrival_time_sec": int(best_prev[t_idx]),
    }