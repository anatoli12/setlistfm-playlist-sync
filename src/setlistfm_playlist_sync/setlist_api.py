"""Setlist.fm API client module."""
import os
import time
import logging
from typing import Dict, List, Optional, Any

import requests
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

# Environment variable validation
SETLIST_KEY = os.environ.get("SETLISTFM_API_KEY")
if not SETLIST_KEY:
    raise RuntimeError(
        "SETLISTFM_API_KEY environment variable is required. "
        "Get your API key from https://api.setlist.fm/docs/1.0/index.html"
    )

LANG = os.getenv("SETLISTFM_ACCEPT_LANGUAGE", "en")
HEADERS = {
    "Accept": "application/json",
    "x-api-key": SETLIST_KEY,
    "Accept-Language": LANG,
    "User-Agent": "setlistfm-playlist-sync/0.1.0"
}

BASE = "https://api.setlist.fm/rest/1.0"
RATE_LIMIT_DELAY = 1  # Base delay in seconds
MAX_RETRIES = 3  # Maximum number of retries per request

def make_request(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> requests.Response:
    """Make a request to the Setlist.fm API with rate limiting handling."""
    retry_after = RATE_LIMIT_DELAY
    attempts = 0
    
    while attempts < MAX_RETRIES:
        try:
            logger.debug(f"Making request to {url} (attempt {attempts + 1}/{MAX_RETRIES})")
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            
            if r.status_code == 429:  # Too Many Requests
                retry_after = int(r.headers.get('Retry-After', retry_after * 2))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                attempts += 1
                continue
                
            r.raise_for_status()
            time.sleep(RATE_LIMIT_DELAY)  # Always wait between requests
            logger.debug(f"Request successful: {r.status_code}")
            return r
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code != 429:
                raise  # Re-raise non-rate-limit errors immediately
            
            if attempts >= MAX_RETRIES - 1:
                logger.error(f"Max retries ({MAX_RETRIES}) exceeded.")
                raise RuntimeError(f"Failed to make request after {MAX_RETRIES} retries: {e}")
            attempts += 1
            
    raise RuntimeError("Failed to make request after max retries")

def search_artist(artist_name: str) -> Dict[str, str]:
    """Search for an artist and return their details."""
    logger.info(f"Searching for artist: {artist_name}")
    r = make_request(
        f"{BASE}/search/artists",
        params={"artistName": artist_name, "p": 1}
    )
    
    data = r.json()
    logger.debug(f"API returned {len(data.get('artist', []))} artists")
    
    if data.get("artist"):
        # Try to find exact match first (case insensitive)
        for artist in data["artist"]:
            if artist["name"].lower() == artist_name.lower():
                logger.info(f"Found exact match: {artist['name']}")
                return {"name": artist["name"], "mbid": artist["mbid"]}
        
        # Look for best match without featuring artists or tribute bands
        for artist in data["artist"]:
            if ("feat." not in artist["name"].lower() and 
                "tribute" not in artist.get("disambiguation", "").lower()):
                logger.info(f"Selected closest match: {artist['name']}")
                return {"name": artist["name"], "mbid": artist["mbid"]}
        
        # Fallback to first result if no clean match
        artist = data["artist"][0]
        logger.warning(f"Using fallback match: {artist['name']}")
        return {"name": artist["name"], "mbid": artist["mbid"]}
            
    raise ValueError(f"Artist not found: {artist_name}")

def fetch_setlists_for_year(mbid: str, year: int, max_pages: int = 50) -> List[str]:
    """
    Fetch all setlists for an artist in a given year.
    
    Args:
        mbid: MusicBrainz ID of the artist
        year: Year to fetch setlists for
        max_pages: Maximum number of pages to fetch (default: 50)
    
    Returns:
        List of song names from all setlists in the given year
    """
    songs = []
    target_year = str(year)
    logger.info(f"Fetching setlists for year {year} (MBID: {mbid})")
    
    for page_num in range(1, max_pages + 1):
        logger.debug(f"Fetching page {page_num}")
        r = make_request(
            f"{BASE}/artist/{mbid}/setlists",
            params={"p": page_num},
            timeout=30
        )
        
        if r.status_code == 404:
            logger.debug("No more pages available (404)")
            break
            
        data = r.json()
        setlists = data.get("setlist", [])
        if not setlists:
            logger.debug("No setlists in response")
            break

        older_than_year = False
        page_song_count = 0
        
        for setlist in setlists:
            # Parse date (format: dd-MM-yyyy)
            event_date = setlist.get("eventDate", "")
            if len(event_date) >= 10:
                setlist_year = event_date[-4:]
                if setlist_year == target_year:
                    # Extract songs from this setlist
                    setlist_songs = _extract_songs_from_setlist(setlist)
                    songs.extend(setlist_songs)
                    page_song_count += len(setlist_songs)
                elif setlist_year.isdigit() and int(setlist_year) < year:
                    older_than_year = True
        
        logger.debug(f"Page {page_num}: Found {page_song_count} songs")
        
        if older_than_year:
            logger.debug("Reached setlists older than target year, stopping")
            break
            
        # Check pagination
        total = data.get("total", 0)
        items_per_page = data.get("itemsPerPage", 20)
        if page_num * items_per_page >= total:
            logger.debug("Reached end of results")
            break
    
    logger.info(f"Found {len(songs)} total songs from {year}")
    return songs


def _extract_songs_from_setlist(setlist: Dict[str, Any]) -> List[str]:
    """Extract song names from a single setlist."""
    songs = []
    sets_data = setlist.get("sets", {})
    
    # Handle both single set and multiple sets
    sets = sets_data.get("set", [])
    if not isinstance(sets, list):
        sets = [sets] if sets else []
    
    for set_data in sets:
        if not set_data:
            continue
            
        set_songs = set_data.get("song", [])
        for song in set_songs:
            name = song.get("name")
            if name and not song.get("tape"):  # Exclude tape/intro segments
                songs.append(name)
    
    return songs
