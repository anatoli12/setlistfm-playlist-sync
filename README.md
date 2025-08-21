# 🎵 Setlist.fm Playlist Sync

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Create YouTube Music playlists from an artist's most-played songs on Setlist.fm for a given year. This tool analyzes live performance data to discover what songs an artist plays most often in their shows and automatically creates a playlist of studio versions.

## ✨ Features

- 🔍 **Smart Artist Search** - Automatic artist disambiguation and matching
- 📊 **Live Performance Analytics** - Analyzes frequency of songs played live
- 🎧 **YouTube Music Integration** - Creates private playlists automatically
- ⚡ **Rate Limiting & Error Handling** - Robust API handling with exponential backoff
- 🎯 **Intelligent Matching** - Handles special cases (intros, tapes, featuring artists)
- 📈 **Configurable Results** - Choose how many top tracks to include

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/anatoli12/setlistfm-playlist-sync.git
cd setlistfm-playlist-sync

# Install the package
pip install -e .
```

### Setup

1. **Get API Keys**
   - [Setlist.fm API key](https://api.setlist.fm/docs/1.0/index.html) (free registration required)
   - YouTube Music OAuth credentials (see setup guide below)

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **YouTube Music Setup**
   - Follow the [ytmusicapi OAuth guide](https://ytmusicapi.readthedocs.io/en/stable/setup.html)
   - Create `oauth.json` in the project root
   - Set `YTM_CLIENT_ID` and `YTM_CLIENT_SECRET` in your `.env`

### Usage

```bash
# Basic usage - creates top 20 playlist
setlistfm-playlist-sync --artist "Megadeth" --year 2024

# Custom number of tracks
setlistfm-playlist-sync --artist "Iron Maiden" --year 2023 --tracks 15

# Verbose output for debugging
setlistfm-playlist-sync --artist "Metallica" --year 2024 --verbose
```

## 📖 Detailed Setup Guide

### 1. Environment Configuration

Your `.env` file should contain:

```env
# Required: Setlist.fm API key
SETLISTFM_API_KEY=your_setlist_fm_api_key

# Optional: Language preference (default: en)
SETLISTFM_ACCEPT_LANGUAGE=en

# Required: YouTube Music OAuth
YTM_CLIENT_ID=your_client_id
YTM_CLIENT_SECRET=your_client_secret
```

### 2. YouTube Music OAuth Setup

The YouTube Music API requires OAuth authentication. Here's how to set it up:

1. **Get OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials

2. **Create oauth.json**
   - Use ytmusicapi's setup tools or manually create the file
   - Place it in the project root directory
   - The file should contain your OAuth tokens

3. **Set Environment Variables**
   - Add your client ID and secret to `.env`
   - These are needed for token refresh

## 🛠️ Development

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=setlistfm_playlist_sync

# Run specific test
python -m pytest tests/test_utils.py -v

# Run with verbose output
python -m pytest -v
```

## 🏗️ Project Structure

```
src/setlistfm_playlist_sync/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface
├── setlist_api.py      # Setlist.fm API client
├── ytmusic_api.py      # YouTube Music API client  
└── utils.py            # Helper functions

tests/                  # Test suite
docs/                   # Documentation
.github/                # GitHub workflows & templates
```

## 📊 How It Works

1. **Artist Search** - Searches Setlist.fm for the artist, handling variations and disambiguation
2. **Setlist Fetching** - Retrieves all setlists from the specified year with pagination
3. **Song Analysis** - Counts song frequencies and ranks by popularity
4. **YouTube Search** - Finds studio versions of songs on YouTube Music
5. **Playlist Creation** - Creates or updates a private playlist with found tracks

## ⚙️ Configuration Options

### Command Line Arguments

- `--artist` (required): Artist name to search for
- `--year` (required): Year to analyze (1950-2030)
- `--tracks`: Number of top tracks (1-100, default: 20)
- `--verbose`: Enable detailed logging

### Environment Variables

- `SETLISTFM_API_KEY`: Your Setlist.fm API key
- `SETLISTFM_ACCEPT_LANGUAGE`: Response language (default: en)
- `YTM_CLIENT_ID`: YouTube Music OAuth client ID
- `YTM_CLIENT_SECRET`: YouTube Music OAuth client secret

## 🔧 Troubleshooting

### Common Issues

1. **"Artist not found"**
   - Try variations of the artist name
   - Check spelling and try with/without "The"

2. **"No songs found for year"**
   - Artist may not have toured that year
   - Try adjacent years or check Setlist.fm manually

3. **YouTube Music authentication errors**
   - Ensure oauth.json is in project root
   - Check that OAuth credentials are valid
   - Try regenerating the oauth.json file

### Debug Mode

Use `--verbose` flag for detailed logging:

```bash
setlistfm-playlist-sync --artist "Artist" --year 2024 --verbose
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Setlist.fm](https://setlist.fm) for providing comprehensive concert data
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) for YouTube Music API access
- The music community for keeping live music history alive

## ⚠️ Disclaimer

This tool is for personal use only. Respect the terms of service of both Setlist.fm and YouTube Music. The created playlists are private by default.
