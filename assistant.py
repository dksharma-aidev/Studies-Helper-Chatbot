"""Sahayak command classification and routing.

classify_command() is a pure function (no side effects) so it is easy to
unit test. Modes (study, campus, focus, emergency) are added in Stage 3.
"""

from __future__ import annotations

import datetime
import logging

import media_controls
from config import (
    EXIT_PHRASES,
    INPUT_TEXT,
    INPUT_VOICE,
    TEXT_MODE_PHRASES,
    VOICE_MODE_PHRASES,
    Settings,
)
from email_service import send_email
from llm_service import LLMService
from voice_io import VoiceIO

log = logging.getLogger(__name__)

# Command names returned by classify_command()
EXIT = "exit"
SET_TEXT_MODE = "set_text_mode"
SET_VOICE_MODE = "set_voice_mode"
UNKNOWN_CONTROL = "unknown_control"
STATUS = "status"
WIKIPEDIA = "wikipedia"
OPEN_YOUTUBE = "open_youtube"
OPEN_GOOGLE = "open_google"
OPEN_STACKOVERFLOW = "open_stackoverflow"
PLAY_TUTORIAL = "play_tutorial"
PLAY_PLAYLIST = "play_playlist"
PLAY_RANDOM = "play_random"
PLAY_MUSIC = "play_music"
TIME = "time"
OPEN_CODE = "open_code"
SEND_EMAIL = "send_email"
CHAT = "chat"


def classify_command(query: str) -> str:
    """Decide which command a (normalized) query is. Order matters."""
    q = query.strip(" .!?")
    if q in EXIT_PHRASES:               # exact match, so "is this offline" is NOT an exit
        return EXIT
    if q in TEXT_MODE_PHRASES:
        return SET_TEXT_MODE
    if q in VOICE_MODE_PHRASES:
        return SET_VOICE_MODE
    if q.startswith(":"):               # mistyped control command, never sent to the AI
        return UNKNOWN_CONTROL
    if q in {"status", "system status"}:
        return STATUS
    if "wikipedia" in q:
        return WIKIPEDIA
    if "open youtube" in q:
        return OPEN_YOUTUBE
    if "open google" in q:
        return OPEN_GOOGLE
    if "open stackoverflow" in q or "open stack overflow" in q:
        return OPEN_STACKOVERFLOW
    if "play tutorial" in q:
        return PLAY_TUTORIAL
    if "playlist" in q and "play" in q:  # before "play music" so it is reachable
        return PLAY_PLAYLIST
    if "random song" in q:
        return PLAY_RANDOM
    if "play music" in q or "play some music" in q:
        return PLAY_MUSIC
    if "the time" in q:
        return TIME
    if "open code" in q or "open vs code" in q:
        return OPEN_CODE
    if "send email" in q:
        return SEND_EMAIL
    return CHAT


class Assistant:
    """Runs one command at a time."""

    def __init__(self, voice: VoiceIO, llm: LLMService, settings: Settings) -> None:
        self.voice = voice
        self.llm = llm
        self.settings = settings

    def handle(self, query: str) -> bool:
        """Run one command. Returns False when the user wants to exit."""
        command = classify_command(query)
        voice = self.voice

        if command == EXIT:
            voice.speak("Going offline. Sahayak out.")
            return False
        if command == SET_TEXT_MODE:
            voice.set_input_mode(INPUT_TEXT)
            voice.speak("Text mode is on.")
        elif command == SET_VOICE_MODE:
            if voice.set_input_mode(INPUT_VOICE):
                voice.speak("Voice mode is on. Say text mode to switch back.")
        elif command == UNKNOWN_CONTROL:
            voice.speak("Unknown command. Use :voice, :text or :quit.")
        elif command == STATUS:
            voice.speak(f"Sahayak is running in {voice.mode_label().lower()} mode.")
        elif command == WIKIPEDIA:
            media_controls.wikipedia_search(voice, query)
        elif command == OPEN_YOUTUBE:
            media_controls.open_url(voice, "youtube.com")
        elif command == OPEN_GOOGLE:
            media_controls.open_url(voice, "google.com")
        elif command == OPEN_STACKOVERFLOW:
            media_controls.open_url(voice, "stackoverflow.com")
        elif command == PLAY_TUTORIAL:
            media_controls.open_url(voice, media_controls.TUTORIAL_URL)
        elif command == PLAY_PLAYLIST:
            media_controls.play_music(voice, self.settings, "playlist")
        elif command == PLAY_RANDOM:
            media_controls.play_music(voice, self.settings, "random")
        elif command == PLAY_MUSIC:
            media_controls.play_music(voice, self.settings, "first")
        elif command == TIME:
            voice.speak(f"The time is {datetime.datetime.now().strftime('%H:%M')}.")
        elif command == OPEN_CODE:
            media_controls.open_vscode(voice, self.settings)
        elif command == SEND_EMAIL:
            send_email(voice, self.settings)
        else:
            print("[System]: Asking the local AI...")
            voice.speak(self.llm.ask(query))
        return True