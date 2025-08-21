"""Tests for setlist_api module."""
import pytest
import requests
from unittest.mock import Mock, patch
from requests.exceptions import RequestException

from setlistfm_playlist_sync import setlist_api


class TestSetlistAPI:
    """Test cases for setlist_api module functions."""

    @patch('setlistfm_playlist_sync.setlist_api.time.sleep')
    def test_make_request_success(self, mock_sleep):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        
        with patch('setlistfm_playlist_sync.setlist_api.requests.get', return_value=mock_response):
            result = setlist_api.make_request("https://test.url")
            
        assert result.json() == {"test": "data"}
        assert result.status_code == 200

    @patch('setlistfm_playlist_sync.setlist_api.time.sleep')
    def test_make_request_rate_limit_retry(self, mock_sleep):
        """Test rate limit handling with retry."""
        # First response: rate limited
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '2'}
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=rate_limit_response)
        
        # Second response: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"test": "data"}
        success_response.raise_for_status.return_value = None
        
        with patch('setlistfm_playlist_sync.setlist_api.requests.get', side_effect=[rate_limit_response, success_response]):
            result = setlist_api.make_request("https://test.url")
            
        assert result.json() == {"test": "data"}
        mock_sleep.assert_called()

    @patch('setlistfm_playlist_sync.setlist_api.time.sleep')
    def test_make_request_max_retries_exceeded(self, mock_sleep):
        """Test max retries exceeded."""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        rate_limit_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=rate_limit_response)
        
        with patch('setlistfm_playlist_sync.setlist_api.requests.get', return_value=rate_limit_response):
            with pytest.raises(RuntimeError, match="Failed to make request after .* retries"):
                setlist_api.make_request("https://test.url")

    @patch('setlistfm_playlist_sync.setlist_api.time.sleep')
    def test_make_request_non_rate_limit_error(self, mock_sleep):
        """Test non-rate-limit error propagation."""
        # Create a mock HTTP error that is NOT a 429
        http_error = requests.exceptions.HTTPError("Not Found")
        http_error.response = Mock()
        http_error.response.status_code = 404
        
        with patch('setlistfm_playlist_sync.setlist_api.requests.get') as mock_get:
            mock_get.side_effect = http_error
            
            with pytest.raises(requests.exceptions.HTTPError):
                setlist_api.make_request("https://test.url")
        
        # Should not retry non-rate-limit errors, so no sleep should be called
        mock_sleep.assert_not_called()

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_search_artist_exact_match(self, mock_request):
        """Test artist search with exact match."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artist": [
                {"name": "The Beatles", "mbid": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"},
                {"name": "Beatles Tribute", "mbid": "other-id"}
            ]
        }
        mock_request.return_value = mock_response
        
        result = setlist_api.search_artist("The Beatles")
        
        assert result["name"] == "The Beatles"
        assert result["mbid"] == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_search_artist_no_exact_match(self, mock_request):
        """Test artist search without exact match."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artist": [
                {"name": "Beatles Tribute", "mbid": "tribute-id", "disambiguation": "tribute band"},
                {"name": "The Beatles Cover Band", "mbid": "cover-id"}
            ]
        }
        mock_request.return_value = mock_response
        
        result = setlist_api.search_artist("The Beatles")
        
        # Should pick the cover band since tribute has "tribute" in disambiguation
        assert result["name"] == "The Beatles Cover Band"
        assert result["mbid"] == "cover-id"

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_search_artist_fallback_to_first(self, mock_request):
        """Test artist search fallback to first result."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "artist": [
                {"name": "Beatles feat. Someone", "mbid": "feat-id"}
            ]
        }
        mock_request.return_value = mock_response
        
        result = setlist_api.search_artist("The Beatles")
        
        # Should use fallback to first result
        assert result["name"] == "Beatles feat. Someone"
        assert result["mbid"] == "feat-id"

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_search_artist_not_found(self, mock_request):
        """Test artist search with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {"artist": []}
        mock_request.return_value = mock_response
        
        with pytest.raises(ValueError, match="Artist not found"):
            setlist_api.search_artist("Unknown Artist")

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_fetch_setlists_for_year(self, mock_request, sample_setlist):
        """Test fetching setlists for a year."""
        # Add eventDate to sample setlist for 2023
        sample_setlist_with_date = {**sample_setlist, "eventDate": "15-10-2023"}
        
        # Mock first page response
        first_page = Mock()
        first_page.status_code = 200
        first_page.json.return_value = {
            "setlist": [sample_setlist_with_date],
            "page": 1,
            "total": 1,
            "itemsPerPage": 20
        }
        
        mock_request.return_value = first_page
        
        result = setlist_api.fetch_setlists_for_year("test-mbid", 2023)
        
        assert len(result) == 2  # Two songs from the sample setlist
        assert "Song 1" in result
        assert "Song 2" in result

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_fetch_setlists_for_year_multiple_pages(self, mock_request, sample_setlist):
        """Test fetching setlists across multiple pages."""
        # Add eventDate to sample setlist for 2023
        sample_setlist_with_date = {**sample_setlist, "eventDate": "15-10-2023"}
        
        # Mock multiple page responses
        first_page = Mock()
        first_page.status_code = 200
        first_page.json.return_value = {
            "setlist": [sample_setlist_with_date],
            "page": 1,
            "total": 40,  # Total items requiring 2 pages (20 items per page)
            "itemsPerPage": 20
        }
        
        second_page = Mock()
        second_page.status_code = 200
        second_page.json.return_value = {
            "setlist": [sample_setlist_with_date],
            "page": 2,
            "total": 40,
            "itemsPerPage": 20
        }
        
        mock_request.side_effect = [first_page, second_page]
        
        result = setlist_api.fetch_setlists_for_year("test-mbid", 2023)
        
        assert len(result) == 4  # Two songs from each of two setlists
        assert result.count("Song 1") == 2
        assert result.count("Song 2") == 2

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_fetch_setlists_for_year_no_results(self, mock_request):
        """Test fetching setlists with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "setlist": [],
            "page": 1,
            "total": 0
        }
        mock_request.return_value = mock_response
        
        result = setlist_api.fetch_setlists_for_year("test-mbid", 2023)
        
        assert result == []

    @patch('setlistfm_playlist_sync.setlist_api.make_request')
    def test_fetch_setlists_for_year_request_exception(self, mock_request):
        """Test request exception during setlist fetching."""
        mock_request.side_effect = RequestException("API Error")
        
        with pytest.raises(RequestException):
            setlist_api.fetch_setlists_for_year("test-mbid", 2023)

    def test_extract_songs_from_setlist(self, sample_setlist):
        """Test song extraction from setlist data."""
        result = setlist_api._extract_songs_from_setlist(sample_setlist)
        
        assert len(result) == 2
        assert "Song 1" in result
        assert "Song 2" in result

    def test_extract_songs_from_setlist_with_covers(self):
        """Test song extraction handles cover songs."""
        setlist_with_covers = {
            "sets": {
                "set": [{
                    "song": [
                        {"name": "Original Song"},
                        {"name": "Cover Song", "cover": {"name": "Original Artist"}}
                    ]
                }]
            }
        }
        
        result = setlist_api._extract_songs_from_setlist(setlist_with_covers)
        
        assert len(result) == 2
        assert "Original Song" in result
        assert "Cover Song" in result

    def test_extract_songs_from_setlist_empty(self):
        """Test song extraction from empty setlist."""
        empty_setlist = {"sets": {"set": []}}
        
        result = setlist_api._extract_songs_from_setlist(empty_setlist)
        
        assert result == []

    def test_extract_songs_from_setlist_no_sets(self):
        """Test song extraction from setlist with no sets."""
        no_sets_setlist = {"sets": {}}
        
        result = setlist_api._extract_songs_from_setlist(no_sets_setlist)
        
        assert result == []

    def test_extract_songs_from_setlist_missing_sets_key(self):
        """Test song extraction from setlist missing sets key."""
        no_sets_key = {}
        
        result = setlist_api._extract_songs_from_setlist(no_sets_key)
        
        assert result == []
