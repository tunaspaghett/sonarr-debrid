import http.client
from dotenv import load_dotenv
import os
import asyncio
import json
from datetime import datetime
import pytz
import traceback
import threading
import sys
from codecs import encode
import time

# Load environment variables
load_dotenv()

def set_env():
    """
    Load API key, host, and port from environment variables.
    Returns the API key, host, and port as a tuple.
    """
    api_key = os.getenv("API_KEY")
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8989))
    return api_key, host, port

def connect_http(host, port):
    """
    Create and return an HTTP connection to the specified host and port.
    """
    return http.client.HTTPConnection(host, port)

def send_request(api_key, conn, endpoint):
    """
    Send a GET request to the specified endpoint with the given API key.
    """
    conn.request("GET", f"{endpoint}?apikey={api_key}", '')

def get_response(conn):
    """
    Retrieve the HTTP response from the connection and return its content.
    """
    return conn.getresponse().read()

def decode_response(response):
    """
    Decode the HTTP response and return it as a string.
    """
    return response.decode('utf-8')

def has_aired(episode):
    """
    Check if an episode has aired by comparing the current time
    to the UTC air date of the episode.
    """
    utc_time = datetime.strptime(episode['airDateUtc'], "%Y-%m-%dT%H:%M:%SZ")
    utc_time = pytz.UTC.localize(utc_time)
    return datetime.now(pytz.UTC) > utc_time

def see_if_imdb_exists(episode):
    """
    Check if the IMDb ID exists in the episode data.
    Returns the IMDb ID or "0" if not found.
    """
    return episode.get("series", {}).get("imdbId", "0")

def get_json(file_path='data.json'):
    """
    Load and return JSON data from a file.
    If the file doesn't exist or contains invalid data, return an empty list.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            raise ValueError("JSON file must contain a list at the top level.")
    except (FileNotFoundError, ValueError):
        return []

def save_json(data, file_path='data.json'):
    """
    Save the given data to a JSON file.
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def insert_episode(episode, file_path='data.json'):
    """
    Insert episode details into the JSON file if not already present.
    """
    data = get_json(file_path)
    
    # Check if the episode ID already exists in the data
    existing = next((obj for obj in data if obj.get("id") == episode["id"]), None)
    
    if existing is None:
        # Episode not found; add it
        episode["has_downloaded"] = False
        data.append(episode)
        print(f"{episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']} added to search")
    else:
        # Episode already exists; check if it's downloaded or still searching
        if existing["has_downloaded"]:
            print(f"{episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']} already downloaded.")
        else:
            print(f"{episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']} already searching.")
    
    # Save the updated data back to the file
    time.sleep(5)
    save_json(data, file_path)

def send_torrent_io_request(url):
    """
    Send a GET request to Torrentio and return the response as a string.
    """
    conn = http.client.HTTPSConnection("torrentio.strem.fun")
    conn.request("GET", url, '', {})
    res = conn.getresponse()
    return res.read().decode('utf-8')

def check_torrentio(imdb_id, season, episode):
    """
    Check Torrentio for torrents using the IMDb ID, season, and episode.
    """
    url = f"/sort=size%7Cqualityfilter=other,scr,cam,unknown/stream/series/{imdb_id}:{season}:{episode}.json"
    return send_torrent_io_request(url)

def sort_results_by_seeders(results):
    """
    Sort torrent results by the number of seeders in descending order.
    """
    return sorted(results['streams'], key=lambda x: int(x['title'].split('👤 ')[1].split(' ')[0]), reverse=True)

def filter_hdr(torrents):
    """
    Filter out torrents that contain 'HDR' in the title.
    """
    return [torrent for torrent in torrents if "HDR" not in torrent["title"]]

def remove_different_languages(possible):
    """
    Remove torrents containing specific banned words.
    """
    banned_words = os.getenv("BANNED_WORDS", "[]")
    try:
        banned_words = json.loads(banned_words)
    except json.JSONDecodeError:
        banned_words = []
    return [item for item in possible if not any(banned_word in item['title'] for banned_word in banned_words)]

        
