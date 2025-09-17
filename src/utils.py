import json

from rapidfuzz import process, fuzz, utils
import pandas as pd
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re

from pathlib import Path
import gtfs_kit as gk

client = OpenAI()

def gtfs_denormalize(feed: pd.DataFrame):
    df = (
        feed.stops
        .merge(feed.stop_times)
        .merge(feed.trips)
        .merge(feed.routes)
    )
    return df

def gtfs_get_longest_stop_pattern(timetable: pd.DataFrame):
    timetable = timetable[timetable["route_short_name"].isin([
        # Display only VAG and infra lines, because rendering all routes, especially bus routes takes a really long time
        "U1", "U2", "U3",
        "S1","S2","S3","S4","S5","S6",
        "4","5","6","7","8","10","11","D",
        "20","21","30","31","32","33","34","35","36","37","38","39","40","43","44","45","46","47","49","50","51","52","53","54","55","56","57","58","59","60","61","62","63","64","65","66","67","68","69","70","71","72","73","81","82","83","84","89","91","92","93","94","95","96","98","99",
        "171","172","173","174","175","176","177","178","179","189"
        "N1","N2","N3","N4","N5","N6","N7","N8","N9","N10","N11","N12","N13","N14","N15","N60","N61",
        "N17","N18","N20","N21"
        "RE 1","RE 7","RE 8","RE 10","RE 14","RE 16","RE 17","RE 19","RE 20","RE 30","RE 31","RE 32","RE 33","RE 40","RE 41","RE 42","RE 49","RE 50"," RE 60","RE 90",
        "RB 11","RB 12","RB 16","RB 21","RB 30","RB 31"
    ])]

    # Add a column with the stop_count to each row
    timetable = timetable.merge(timetable.groupby("trip_id")["stop_id"].nunique().reset_index(name="stop_count"))

    # Keep all rows for those trip_ids
    timetable = timetable[timetable["trip_id"].isin(
        timetable.sort_values(["route_short_name", "stop_count"], ascending=[True, False]).drop_duplicates(
            "route_short_name")[["route_short_name", "trip_id"]]["trip_id"])]
    return timetable

