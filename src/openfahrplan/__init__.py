import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import logging
from openfahrplan.lib.gtfs import GTFSFeed
from openfahrplan.lib.raptor import RaptorIndex

# Pandas Settings
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.expand_frame_repr", False)
pd.set_option("display.width", 0)

# Load environment variables
load_dotenv()

# Set data path
data_folder = Path(os.getenv("OPENFAHRPLAN_DATA_DIR", Path(__file__).parent /".."/".."/ "data"))

# Load the gtfs feed
logging.info("Start init.")
logging.info("Loading gtfs feed...")
feed = GTFSFeed(data_folder)
timetable = feed.stops.merge(feed.stop_times).merge(feed.trips).merge(feed.routes)
station_labels = feed.stops[["stop_id", "stop_name"]].drop_duplicates(subset=["stop_name"]).rename(columns={"stop_name": "label", "stop_id": "value"}).to_dict("records")

logging.info("Precomputing raptor index...")
raptor_index = RaptorIndex.from_feed(feed)

logging.info("Init done.")

# Export everything
__all__ = ["feed","timetable","station_labels","raptor_index", "data_folder"]