def send_request_to_real_debrid(endpoint, data=None):
    """
    Send a POST request to Real-Debrid API with given endpoint and data.
    """
    rd_key = os.getenv("DEBRID_KEY")
    conn = http.client.HTTPSConnection("api.real-debrid.com")
    boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

    dataList = [
        encode('--' + boundary),
        encode('Content-Disposition: form-data; name={};'.format(data.keys()[0] if data else '')),
        encode('Content-Type: {}'.format('text/plain')),
        encode(''),
        encode(data.get(next(iter(data.keys())), '')) if data else encode(''),
        encode('--' + boundary + '--'),
        encode('')
    ]
    body = b'\r\n'.join(dataList)
    payload = body
    headers = {
        'Authorization': f'Bearer {rd_key}',
        'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }

    conn.request("POST", endpoint, payload, headers)
    res = conn.getresponse()
    return res.read().decode("utf-8")

def send_magnet_debrid(magnet):
    """Send the magnet link to Real-Debrid."""
    endpoint = "/rest/1.0/torrents/addMagnet"
    data = {"magnet": magnet}
    return send_request_to_real_debrid(endpoint, data)

def start_torrent_download(response):
    """Start the download for a given torrent using Real-Debrid."""
    torrent_id = json.loads(response)["id"]
    endpoint = "/rest/1.0/torrents/selectFiles/" + torrent_id
    data = {"files": "all"}
    return send_request_to_real_debrid(endpoint, data)

def loop_results(results):
    """
    Process torrent results by sorting them based on seeders.
    """
    return sort_results_by_seeders(results)

def loop_episodes(data):
    """
    Process each episode in the given data, find torrents, and display magnet links.
    """
    for episode in data:
        imdb_id = see_if_imdb_exists(episode)
        if imdb_id != "0":
            if episode["has_downloaded"] == True:
                continue
            print(f"Finding torrents for {episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']}")
            results = json.loads(check_torrentio(imdb_id, episode['seasonNumber'], episode['episodeNumber']))
            print(f"Found {len(results['streams'])} possible torrents")
            sorted_results = loop_results(results)
            filtered_results = remove_different_languages(sorted_results)
            if os.getenv("HDR_MODE") == "false":
                print("Removing HDR entries as HDR_MODE is disabled in the environment.")
                filtered_results = filter_hdr(filtered_results)
            if filtered_results:
                magnet = find_magnet(filtered_results[0])
                print(f"Best torrent magnet: {magnet}")
                rd_response = send_magnet_debrid(magnet)
                print(rd_response)
                print("Sent magnet to debrid")
                #files = select_files_from_rd(json.loads(rd_response)["id"])
                #files = format_files(files)
                start_torrent_download(rd_response)
                print("Removing episode from watch list")
                time.sleep(3)
                remove_episode(episode)

def remove_episode(episode):
    """
    Removing from search. Not from the json, because we need to know we already downloaded it 
    """
    data = get_json()
    for item in data:
        if item == episode:
            item["has_downloaded"] = True
    save_json(data)

def find_magnet(torrent):
    """
    Generate a magnet link from torrent data.
    """
    return "magnet:?xt=urn:btih:" + torrent['infoHash']

def check_for_torrents():
    """
    Check for torrents of episodes in the JSON file.
    """
    data = get_json()
    loop_episodes(data)

def get_episode_details(show):
    """
    Retrieve detailed episode information using the API.
    """
    api_key, host, port = set_env()
    conn = connect_http(host, port)
    send_request(api_key, conn, f"/api/v3/episode/{show['id']}")
    return json.loads(decode_response(get_response(conn)))

def loop_through_calendar(calendar):
    """
    Process each show in the calendar, checking if episodes have aired.
    """
    for show in json.loads(calendar):
        try:
            episode = get_episode_details(show)
            print(f"Found {episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']} Released: {episode['airDateUtc']}")
            if has_aired(episode):
                insert_episode(episode)
            else:
                print(f"{episode['series']['title']} Season {episode['seasonNumber']} Episode {episode['episodeNumber']} has not aired. Ignoring.")
        except KeyError as e:
            print(f"Missing key in show data: {e}")

def update_library():
    print("Updating Jellyfin Library")
    if os.getenv("JELLYFIN") == "true":
        update_jellyfin_library()
def update_jellyfin_library():
    """connect to jellyfin and update the library"""
    host,port,api_key = (os.getenv(key) for key in ["JELLYFIN_HOST","JELLYFIN_PORT","JELLYFIN_API_TOKEN"])
    conn = http.client.HTTPConnection(host, int(port))
    payload = ''
    headers = {
    'Authorization': api_key
    }
    conn.request("POST", "/Library/Refresh", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))

async def get_calendar():
    """
    Retrieve the calendar data from the API.
    """
    api_key, host, port = set_env()
    conn = connect_http(host, port)
    send_request(f"{api_key}", conn, "/api/v3/calendar")
    return decode_response(get_response(conn))

# Flag to control the loop
running = True

async def main():
    """
    Main function to retrieve the calendar, update it, and check for torrents.
    """
    try:
        calendar = await get_calendar()
        print("Finding shows airing today")
        time.sleep(5)
        loop_through_calendar(calendar)
        print("Calendar updated, searching backlog")
        time.sleep(5)
        check_for_torrents()
        update_library()
        print("Finished, see you soon")
    except Exception as e:
        traceback.print_exc()

def start_timer(interval):
    """
    Start a timer to periodically run the main function.
    """
    global running

    def run_main():
        if running:
            asyncio.run(main())
            threading.Timer(interval, run_main).start()

    run_main()

try:
    start_timer(600) #how long before each run to wait
except KeyboardInterrupt:
    running = False
    sys.exit()
