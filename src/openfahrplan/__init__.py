from dotenv import load_dotenv
from openfahrplan.lib.gtfs import load_feed, gtfs_build_graph
import pandas as pd

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)
pd.set_option("display.width", 0)

load_dotenv()

feed = load_feed()
timetable = feed.stops.merge(feed.stop_times).merge(feed.trips).merge(feed.routes)
graph,coords = gtfs_build_graph(feed)
__all__ = ["feed","timetable","graph"]
