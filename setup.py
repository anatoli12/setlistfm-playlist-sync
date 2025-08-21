"""Setup configuration for setlistfm-playlist-sync."""
from setuptools import setup, find_packages

setup(
    name="setlistfm-playlist-sync",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "ytmusicapi",
        "python-dotenv",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "setlistfm-playlist-sync=setlistfm_playlist_sync.cli:main",
        ],
    },
    author="anatoli12",
    description="Create YouTube Music playlists from Setlist.fm data",
    keywords="music, youtube, setlist.fm, playlist",
    url="https://github.com/anatoli12/setlistfm-playlist-sync",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
