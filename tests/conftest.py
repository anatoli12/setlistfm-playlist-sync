"""Common test fixtures and configuration."""
import os
import tempfile
from unittest.mock import Mock, MagicMock
import pytest
import json


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("SETLISTFM_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("YTMUSIC_OAUTH", "/tmp/test_oauth.json")


@pytest.fixture
def sample_setlist():
    """Sample setlist data structure for testing song extraction."""
    return {
        "sets": {
            "set": [{
                "song": [
                    {"name": "Song 1"},
                    {"name": "Song 2"}
                ]
            }]
        }
    }


@pytest.fixture
def sample_setlist_response():
    """Sample Setlist.fm API response."""
    return {
        "type": "setlists",
        "itemsPerPage": 20,
        "page": 1,
        "total": 1,
        "setlist": [
            {
                "id": "test-id-1",
                "versionId": "test-version-1",
                "eventDate": "15-10-2023",
                "artist": {
                    "mbid": "test-mbid",
                    "name": "Test Artist",
                    "sortName": "Artist, Test"
                },
                "venue": {
                    "id": "test-venue-id",
                    "name": "Test Venue",
                    "city": {
                        "id": "test-city-id",
                        "name": "Test City",
                        "state": "Test State",
                        "country": {"code": "US", "name": "United States"}
                    }
                },
                "sets": {
                    "set": [
                        {
                            "song": [
                                {
                                    "name": "Test Song 1",
                                    "with": {},
                                    "cover": {},
                                    "info": ""
                                },
                                {
                                    "name": "Test Song 2",
                                    "with": {},
                                    "cover": {},
                                    "info": ""
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture
def sample_artist_search_response():
    """Sample artist search response from Setlist.fm."""
    return {
        "type": "artists",
        "itemsPerPage": 30,
        "page": 1,
        "total": 1,
        "artist": [
            {
                "mbid": "test-mbid-12345",
                "name": "Test Artist",
                "sortName": "Artist, Test",
                "disambiguation": "",
                "url": "https://www.setlist.fm/setlists/test-artist-123.html"
            }
        ]
    }


@pytest.fixture
def sample_ytmusic_search_results():
    """Sample YouTube Music search results."""
    return [
        {
            "videoId": "test-video-id-1",
            "title": "Test Song 1",
            "artists": [{"name": "Test Artist", "id": "test-artist-id"}],
            "album": {"name": "Test Album", "id": "test-album-id"},
            "duration": "3:45",
            "thumbnails": []
        },
        {
            "videoId": "test-video-id-2", 
            "title": "Test Song 2",
            "artists": [{"name": "Test Artist", "id": "test-artist-id"}],
            "album": {"name": "Test Album", "id": "test-album-id"},
            "duration": "4:12",
            "thumbnails": []
        }
    ]


@pytest.fixture
def mock_ytmusic_oauth_file(tmp_path):
    """Create a mock OAuth file for YouTube Music."""
    oauth_data = {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret", 
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    
    oauth_file = tmp_path / "oauth.json"
    oauth_file.write_text(json.dumps(oauth_data))
    return str(oauth_file)


@pytest.fixture
def mock_ytmusic_api():
    """Mock YTMusic API instance."""
    mock_api = Mock()
    mock_api.search.return_value = []
    mock_api.create_playlist.return_value = "test-playlist-id"
    mock_api.add_playlist_items.return_value = {}
    mock_api.edit_playlist.return_value = {}
    return mock_api


@pytest.fixture
def sample_songs_with_counts():
    """Sample song frequency data."""
    return [
        ("Test Song 1", 5),
        ("Test Song 2", 3),
        ("Test Song 3", 2),
        ("Test Song 4", 1),
        ("Test Song 5", 1)
    ]
