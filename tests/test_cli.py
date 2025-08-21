"""Tests for cli module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from setlistfm_playlist_sync import cli


class TestCLI:
    """Test cases for cli module functions."""

    @patch('setlistfm_playlist_sync.cli.setlist_api')
    @patch('setlistfm_playlist_sync.cli.ytmusic_api')
    @patch('setlistfm_playlist_sync.cli.utils')
    @patch('builtins.print')  # Mock print to avoid output during tests
    def test_run_success(self, mock_print, mock_utils, mock_ytmusic_api, mock_setlist_api):
        """Test successful run of the main workflow."""
        # Mock setlist_api functions
        mock_setlist_api.search_artist.return_value = {"name": "Test Artist", "mbid": "test-mbid"}
        mock_setlist_api.fetch_setlists_for_year.return_value = ["Song 1", "Song 2", "Song 1"]
        
        # Mock utils functions  
        mock_utils.top_songs.return_value = ["Song 1", "Song 2"]
        
        # Mock ytmusic_api functions
        mock_ytmusic = Mock()
        mock_ytmusic_api.init_ytmusic.return_value = mock_ytmusic
        mock_ytmusic_api.build_queries.return_value = ["Test Artist - Song 1", "Test Artist - Song 2"]
        mock_ytmusic_api.create_or_update_ytmusic_playlist.return_value = ("playlist-id", ["video-1", "video-2"])
        
        # Run the function (should not raise exception)
        cli.run("Test Artist", 2023, 10)
        
        # Verify the workflow
        mock_setlist_api.search_artist.assert_called_once_with("Test Artist")
        mock_setlist_api.fetch_setlists_for_year.assert_called_once_with("test-mbid", 2023)
        mock_utils.top_songs.assert_called_once_with(["Song 1", "Song 2", "Song 1"], n=10)
        mock_ytmusic_api.create_or_update_ytmusic_playlist.assert_called_once()

    @patch('setlistfm_playlist_sync.cli.setlist_api')
    @patch('sys.exit')
    def test_run_artist_not_found(self, mock_exit, mock_setlist_api):
        """Test run when artist is not found."""
        mock_setlist_api.search_artist.side_effect = ValueError("Artist not found: Unknown Artist")
        
        with patch('builtins.print'):
            cli.run("Unknown Artist", 2023, 10)
            
        mock_exit.assert_called_once_with(1)

    @patch('setlistfm_playlist_sync.cli.setlist_api')
    @patch('sys.exit')
    @patch('builtins.print')
    def test_run_no_setlists_found(self, mock_print, mock_exit, mock_setlist_api):
        """Test run when no setlists are found."""
        # Mock setlist_api functions
        mock_setlist_api.search_artist.return_value = {"name": "Test Artist", "mbid": "test-mbid"}
        mock_setlist_api.fetch_setlists_for_year.return_value = []  # No setlists
        
        cli.run("Test Artist", 2023, 10)
        
        # Should exit with error when no songs found
        mock_exit.assert_called_once_with(1)

    @patch('setlistfm_playlist_sync.cli.setlist_api')
    @patch('setlistfm_playlist_sync.cli.ytmusic_api')
    @patch('sys.exit')
    @patch('builtins.print')
    def test_run_ytmusic_initialization_error(self, mock_print, mock_exit, mock_ytmusic_api, mock_setlist_api):
        """Test run when YouTube Music initialization fails."""
        mock_setlist_api.search_artist.return_value = {"name": "Test Artist", "mbid": "test-mbid"}
        mock_setlist_api.fetch_setlists_for_year.return_value = ["Song 1", "Song 2"]
        mock_ytmusic_api.init_ytmusic.side_effect = RuntimeError("YouTube Music initialization failed")
        
        with patch('setlistfm_playlist_sync.cli.utils'):
            cli.run("Test Artist", 2023, 10)
            
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023', '--tracks', '15'])
    @patch('setlistfm_playlist_sync.cli.run')
    def test_main_with_arguments(self, mock_run):
        """Test main function with command line arguments."""
        cli.main()
        
        mock_run.assert_called_once_with("Test Artist", 2023, 15)

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023'])
    @patch('setlistfm_playlist_sync.cli.run')
    def test_main_with_defaults(self, mock_run):
        """Test main function with default tracks value."""
        cli.main()
        
        # Should use default tracks (20)
        mock_run.assert_called_once_with("Test Artist", 2023, 20)

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023'])
    @patch('setlistfm_playlist_sync.cli.run')
    @patch('sys.exit')
    def test_main_error_handling(self, mock_exit, mock_run):
        """Test main function error handling."""
        mock_run.side_effect = ValueError("Artist not found")
        
        with patch('builtins.print'):
            cli.main()
            
        mock_exit.assert_called_once_with(1)

    @patch('sys.argv', ['cli.py'])
    def test_main_missing_artist_argument(self):
        """Test main function with missing artist argument."""
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            with pytest.raises(SystemExit):
                cli.main()
            # Should show help message about missing argument
            assert "required" in fake_stderr.getvalue().lower()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', 'invalid'])
    def test_main_invalid_year_argument(self):
        """Test main function with invalid year argument."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023', '--tracks', 'invalid'])
    def test_main_invalid_tracks_argument(self):
        """Test main function with invalid tracks argument."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--help'])
    def test_main_help_option(self):
        """Test main function with help option."""
        with patch('sys.stdout', new=StringIO()) as fake_stdout:
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            # Should exit successfully when showing help
            assert exc_info.value.code == 0
            # Should show help text
            help_text = fake_stdout.getvalue()
            assert "usage:" in help_text.lower()
            assert "artist" in help_text.lower()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023', '--tracks', '0'])
    def test_main_invalid_tracks_zero(self):
        """Test main function with zero tracks (should be rejected)."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023', '--tracks', '101'])
    def test_main_invalid_tracks_too_many(self):
        """Test main function with too many tracks (should be rejected)."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '1949'])
    def test_main_invalid_year_too_old(self):
        """Test main function with year too old (should be rejected)."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2031'])
    def test_main_invalid_year_too_new(self):
        """Test main function with year too new (should be rejected)."""
        with patch('sys.stderr', new=StringIO()):
            with pytest.raises(SystemExit):
                cli.main()

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023', '--verbose'])
    @patch('setlistfm_playlist_sync.cli.run')
    def test_main_verbose_flag(self, mock_run):
        """Test main function with verbose flag."""
        with patch('setlistfm_playlist_sync.cli.setup_logging') as mock_setup_logging:
            cli.main()
            
        mock_setup_logging.assert_called_once_with(True)
        mock_run.assert_called_once()

    def test_setup_logging_normal(self):
        """Test setup_logging with normal verbosity."""
        with patch('logging.basicConfig') as mock_basic_config:
            cli.setup_logging(verbose=False)
            
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs['level'] == 20  # logging.INFO

    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose flag."""
        with patch('logging.basicConfig') as mock_basic_config:
            cli.setup_logging(verbose=True)
            
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs['level'] == 10  # logging.DEBUG

    @patch('sys.argv', ['cli.py', '--artist', 'Test Artist', '--year', '2023'])
    @patch('setlistfm_playlist_sync.cli.run')
    @patch('sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_run):
        """Test main function handling keyboard interrupt."""
        mock_run.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print'):
            cli.main()
            
        mock_exit.assert_called_once_with(1)

    @patch('setlistfm_playlist_sync.cli.setlist_api')
    @patch('setlistfm_playlist_sync.cli.ytmusic_api')  
    @patch('setlistfm_playlist_sync.cli.utils')
    @patch('builtins.print')
    def test_run_playlist_title_format(self, mock_print, mock_utils, mock_ytmusic_api, mock_setlist_api):
        """Test that playlist title follows expected format."""
        # Mock all the dependencies
        mock_setlist_api.search_artist.return_value = {"name": "Test Artist", "mbid": "test-mbid"}
        mock_setlist_api.fetch_setlists_for_year.return_value = ["Song 1", "Song 2", "Song 3"]
        mock_utils.top_songs.return_value = ["Song 1", "Song 2"]
        
        mock_ytmusic = Mock()
        mock_ytmusic_api.init_ytmusic.return_value = mock_ytmusic
        mock_ytmusic_api.build_queries.return_value = ["Test Artist - Song 1", "Test Artist - Song 2"]
        mock_ytmusic_api.create_or_update_ytmusic_playlist.return_value = ("playlist-id", ["video-1", "video-2"])
        
        cli.run("Test Artist", 2022, 5)
        
        # Check that create_or_update_ytmusic_playlist was called with correct title format
        call_args = mock_ytmusic_api.create_or_update_ytmusic_playlist.call_args[0]
        title = call_args[1]  # Second argument is title
        assert "Test Artist" in title
        assert "2022" in title
        assert "setlist.fm" in title
