"""Utility functions for processing setlist data."""
import collections
from typing import List

def top_songs(songs: List[str], n: int = 20) -> List[str]:
    """Return the top n most frequently played songs."""
    counter = collections.Counter(songs)
    # tie-breaker: alphabetical after count
    return [t[0] for t in sorted(
        counter.items(),
        key=lambda kv: (-kv[1], kv[0].lower())
    )[:n]]
