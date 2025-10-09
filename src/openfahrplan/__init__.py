from dotenv import load_dotenv
from openfahrplan.lib.gtfs import load_feed
import pandas as pd

from openfahrplan.lib.raptor import RaptorIndex

# Pandas Settings
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)
pd.set_option("display.width", 0)

# Load environment variables
load_dotenv()

# Load the gtfs feed
feed = load_feed()
timetable = feed.stops.merge(feed.stop_times).merge(feed.trips).merge(feed.routes)
station_labels = feed.stops[["stop_id", "stop_name"]].drop_duplicates(subset=["stop_name"]).rename(columns={"stop_name": "label", "stop_id": "value"}).to_dict("records")

# Precompute raptor index
raptor_index = RaptorIndex.from_feed(feed)

# Export everything
__all__ = ["feed","timetable","station_labels","raptor_index"]
