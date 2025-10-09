# import json
#
# import pandas as pd
# from openai import OpenAI
# import requests
# from bs4 import BeautifulSoup
# import os
# from openfahrplan.lib.gtfs import gtfs_find_station
# from openfahrplan.lib.display import get_route_color
# from openfahrplan.lib.station_search import gtfs_find_station_grouped
#
# if os.getenv("OPENAI_API_KEY"):
#     client = OpenAI()
#
# def fetch_vag_disruptions_page():
#     url = "https://www.vag.de/fahrplanaenderungen-stoerungen"
#     resp = requests.get(url, timeout=3)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     return [item.get_text(" ", strip=True) for item in soup.select_one(".linieninfo_list").select(".stoerung__item")]
#
# def fetch_infra_disruptions_page():
#     url = "https://www.infra-fuerth.de/privatkunden/infothek/fahrplanaenderung"
#     resp = requests.get(url, timeout=3)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     return [item.get_text(" ", strip=True) for item in soup.find("h2",string="Aktuelle Fahrplanänderungen").find_parent().select(".accs-container")]
#
# def fetch_vgn_disruptions_page():
#     url = "https://www.vgn.de/fahrplanaenderungen/"
#     resp = requests.get(url, timeout=3)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     return [item.get_text(" ", strip=True) for item in soup.select_one(".Result").select(".card-block")]
#
# # TODO: if OPENAI_API_KEY is not set or SKIP_OPENAPI is set, return dummy data
# def gtfs_get_disruptions(feed):
#     raw = mock_disruptions
#     if os.getenv("OPENAI_API_KEY"):
#         texts = fetch_vag_disruptions_page() + fetch_infra_disruptions_page()+ fetch_vgn_disruptions_page()
#         prompt = f"""
#             Here are disruption announcements from various agency websites:
#
#             {json.dumps(texts, ensure_ascii=False, indent=2)}
#
#             Task:
#             - Identify the affected stop names mentioned in each entry.
#             - For each stop, list the disrupted lines.
#             - If multiple lines are disrupted at the same stop, put them all in the list.
#             - If no stops are clearly affected, skip them.
#             - If you cant find an affected line, but the word "Aufzug" is mentioned, pretend the line is "Elevator"
#
#             Return ONLY valid JSON array of objects in this format:
#             [
#               {{"stop_name": "Gustav-Adolf-Str.", "disruptions": ["U1"]}},
#               {{"stop_name": "Plärrer", "disruptions": ["U1", "U2"]}}
#             ]
#             """
#
#         resp = client.responses.create(
#             model="gpt-4.1-mini",
#             input=prompt
#         )
#
#         raw = resp.output[0].content[0].text.strip()
#         print("Successfully issued openai request")
#     try:
#         data = json.loads(raw)
#     except json.JSONDecodeError:
#         data = []
#
#     disruptions = pd.DataFrame(data)
#     print(disruptions.head(1)["stop_name"].squeeze())
#     disruptions["stop_id"] = disruptions.apply(lambda row: gtfs_find_station_grouped(feed,row["stop_name"].squeeze())["stop_id"],axis=1)
#     disruptions["color"] = disruptions["disruptions"].apply(get_disruption_color)
#     return disruptions
#
# def get_disruption_color(disruptions):
#     if not disruptions:  # no disruptions
#         return "grey"
#     colors = {get_route_color(line) for line in disruptions}
#     return colors.pop() if len(colors) == 1 else "grey"
#
# mock_disruptions =  text = """
#     [
#   {"stop_name": "Herrnhütte", "disruptions": ["Elevator"]},
#   {"stop_name": "Hohe Marter", "disruptions": ["Elevator"]},
#   {"stop_name": "Nürnberg Hauptbahnhof Mittelhalle", "disruptions": ["Elevator"]},
#   {"stop_name": "Rathenauplatz", "disruptions": ["U2", "U3", "8"]},
#   {"stop_name": "Maxfeld", "disruptions": ["37", "46", "47"]},
#   {"stop_name": "Kraftshof", "disruptions": ["31"]}
# ]
#     """