"""Command line interface for setlistfm-playlist-sync."""
import argparse
import logging
import sys

from . import setlist_api
from . import ytmusic_api  
from . import utils

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def run(artist_name: str, year: int, num_tracks: int = 20) -> None:
    """Create a YouTube Music playlist from Setlist.fm data.
    
    Args:
        artist_name: Name of the artist to search for
        year: Year to fetch setlists from
        num_tracks: Number of top tracks to include (default: 20)
    """
    logger.info(f"Starting playlist creation for {artist_name} in {year}")
    
    try:
        # Find the artist
        print(f"🔍 Searching for artist: {artist_name}")
        artist = setlist_api.search_artist(artist_name)
        print(f"✅ Found: {artist['name']}")
        
        # Get setlist data
        print(f"📋 Fetching setlists for {year}...")
        songs = setlist_api.fetch_setlists_for_year(artist["mbid"], year)
        if not songs:
            raise ValueError(f"No songs found for {artist_name} in {year}")
        
        print(f"📊 Found {len(songs)} total song performances")
        
        # Process the songs
        top_tracks = utils.top_songs(songs, n=num_tracks)
        print(f"🎵 Calculated top {len(top_tracks)} most-played songs")

        # Initialize YouTube Music
        print("🎬 Connecting to YouTube Music...")
        ytm = ytmusic_api.init_ytmusic()
        
        # Create playlist
        title = f"{artist['name']} – Top {len(top_tracks)} Live ({year}, setlist.fm)"
        description = (
            f"Auto-generated from setlist.fm data for {artist['name']} in {year}. "
            f"Based on {len(songs)} song performances from live shows."
        )
        
        queries = ytmusic_api.build_queries(artist['name'], top_tracks)
        print(f"🎧 Creating playlist: {title}")
        
        playlist_id, video_ids = ytmusic_api.create_or_update_ytmusic_playlist(
            ytm, title, description, queries
        )
        
        # Print results
        print(f"\n✅ Success! Playlist created with {len(video_ids)} tracks")
        print(f"🔗 URL: https://music.youtube.com/playlist?list={playlist_id}")
        print("\n🎵 Tracks added:")
        for i, query in enumerate(queries[:len(video_ids)], 1):
            print(f"  {i:2d}. {query}")
            
        if len(video_ids) < len(queries):
            missing = len(queries) - len(video_ids)
            print(f"\n⚠️  {missing} tracks could not be found on YouTube Music")
        
    except Exception as e:
        logger.error(f"Failed to create playlist: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

def main() -> None:
    """Entry point for the command line interface."""
    parser = argparse.ArgumentParser(
        description="Create YouTube Music playlists from Setlist.fm data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --artist "Megadeth" --year 2024
  %(prog)s --artist "Iron Maiden" --year 2023 --tracks 15 --verbose
  
For more information, visit: https://github.com/anatoli12/setlistfm-playlist-sync
        """
    )
    
    parser.add_argument(
        "--artist", 
        required=True, 
        help="Artist name to search for (e.g., 'Megadeth')"
    )
    parser.add_argument(
        "--year", 
        type=int, 
        required=True, 
        help="Year to fetch setlists from (e.g., 2024)"
    )
    parser.add_argument(
        "--tracks", 
        type=int, 
        default=20, 
        help="Number of top tracks to include (default: 20)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.tracks < 1:
        parser.error("Number of tracks must be at least 1")
    if args.tracks > 100:
        parser.error("Number of tracks cannot exceed 100")
    if args.year < 1950 or args.year > 2030:
        parser.error("Year must be between 1950 and 2030")
    
    setup_logging(args.verbose)
    
    try:
        run(args.artist, args.year, args.tracks)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            raise
        sys.exit(1)