route_colors = {
    "U1": "#114273",
    "U2": "#fa0004",
    "U3": "#227e7f",
    "RE/RB": "#03643b",
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

def get_disruption_color(disruptions):
    if not disruptions:  # no disruptions
        return "grey"
    colors = {get_route_color(line) for line in disruptions}
    return colors.pop() if len(colors) == 1 else "grey"

def fetch_vag_disruptions_page():
    url = "https://www.vag.de/fahrplanaenderungen-stoerungen"
    resp = requests.get(url, timeout=3)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [item.get_text(" ", strip=True) for item in soup.select_one(".linieninfo_list").select(".stoerung__item")]

def fetch_infra_disruptions_page():
    url = "https://www.infra-fuerth.de/privatkunden/infothek/fahrplanaenderung"
    resp = requests.get(url, timeout=3)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [item.get_text(" ", strip=True) for item in soup.find("h2",string="Aktuelle Fahrplanänderungen").find_parent().select(".accs-container")]

def fetch_vgn_disruptions_page():
    url = "https://www.vgn.de/fahrplanaenderungen/"
    resp = requests.get(url, timeout=3)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [item.get_text(" ", strip=True) for item in soup.select_one(".Result").select(".card-block")]

# TODO: if OPENAI_API_KEY is not set or SKIP_OPENAPI is set, return dummy data
def gtfs_get_disruptions(feed):
    texts = fetch_vag_disruptions_page() + fetch_infra_disruptions_page()+ fetch_vgn_disruptions_page()
    prompt = f"""
        Here are disruption announcements from various agency websites:
    
        {json.dumps(texts, ensure_ascii=False, indent=2)}
    
        Task:
        - Identify the affected stop names mentioned in each entry.
        - For each stop, list the disrupted lines.
        - If multiple lines are disrupted at the same stop, put them all in the list.
        - If no stops are clearly affected, skip them.
        - If you cant find an affected line, but the word "Aufzug" is mentioned, pretend the line is "Elevator"
    
        Return ONLY valid JSON array of objects in this format:
        [
          {{"stop_name": "Gustav-Adolf-Str.", "disruptions": ["U1"]}},
          {{"stop_name": "Plärrer", "disruptions": ["U1", "U2"]}}
        ]
        """

    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    raw = resp.output[0].content[0].text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = []

    disruptions = pd.DataFrame(data)
    disruptions["stop_id"] = disruptions.apply(lambda row: gtfs_find_station(feed,row["stop_name"])["stop_id"],axis=1)
    return disruptions

def gtfs_get_fake_disruptions(feed):
    text = """
    [
  {"stop_name": "Hohe Marter", "disruptions": ["Elevator"]},
  {"stop_name": "Fürth Rathaus", "disruptions": ["Elevator"]},
  {"stop_name": "Nürnberg Hauptbahnhof Mittelhalle", "disruptions": ["Elevator"]},
  {"stop_name": "Herrnhütte", "disruptions": ["Elevator"]},
  {"stop_name": "Rathenauplatz", "disruptions": ["U2", "U3", "8"]},
  {"stop_name": "Herzogstr.", "disruptions": ["55", "96"]},
  {"stop_name": "Fallrohrstr.", "disruptions": ["43", "94"]},
  {"stop_name": "Burgthann Bahnhof straße", "disruptions": ["N15"]},
  {"stop_name": "Obstmarkt", "disruptions": ["37", "46", "47"]},
  {"stop_name": "Maxfeld", "disruptions": ["37", "46", "47"]},
  {"stop_name": "Thumenberger Weg im Bereich Martin-Albert-Straße", "disruptions": ["45"]},
  {"stop_name": "Edisonstraße", "disruptions": ["69"]},
  {"stop_name": "Sprottauer Str.", "disruptions": ["56"]},
  {"stop_name": "Vincenzenbronn", "disruptions": ["N7"]},
  {"stop_name": "Kraftshof", "disruptions": ["31"]},
  {"stop_name": "Balbiererstraße", "disruptions": ["N18"]},
  {"stop_name": "Leyher Straße", "disruptions": ["177"]},
  {"stop_name": "Zirndorfer Straße", "disruptions": ["178", "N18"]},
  {"stop_name": "Neumannstraße", "disruptions": ["178", "N18"]},
  {"stop_name": "Erlöserkirche", "disruptions": ["178", "N18"]},
  {"stop_name": "Vestner Weg", "disruptions": ["178", "N18"]},
  {"stop_name": "Saarburger Straße", "disruptions": ["178", "N18"]},
  {"stop_name": "Flößaustraße", "disruptions": ["178", "N18"]},
  {"stop_name": "Kaiserstraße", "disruptions": ["178", "N18"]},
  {"stop_name": "Dr.-Frank-Straße", "disruptions": ["178", "N18"]},
  {"stop_name": "Rosen-/Theaterstraße", "disruptions": ["172"]},
  {"stop_name": "Stadthalle Süd", "disruptions": ["172"]},
  {"stop_name": "Katharinenstraße", "disruptions": ["172"]},
  {"stop_name": "Theaterstraße", "disruptions": ["172"]},
  {"stop_name": "Mathildenstraße", "disruptions": ["172"]},
  {"stop_name": "Maxstraße", "disruptions": ["172"]},
  {"stop_name": "Weiherstraße", "disruptions": ["172"]},
  {"stop_name": "Mariensteig", "disruptions": ["172"]},
  {"stop_name": "Mondstraße", "disruptions": ["172"]},
  {"stop_name": "Maxstraße", "disruptions": ["172"]},
  {"stop_name": "Hauptbahnhof", "disruptions": ["172"]},
  {"stop_name": "Hirschenstraße", "disruptions": ["172"]},
  {"stop_name": "Schönblick", "disruptions": ["171", "174", "175"]},
  {"stop_name": "Am Vacher Markt", "disruptions": ["171", "174", "175"]},
  {"stop_name": "Am Festplatz", "disruptions": ["171", "175"]},
  {"stop_name": "Flexdorfer Straße", "disruptions": ["171", "175"]},
  {"stop_name": "Am Altengraben", "disruptions": ["171", "175"]},
  {"stop_name": "Vach Nord", "disruptions": ["171", "175"]},
  {"stop_name": "Mannhof", "disruptions": ["174"]},
  {"stop_name": "Königstraße", "disruptions": ["175"]},
  {"stop_name": "Rathaus", "disruptions": ["175"]},
  {"stop_name": "Maxbrücke", "disruptions": ["175"]},
  {"stop_name": "Billinganlage", "disruptions": ["175"]},
  {"stop_name": "Grüner Markt", "disruptions": ["175"]},
  {"stop_name": "Kulturforum", "disruptions": ["175"]},
  {"stop_name": "Kapellenstraße", "disruptions": ["175", "125", "126", "N9", "N22", "N23"]},
  {"stop_name": "Nürnberg, Frankenstadion", "disruptions": ["S1", "S3"]},
  {"stop_name": "Nürnberg Hbf", "disruptions": ["S5"]},
  {"stop_name": "Wiesau, Hauptstr. 66", "disruptions": ["1857", "1858", "1862"]},
  {"stop_name": "Lauf, Markt­platz", "disruptions": ["332", "344", "345", "351", "352", "353"]},
  {"stop_name": "Goldkronach", "disruptions": ["329", "330", "367"]},
  {"stop_name": "Reckendorf, Orts­mit­te", "disruptions": ["953"]},
  {"stop_name": "Reckenneusig", "disruptions": ["953"]},
  {"stop_name": "Su.-Ro., Rosenberger Str.", "disruptions": ["420", "421", "422", "423", "424", "425", "426", "427", "447", "448", "456", "457", "463", "464", "466", "477", "479", "480", "481", "486"]},
  {"stop_name": "Su.-Ro., Luitpoldplatz", "disruptions": ["420", "421", "422", "423", "424", "425", "426", "427", "447", "448", "456", "457", "463", "464", "466", "477", "479", "480", "481", "486"]},
  {"stop_name": "Su.-Ro., Arbeitsamt (stadt­ein­wärts)", "disruptions": ["420", "421", "422", "423", "424", "425", "426", "427", "447", "448", "456", "457", "463", "464", "466", "477", "479", "480", "481", "486"]},
  {"stop_name": "Pfisterstraße", "disruptions": ["922"]},
  {"stop_name": "Bruck Bahnhof", "disruptions": ["284", "293"]},
  {"stop_name": "Skulpturenpark", "disruptions": ["290", "295"]},
  {"stop_name": "Hallstadt Schule", "disruptions": ["904"]},
  {"stop_name": "Rother Str.", "disruptions": ["663"]},
  {"stop_name": "Grenzstr.", "disruptions": ["751"]},
  {"stop_name": "Bocksbergsiedlung Ost", "disruptions": ["751"]},
  {"stop_name": "Bocksbergsiedlung West", "disruptions": ["751"]},
  {"stop_name": "Sonnenstraße", "disruptions": ["751"]},
  {"stop_name": "Funkenbachstr.", "disruptions": ["751", "755"]},
  {"stop_name": "Industriestr.", "disruptions": ["751", "755"]},
  {"stop_name": "Rezathalle", "disruptions": ["751", "755"]},
  {"stop_name": "Philipp-Zorn-Str.", "disruptions": ["753"]},
  {"stop_name": "Welserstr. Ost", "disruptions": ["753"]},
  {"stop_name": "Welserstr. West", "disruptions": ["753"]},
  {"stop_name": "Endresstraße", "disruptions": ["756"]},
  {"stop_name": "Weinberg, Kindergarten", "disruptions": ["804", "805"]},
  {"stop_name": "Weinberg", "disruptions": ["805"]},
  {"stop_name": "Carl-Schmolz-Weg", "disruptions": ["910"]},
  {"stop_name": "Hartlandener Straße", "disruptions": ["912"]},
  {"stop_name": "Schellenbergerstr.", "disruptions": ["918"]},
  {"stop_name": "Pfisterstraße", "disruptions": ["922"]},
  {"stop_name": "Am Tauschenberg", "disruptions": ["927"]},
  {"stop_name": "Kersbach Fliederweg", "disruptions": ["224", "260", "264"]},
  {"stop_name": "Oberehrenbach Kirchplatz", "disruptions": ["223"]},
  {"stop_name": "Unterailsfeld", "disruptions": ["231", "232"]},
  {"stop_name": "Höchstadt, Schillerplatz", "disruptions": ["238", "245"]},
  {"stop_name": "Höchstadt, Aischwiese", "disruptions": ["245"]},
  {"stop_name": "Am Friedhof", "disruptions": ["Baiersdorf"]},
  {"stop_name": "Baiersdorf Bahnhof Westseite", "disruptions": ["Baiersdorf"]},
  {"stop_name": "Erlanger Straße", "disruptions": ["Baiersdorf", "254", "254"]},
  {"stop_name": "Kraftshof", "disruptions": ["31"]},
  {"stop_name": "Cadolzburg, Schafhofstr.", "disruptions": ["118", "126"]},
  {"stop_name": "Ohmplatz", "disruptions": ["281", "289", "290", "295"]},
  {"stop_name": "Su.-Ro., Dolestr.", "disruptions": ["421"]},
  {"stop_name": "Obersdorf, Frohnbergstr.", "disruptions": ["421"]},
  {"stop_name": "Obersdorf, Dorfstr.", "disruptions": ["421"]},
  {"stop_name": "Zirndorf, Markt­platz", "disruptions": ["150"]},
  {"stop_name": "Zirndorf, Angerzeile", "disruptions": ["150"]},
  {"stop_name": "Zirndorf, Ost", "disruptions": ["150"]},
  {"stop_name": "Hallstadt Schule", "disruptions": ["904"]},
  {"stop_name": "Neunkirchen am Brand", "disruptions": ["209"]},
  {"stop_name": "Dörfles-Esbach Bahnhof", "disruptions": ["1403", "1423", "1424", "1427", "1429", "1431", "1433", "1434", "1405", "1425"]},
  {"stop_name": "Reckendorf Ortsmitte", "disruptions": ["953"]},
  {"stop_name": "Rohrbach (CO)", "disruptions": ["1454.2", "1467"]},
  {"stop_name": "Buscheller", "disruptions": ["1454.2", "1467"]},
  {"stop_name": "Haimendorf", "disruptions": ["661"]},
  {"stop_name": "Pegnitz Schmiedpeunt", "disruptions": ["389"]},
  {"stop_name": "Pegnitz Gymnasium", "disruptions": ["389"]},
  {"stop_name": "Freihung, Industriestraße", "disruptions": ["449", "480"]},
  {"stop_name": "Theresienstein", "disruptions": ["1562"]},
  {"stop_name": "Unteres Tor", "disruptions": ["1562"]},
  {"stop_name": "Rathaus", "disruptions": ["1562"]},
  {"stop_name": "Karlstraße", "disruptions": ["1562"]},
  {"stop_name": "Waldstraße", "disruptions": ["N18"]},
  {"stop_name": "Balbiererstraße", "disruptions": ["N18"]},
  {"stop_name": "Vach, Am Vacher Markt", "disruptions": ["121"]},
  {"stop_name": "Vach, Am Vacher Markt", "disruptions": ["171", "174", "175"]}
]
    """

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = []
    disruptions =  pd.DataFrame(data)
    disruptions["stop_id"] = disruptions.apply(lambda row: gtfs_find_station(feed,row["stop_name"])["stop_id"],axis=1)
    disruptions["color"] = disruptions["disruptions"].apply(get_disruption_color)
    return disruptions

def load_feed():
    project_root = Path(__file__).parent.parent
    # TODO: handle conflicting ids across multiple gtfs datasets
    return gk.read_feed(project_root/"data/gtfs/vgn/GTFS.zip",dist_units="km")

def gtfs_find_station(feed, query: str) -> str:
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
    children = feed.stops[feed.stops['parent_station'] == parent["stop_id"]]
    return parent


