"""Sahayak computer controls: websites, music, VS Code and Wikipedia.

Websites and Wikipedia need internet. Music and VS Code are local.
"""

from __future__ import annotations

import logging
import os
import random
import re
import tempfile
import webbrowser
from pathlib import Path

from config import AUDIO_EXTENSIONS, Settings
from voice_io import VoiceIO

log = logging.getLogger(__name__)

TUTORIAL_URL = "https://www.youtube.com/watch?v=Lp9Ftuq2sVI"


def open_url(voice: VoiceIO, url: str) -> None:
    """Open a website (adds https:// if the scheme is missing)."""
    if not re.match(r"^https?://", url):
        url = "https://" + url
    try:
        opened = webbrowser.open(url)
    except webbrowser.Error as err:
        log.error("Browser error: %s", type(err).__name__)
        opened = False
    if not opened:
        voice.speak("I could not open the browser.")


def start_file(path: Path) -> bool:
    """Open a file with the Windows default app. Returns True on success."""
    try:
        os.startfile(str(path))          # Windows only
        return True
    except (OSError, AttributeError) as err:
        log.error("Cannot open file: %s", type(err).__name__)
        return False


def get_audio_files(folder: Path) -> list[Path]:
    """Return audio files in a folder (case-insensitive extension, sorted)."""
    try:
        return sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
        )
    except OSError as err:
        log.error("Cannot read music folder: %s", type(err).__name__)
        return []


def play_music(voice: VoiceIO, settings: Settings, mode: str) -> None:
    """mode is 'first', 'random' or 'playlist'."""
    if settings.music_dir is None:
        voice.speak("Your music folder is not set or does not exist. "
                    "Check SAHAYAK_MUSIC_DIR in the .env file.")
        return
    songs = get_audio_files(settings.music_dir)
    if not songs:
        voice.speak("I could not find any audio files in your music folder.")
        return

    if mode == "playlist":
        # Written to the temp folder so your music folder is never modified.
        target = Path(tempfile.gettempdir()) / "sahayak_playlist.m3u"
        try:
            target.write_text("\n".join(str(s) for s in songs), encoding="utf-8")
        except OSError as err:
            log.error("Cannot write playlist: %s", type(err).__name__)
            voice.speak("I could not create the playlist.")
            return
        voice.speak("Playing your full playlist.")
    else:
        target = random.choice(songs) if mode == "random" else songs[0]
        voice.speak(f"Playing {target.stem}.")

    if not start_file(target):
        voice.speak("I could not open the music player.")


def open_vscode(voice: VoiceIO, settings: Settings) -> None:
    """Open VS Code from the configured path."""
    if settings.code_path is None:
        voice.speak("The VS Code path is not set or does not exist. "
                    "Check SAHAYAK_CODE_PATH in the .env file.")
        return
    if not start_file(settings.code_path):
        voice.speak("I could not open VS Code.")


def wikipedia_search(voice: VoiceIO, query: str) -> None:
    """Speak the first two sentences of a Wikipedia summary (needs internet)."""
    topic = re.sub(
        r"\b(search|on wikipedia|wikipedia|according to|tell me about)\b", "", query
    )
    topic = " ".join(topic.split())
    if not topic:
        voice.speak("What should I search for on Wikipedia?")
        return
    try:
        import wikipediaapi
    except ImportError:
        voice.speak("Wikipedia support is not installed. Run: pip install wikipedia-api")
        return

    voice.speak("Searching Wikipedia. This needs internet.")
    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="SahayakAssistant/1.0 (student project)", language="en"
        )
        page = wiki.page(topic)
        if not page.exists():
            voice.speak(f"I could not find an entry for {topic} on Wikipedia.")
            return
        summary = page.summary.strip()
    except Exception as err:  # wikipediaapi/requests raise many network error types
        log.error("Wikipedia error: %s", type(err).__name__)
        voice.speak("I could not reach Wikipedia. Check your internet connection.")
        return
    sentences = re.split(r"(?<=[.!?])\s+", summary)
    voice.speak("According to Wikipedia. " + " ".join(sentences[:2]))