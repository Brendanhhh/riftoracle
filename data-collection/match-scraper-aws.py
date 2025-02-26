import os
import json
import csv
import time
import requests
import logging
from datetime import datetime, timedelta

# --- Configuration ---
# Read sensitive info from environment variables (set these on your EC2 instance)
API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    raise Exception("Please set the RIOT_API_KEY environment variable.")

REGION = os.getenv("RIOT_REGION", "na1")
REGIONAL_ENDPOINT = os.getenv("RIOT_REGIONAL_ENDPOINT", "americas")
TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"]
DIVISIONS = ["I", "II", "III", "IV"]

# Define base directory relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")
CSV_FILE = os.path.join(BASE_DIR, "match_ids.csv")
MATCHES_DIR = os.path.join(BASE_DIR, "matches")

# --- Logging Setup ---
logging.basicConfig(
    filename=os.path.join(BASE_DIR, "match_scraper.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# --- Rate limiting setup ---
REQUEST_LIMIT = 100
WINDOW_SECONDS = 120
request_timestamps = []

# --- In-memory cache for summoner PUUIDs ---
puuid_cache = {}

# --- Utility functions for state management ---
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

# --- Rate limiting ---
def rate_limit_sleep():
    global request_timestamps
    now = datetime.now()
    # Remove timestamps older than the time window
    request_timestamps = [t for t in request_timestamps if t > now - timedelta(seconds=WINDOW_SECONDS)]
    if len(request_timestamps) >= REQUEST_LIMIT:
        oldest = request_timestamps[0]
        sleep_time = (oldest + timedelta(seconds=WINDOW_SECONDS)) - now
        logging.info(f"Rate limit reached. Sleeping {sleep_time.total_seconds():.1f}s")
        time.sleep(max(sleep_time.total_seconds(), 0))
    request_timestamps.append(now)

# --- API call with iterative retry ---
def make_api_call(url):
    while True:
        rate_limit_sleep()
        try:
            response = requests.get(url, headers={"X-Riot-Token": API_KEY})
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                logging.warning(f"429 Received. Sleeping {retry_after}s")
                time.sleep(retry_after)
                continue  # Retry the request
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"API Error: {str(e)}")
            return None

# --- API helper functions ---
def get_players(tier, division, page=1):
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page={page}"
    return make_api_call(url)

def get_puuid(summoner_id):
    if summoner_id in puuid_cache:
        return puuid_cache[summoner_id]
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
    data = make_api_call(url)
    puuid = data.get("puuid") if data else None
    puuid_cache[summoner_id] = puuid
    return puuid

def get_matches(puuid, count=10):
    url = f"https://{REGIONAL_ENDPOINT}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count={count}"
    return make_api_call(url) or []

def save_match(match_id, tier, division):
    # Create folder structure: matches/<tier>/<division>
    folder_path = os.path.join(MATCHES_DIR, tier.lower(), division)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{match_id}.json")
    
    if os.path.exists(file_path):
        return False  # Match already saved
    
    url = f"https://{REGIONAL_ENDPOINT}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    data = make_api_call(url)
    if data:
        with open(file_path, "w") as f:
            json.dump(data, f)
        save_match_id_csv(match_id, tier, division)
        logging.info(f"Saved match {match_id} for {tier} {division}")
        return True
    return False

def save_match_id_csv(match_id, tier, division):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["match_id", "tier", "division"])  # Header row
        writer.writerow([match_id, tier, division])

def collect_data(matches_per_tier=5):
    state = load_state()  # Load progress state

    for tier in TIERS:
        # For Diamond, process divisions in reverse order; otherwise, use normal order.
        divisions_to_process = list(reversed(DIVISIONS)) if tier == "DIAMOND" else DIVISIONS
        for division in divisions_to_process:
            logging.info(f"Processing {tier} {division}")
            collected = 0
            # Resume from last processed page (if available), otherwise start at page 1.
            page = state.get(tier, {}).get(division, 1)
            done = False

            while collected < matches_per_tier and not done:
                players = get_players(tier, division, page)
                if not players:
                    break  # No more players available

                for player in players:
                    if collected >= matches_per_tier:
                        done = True
                        break
                    puuid = get_puuid(player["summonerId"])
                    if not puuid:
                        continue
                    # Get a list of match IDs for the player (limit to 10, process only first 5)
                    matches = get_matches(puuid, count=10)
                    for match_id in matches[:5]:
                        if collected >= matches_per_tier:
                            done = True
                            break
                        if save_match(match_id, tier, division):
                            collected += 1
                            logging.info(f"Collected {collected}/{matches_per_tier} for {tier} {division}")
                # Save progress for this tier/division after processing each page.
                state.setdefault(tier, {})[division] = page
                save_state(state)
                page += 1
                time.sleep(0.5)  # Buffer between page requests

            # If we're processing Diamond and have just finished Diamond I, then stop entirely.
            if tier == "DIAMOND" and division == "I":
                logging.info("Finished processing Diamond I. Stopping further processing.")
                return
            
print(f"Input desired number of matches per tier: ")
x = int(input)
if __name__ == "__main__":
    collect_data(matches_per_tier=100)
