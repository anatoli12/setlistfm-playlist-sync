# AI Agent Instructions for setlistfm-playlist-sync

## Project Overview
This project creates YouTube Music playlists from an artist's most-played songs on Setlist.fm. It's organized into distinct modules handling different responsibilities:

```
src/setlistfm_playlist_sync/
├── setlist_api.py   # Setlist.fm API client with rate limiting
├── ytmusic_api.py   # YouTube Music API client & playlist management
├── utils.py         # Helper functions (e.g., song frequency analysis)
└── cli.py          # Command-line interface
```

## Key Architectural Patterns

### API Client Structure
- All API clients implement rate limiting and error handling
- `setlist_api.py` uses exponential backoff for rate limits (see `make_request()`)
- `ytmusic_api.py` uses OAuth authentication with credentials from environment

### Authentication Flow
1. Setlist.fm: API key from `SETLISTFM_API_KEY` environment variable
2. YouTube Music: OAuth credentials loaded from `oauth.json` file path specified in `YTMUSIC_OAUTH` env var

### Data Flow
1. Artist search → Get MBID → Fetch setlists → Extract songs → Calculate frequencies
2. Generate search queries → Search YouTube Music → Create/update playlist

## Development Workflow

### Setup
```bash
pip install -e ".[dev]"  # Install with development dependencies
```

### Testing
```bash
python -m pytest        # Run all tests
python -m pytest -v     # Verbose output
python -m pytest -k "test_name"  # Run specific test
```

### Key Files for Common Tasks
- Add new API endpoints: Extend `setlist_api.py` or `ytmusic_api.py`
- Modify song processing: See `utils.py::top_songs()`
- Change playlist format: See `cli.py::run()`

## Common Patterns & Conventions

### Error Handling
- API clients wrap network errors with context
- Rate limiting is handled automatically with retries
- CLI provides user-friendly error messages

### Testing
- Fixtures in `tests/conftest.py`
- Mock API responses in test files
- Integration tests marked with `@pytest.mark.integration`

### Environment Variables
Required in `.env`:
```
SETLISTFM_API_KEY=your_key
YTMUSIC_OAUTH=path/to/oauth.json
```

## Integration Points
1. Setlist.fm API
   - Rate limit: 2 requests/second
   - Endpoints used: `/search/artists`, `/artist/{mbid}/setlists`

2. YouTube Music API
   - Requires OAuth authentication
   - Endpoints: Search and playlist management

## Project-Specific Guidelines
1. Always use the `make_request()` helper for Setlist.fm API calls
2. Handle artist name variations carefully (see `search_artist()`)
3. Respect rate limits and implement backoff in new API integrations
