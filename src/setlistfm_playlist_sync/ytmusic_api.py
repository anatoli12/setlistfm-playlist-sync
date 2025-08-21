"""YouTube Music API client module."""
import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple

from ytmusicapi import YTMusic, OAuthCredentials

logger = logging.getLogger(__name__)

def build_queries(artist: str, titles: List[str]) -> List[str]:
    """Build search queries for YouTube Music.
    
    Args:
        artist: Artist name
        titles: List of song titles
        
    Returns:
        List of formatted search queries
    """
    return [f"{artist} - {title}" for title in titles]

def create_or_update_ytmusic_playlist(
    ytm: YTMusic, title: str, description: str, queries: List[str]
) -> Tuple[str, List[str]]:
    """Create or update a YouTube Music playlist with the given tracks.
    
    Args:
        ytm: YouTube Music client
        title: Playlist title
        description: Playlist description
        queries: List of search queries for songs
        
    Returns:
        Tuple of (playlist_id, list of video_ids added)
    """
    logger.info(f"Creating/updating playlist: {title}")
    
    # Find existing playlist or create new one
    playlist_id = _find_or_create_playlist(ytm, title, description)
    
    # Search for videos and collect IDs
    video_ids = _search_for_videos(ytm, queries)
    
    # Add videos to playlist
    if video_ids:
        logger.info(f"Adding {len(video_ids)} tracks to playlist")
        ytm.add_playlist_items(playlist_id, video_ids, duplicates=True)
    else:
        logger.warning("No videos found to add to playlist")
    
    return playlist_id, video_ids


def _find_or_create_playlist(ytm: YTMusic, title: str, description: str) -> str:
    """Find existing playlist by title or create a new one."""
    try:
        playlists = ytm.get_library_playlists(limit=200)
        for playlist in playlists:
            if playlist["title"].lower() == title.lower():
                logger.info(f"Found existing playlist: {playlist['playlistId']}")
                return playlist["playlistId"]
    except Exception as e:
        logger.warning(f"Error searching for existing playlists: {e}")
    
    # Create new playlist
    logger.info("Creating new playlist")
    playlist_id = ytm.create_playlist(
        title=title, 
        description=description, 
        privacy_status="PRIVATE"
    )
    return str(playlist_id)


def _search_for_videos(ytm: YTMusic, queries: List[str]) -> List[str]:
    """Search for videos on YouTube Music for each query."""
    video_ids = []
    
    for i, query in enumerate(queries, 1):
        logger.debug(f"Searching for track {i}/{len(queries)}: {query}")
        
        try:
            # Try songs filter first
            results = ytm.search(query, filter="songs") or []
            if not results:
                # Fallback to videos if no songs found
                results = ytm.search(query, filter="videos") or []
            
            if results:
                video_id = results[0].get("videoId")
                if video_id:
                    video_ids.append(video_id)
                    logger.debug(f"Found video: {video_id}")
                else:
                    logger.warning(f"No video ID found for: {query}")
            else:
                logger.warning(f"No results found for: {query}")
                
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
        
        # Small delay to be respectful
        time.sleep(0.1)
    
    logger.info(f"Found {len(video_ids)} out of {len(queries)} tracks")
    return video_ids

def init_ytmusic() -> YTMusic:
    """Initialize YouTube Music API client with proper error handling."""
    try:
        # Required environment variables
        client_id = os.environ.get("YTM_CLIENT_ID")
        client_secret = os.environ.get("YTM_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise RuntimeError(
                "YouTube Music OAuth credentials missing. Please set:\n"
                "- YTM_CLIENT_ID\n"
                "- YTM_CLIENT_SECRET\n"
                "Follow the setup guide in the README."
            )
        
        # Find oauth.json file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        oauth_path = os.path.join(base_dir, "oauth.json")
        
        if not os.path.exists(oauth_path):
            raise FileNotFoundError(
                f"OAuth file not found at {oauth_path}. "
                "Please create oauth.json following the setup guide."
            )
        
        logger.info("Initializing YouTube Music client")
        return YTMusic(
            auth=oauth_path,
            oauth_credentials=OAuthCredentials(
                client_id=client_id, 
                client_secret=client_secret
            ),
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize YouTube Music client: {e}")
        raise RuntimeError(f"YouTube Music initialization failed: {e}") from e
