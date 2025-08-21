"""Tests for ytmusic_api module."""
import pytest
import json
from unittest.mock import Mock, patch, mock_open
from ytmusicapi import YTMusic

from setlistfm_playlist_sync import ytmusic_api


class TestYTMusicAPI:
    """Test cases for ytmusic_api module functions."""

    def test_build_queries(self):
        """Test building search queries from artist and titles."""
        artist = "Test Artist"
        titles = ["Song 1", "Song 2", "Song 3"]
        
        result = ytmusic_api.build_queries(artist, titles)
        
        expected = ["Test Artist - Song 1", "Test Artist - Song 2", "Test Artist - Song 3"]
        assert result == expected

    def test_build_queries_empty_titles(self):
        """Test building queries with empty titles list."""
        result = ytmusic_api.build_queries("Test Artist", [])
        assert result == []

    @patch('setlistfm_playlist_sync.ytmusic_api._find_or_create_playlist')
    @patch('setlistfm_playlist_sync.ytmusic_api._search_for_videos')
    def test_create_or_update_ytmusic_playlist_success(self, mock_search, mock_find_create):
        """Test successful playlist creation/update."""
        mock_ytmusic = Mock()
        mock_find_create.return_value = "test-playlist-id"
        mock_search.return_value = ["video-id-1", "video-id-2"]
        
        playlist_id, video_ids = ytmusic_api.create_or_update_ytmusic_playlist(
            mock_ytmusic, "Test Playlist", "Test Description", ["query1", "query2"]
        )
        
        assert playlist_id == "test-playlist-id"
        assert video_ids == ["video-id-1", "video-id-2"]
        mock_ytmusic.add_playlist_items.assert_called_once_with(
            "test-playlist-id", ["video-id-1", "video-id-2"], duplicates=True
        )

    @patch('setlistfm_playlist_sync.ytmusic_api._find_or_create_playlist')
    @patch('setlistfm_playlist_sync.ytmusic_api._search_for_videos')
    def test_create_or_update_ytmusic_playlist_no_videos(self, mock_search, mock_find_create):
        """Test playlist creation when no videos are found."""
        mock_ytmusic = Mock()
        mock_find_create.return_value = "test-playlist-id"
        mock_search.return_value = []
        
        playlist_id, video_ids = ytmusic_api.create_or_update_ytmusic_playlist(
            mock_ytmusic, "Test Playlist", "Test Description", ["query1", "query2"]
        )
        
        assert playlist_id == "test-playlist-id"
        assert video_ids == []
        mock_ytmusic.add_playlist_items.assert_not_called()

    def test_find_or_create_playlist_existing(self):
        """Test finding an existing playlist."""
        mock_ytmusic = Mock()
        existing_playlists = [
            {"title": "Other Playlist", "playlistId": "other-id"},
            {"title": "Test Playlist", "playlistId": "existing-id"}
        ]
        mock_ytmusic.get_library_playlists.return_value = existing_playlists
        
        result = ytmusic_api._find_or_create_playlist(mock_ytmusic, "Test Playlist", "Description")
        
        assert result == "existing-id"
        mock_ytmusic.create_playlist.assert_not_called()

    def test_find_or_create_playlist_create_new(self):
        """Test creating a new playlist when none exists."""
        mock_ytmusic = Mock()
        mock_ytmusic.get_library_playlists.return_value = []
        mock_ytmusic.create_playlist.return_value = "new-playlist-id"
        
        result = ytmusic_api._find_or_create_playlist(mock_ytmusic, "New Playlist", "Description")
        
        assert result == "new-playlist-id"
        mock_ytmusic.create_playlist.assert_called_once_with(
            title="New Playlist",
            description="Description",
            privacy_status="PRIVATE"
        )

    def test_find_or_create_playlist_case_insensitive(self):
        """Test that playlist search is case insensitive."""
        mock_ytmusic = Mock()
        existing_playlists = [
            {"title": "test playlist", "playlistId": "existing-id"}
        ]
        mock_ytmusic.get_library_playlists.return_value = existing_playlists
        
        result = ytmusic_api._find_or_create_playlist(mock_ytmusic, "TEST PLAYLIST", "Description")
        
        assert result == "existing-id"

    @patch('setlistfm_playlist_sync.ytmusic_api.time.sleep')
    def test_search_for_videos_success(self, mock_sleep):
        """Test successful video searching."""
        mock_ytmusic = Mock()
        
        # Mock search results - different results for each query
        mock_ytmusic.search.side_effect = [
            [{"videoId": "video-1"}],  # First query result
            [{"videoId": "video-2"}]   # Second query result
        ]
        
        queries = ["Query 1", "Query 2"]
        result = ytmusic_api._search_for_videos(mock_ytmusic, queries)
        
        assert result == ["video-1", "video-2"]
        assert mock_ytmusic.search.call_count == 2
        mock_sleep.assert_called()

    @patch('setlistfm_playlist_sync.ytmusic_api.time.sleep')
    def test_search_for_videos_fallback_to_videos(self, mock_sleep):
        """Test fallback from songs to videos filter."""
        mock_ytmusic = Mock()
        
        # First call (songs filter) returns empty, second call (videos filter) returns results
        mock_ytmusic.search.side_effect = [[], [{"videoId": "video-1"}]]
        
        result = ytmusic_api._search_for_videos(mock_ytmusic, ["Query 1"])
        
        assert result == ["video-1"]
        # Should be called twice: once with songs filter, once with videos filter
        assert mock_ytmusic.search.call_count == 2

    @patch('setlistfm_playlist_sync.ytmusic_api.time.sleep')
    def test_search_for_videos_no_results(self, mock_sleep):
        """Test video searching when no results are found."""
        mock_ytmusic = Mock()
        mock_ytmusic.search.return_value = []
        
        result = ytmusic_api._search_for_videos(mock_ytmusic, ["Unknown Query"])
        
        assert result == []

    @patch('setlistfm_playlist_sync.ytmusic_api.time.sleep')
    def test_search_for_videos_exception_handling(self, mock_sleep):
        """Test exception handling during video search."""
        mock_ytmusic = Mock()
        mock_ytmusic.search.side_effect = Exception("API Error")
        
        result = ytmusic_api._search_for_videos(mock_ytmusic, ["Query 1"])
        
        assert result == []

    @patch.dict('os.environ', {
        'YTM_CLIENT_ID': 'test-client-id',
        'YTM_CLIENT_SECRET': 'test-client-secret'
    })
    @patch('os.path.exists')
    @patch('setlistfm_playlist_sync.ytmusic_api.YTMusic')
    def test_init_ytmusic_success(self, mock_ytmusic_class, mock_exists):
        """Test successful YTMusic initialization."""
        mock_exists.return_value = True
        mock_ytmusic_instance = Mock()
        mock_ytmusic_class.return_value = mock_ytmusic_instance
        
        result = ytmusic_api.init_ytmusic()
        
        assert result == mock_ytmusic_instance
        mock_ytmusic_class.assert_called_once()

    def test_init_ytmusic_missing_client_id(self):
        """Test YTMusic initialization with missing client ID."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(RuntimeError, match="YouTube Music OAuth credentials missing"):
                ytmusic_api.init_ytmusic()

    @patch.dict('os.environ', {
        'YTM_CLIENT_ID': 'test-client-id',
        'YTM_CLIENT_SECRET': 'test-client-secret'
    })
    @patch('os.path.exists')
    def test_init_ytmusic_missing_oauth_file(self, mock_exists):
        """Test YTMusic initialization with missing OAuth file."""
        mock_exists.return_value = False
        
        with pytest.raises(RuntimeError, match="OAuth file not found"):
            ytmusic_api.init_ytmusic()

    @patch.dict('os.environ', {
        'YTM_CLIENT_ID': 'test-client-id',
        'YTM_CLIENT_SECRET': 'test-client-secret'
    })
    @patch('os.path.exists')
    @patch('setlistfm_playlist_sync.ytmusic_api.YTMusic')
    def test_init_ytmusic_initialization_error(self, mock_ytmusic_class, mock_exists):
        """Test YTMusic initialization error handling."""
        mock_exists.return_value = True
        mock_ytmusic_class.side_effect = Exception("OAuth Error")
        
        with pytest.raises(RuntimeError, match="YouTube Music initialization failed"):
            ytmusic_api.init_ytmusic()

    def test_search_for_videos_no_video_id(self):
        """Test handling search results without video ID."""
        mock_ytmusic = Mock()
        
        # Mock search result without videoId
        search_results = [{"title": "Some Song"}]
        mock_ytmusic.search.return_value = search_results
        
        with patch('setlistfm_playlist_sync.ytmusic_api.time.sleep'):
            result = ytmusic_api._search_for_videos(mock_ytmusic, ["Query 1"])
        
        assert result == []
