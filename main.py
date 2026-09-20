"""Sahayak entry point. Run with:  python main.py"""

from __future__ import annotations

import argparse
import datetime
import logging
from typing import Optional

from assistant import Assistant
from config import (
    APP_NAME,
    INPUT_TEXT,
    INPUT_VOICE,
    OLLAMA_MODEL,
    Settings,
    feature_status,
    load_settings,
    setup_logging,
)
from llm_service import LLMService
from voice_io import VoiceIO

log = logging.getLogger(__name__)


def print_startup_summary(settings: Settings) -> None:
    """Show which optional features are ready. Never prints secret values."""
    for feature, ready in feature_status(settings).items():
        state = "ready" if ready else "not configured (feature disabled)"
        print(f"[System]: {feature}: {state}")
    for warning in settings.warnings:
        print(f"[Config warning]: {warning}")


def greet(voice: VoiceIO) -> None:
    """Greet the user based on the time of day."""
    hour = datetime.datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    voice.speak(f"Good {part}. This is {APP_NAME}. Waiting for instructions.")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Read the optional --mode flag (skips the startup question)."""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} student assistant")
    parser.add_argument(
        "--mode", choices=[INPUT_VOICE, INPUT_TEXT],
        help="start directly in voice or text input mode",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    """Start Sahayak. Optional features that fail do not stop the program."""
    args = parse_args(argv)
    setup_logging()
    print("=============================================")
    print(f"                {APP_NAME.upper()}                    ")
    print("=============================================")

    settings = load_settings()
    print_startup_summary(settings)
    for warning in settings.warnings:
        log.warning(warning)               # warnings contain names only, no values

    voice = VoiceIO()
    voice.select_startup_mode(args.mode)   # falls back to text if no microphone

    llm = LLMService()
    print("[System]: Loading local AI model...")
    if llm.warm_up():
        print("[System]: Local AI model ready.")
    else:
        print(f"[System]: WARNING: Ollama not reachable. Start Ollama and run: ollama pull {OLLAMA_MODEL}")
        print("[System]: Other commands will still work.")

    assistant = Assistant(voice, llm, settings)
    greet(voice)

    while True:
        query = voice.listen()
        if query is None:
            continue
        try:
            if not assistant.handle(query):
                break
        except Exception:  # last-resort guard so one bad command can't end the session
            log.exception("Unexpected error while handling a command")
            voice.speak("Something went wrong with that command. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[System]: Stopped by user.")