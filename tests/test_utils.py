"""Tests for utils module."""
import pytest
from collections import Counter

from setlistfm_playlist_sync import utils


class TestUtils:
    """Test cases for utils module functions."""

    def test_top_songs_basic_functionality(self):
        """Test basic top songs calculation."""
        songs = ["Song A", "Song B", "Song A", "Song C", "Song A", "Song B"]
        
        result = utils.top_songs(songs)
        
        # Should return top song names only, sorted by frequency then alphabetically
        expected = ["Song A", "Song B", "Song C"]  # Song A(3), Song B(2), Song C(1)
        assert result == expected

    def test_top_songs_with_limit(self):
        """Test top songs with n parameter."""
        songs = ["Song A", "Song B", "Song A", "Song C", "Song A", "Song B"]
        
        result = utils.top_songs(songs, n=2)
        
        assert len(result) == 2
        assert result == ["Song A", "Song B"]

    def test_top_songs_empty_list(self):
        """Test top songs with empty song list."""
        result = utils.top_songs([])
        assert result == []

    def test_top_songs_single_song(self):
        """Test top songs with single song."""
        result = utils.top_songs(["Single Song"])
        assert result == ["Single Song"]

    def test_top_songs_all_unique_alphabetical_tiebreaker(self):
        """Test top songs where all songs appear once (alphabetical tiebreaker)."""
        songs = ["Song C", "Song A", "Song B", "Song D"]
        
        result = utils.top_songs(songs)
        
        # All have count of 1, so should be sorted alphabetically
        assert result == ["Song A", "Song B", "Song C", "Song D"]

    def test_top_songs_n_larger_than_unique_songs(self):
        """Test top songs when n is larger than number of unique songs."""
        songs = ["Song A", "Song A", "Song B"]
        
        result = utils.top_songs(songs, n=10)
        
        assert len(result) == 2  # Only 2 unique songs
        assert result == ["Song A", "Song B"]

    def test_top_songs_zero_n(self):
        """Test top songs with zero n."""
        songs = ["Song A", "Song B", "Song C"]
        
        result = utils.top_songs(songs, n=0)
        
        assert result == []

    def test_top_songs_case_sensitivity_with_alphabetical_sort(self):
        """Test that top songs handles case sensitivity with alphabetical sorting."""
        songs = ["song b", "Song A", "song b"]  # song b appears twice, Song A once
        
        result = utils.top_songs(songs)
        
        # song b (2 times) should come first, then Song A (1 time)
        assert result == ["song b", "Song A"]

    def test_top_songs_alphabetical_tiebreaker(self):
        """Test alphabetical tiebreaker for same frequency."""
        songs = ["Zebra", "Apple", "Banana", "Apple", "Zebra", "Banana"]
        
        result = utils.top_songs(songs)
        
        # All appear twice, should be sorted alphabetically
        assert result == ["Apple", "Banana", "Zebra"]

    def test_top_songs_mixed_frequencies_alphabetical_tiebreaker(self):
        """Test mixed frequencies with alphabetical tiebreaker."""
        songs = ["C", "A", "B", "A", "C", "C"]  # C(3), A(2), B(1)
        
        result = utils.top_songs(songs)
        
        # Should be sorted by frequency desc, then alphabetically
        assert result == ["C", "A", "B"]

    def test_top_songs_performance_with_large_list(self):
        """Test top songs performance with large list."""
        # Create a large list of songs
        songs = [f"Song {i % 100:02d}" for i in range(10000)]  # 100 unique songs, 10k total
        
        result = utils.top_songs(songs, n=10)
        
        assert len(result) == 10
        # Should be the first 10 alphabetically since all have same count
        expected = [f"Song {i:02d}" for i in range(10)]
        assert result == expected

    def test_top_songs_case_insensitive_alphabetical_sort(self):
        """Test that alphabetical sorting is case insensitive."""
        songs = ["apple", "Banana", "cherry", "apple"]  # apple appears twice
        
        result = utils.top_songs(songs, n=3)
        
        # apple (2) first, then Banana and cherry (1 each) sorted case-insensitively
        assert result == ["apple", "Banana", "cherry"]

    @pytest.mark.parametrize("n", [1, 5, 10, 20])
    def test_top_songs_various_n_values(self, n):
        """Test top songs with various n values."""
        songs = [f"Song {i:02d}" for i in range(50)]  # 50 unique songs
        
        result = utils.top_songs(songs, n=n)
        
        expected_length = min(n, 50)
        assert len(result) == expected_length
        # Should be first n songs alphabetically
        expected = [f"Song {i:02d}" for i in range(expected_length)]
        assert result == expected

    def test_top_songs_default_n_value(self):
        """Test that default n value is 20."""
        songs = [f"Song {i:02d}" for i in range(30)]  # 30 unique songs
        
        result = utils.top_songs(songs)  # No n specified, should default to 20
        
        assert len(result) == 20
