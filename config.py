"""Sahayak configuration: constants, settings validation and logging.

Nothing in this file ever prints or logs a password or other secret value.
Only the *names* of missing settings are reported.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------- constants
APP_NAME = "Sahayak"

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
LOG_FILE = BASE_DIR / "sahayak.log"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"   # used from Stage 4

OLLAMA_MODEL = "llama3"
MAX_LLM_TOKENS = 150            # maximum length of one LLM reply
MAX_HISTORY_MESSAGES = 7        # system prompt + last 6 messages
MAX_QUERY_CHARS = 500           # longer input is cut off (safer input handling)

AUDIO_EXTENSIONS = frozenset({".mp3", ".wav", ".m4a", ".flac"})

SYSTEM_PROMPT = (
    "Your name is Sahayak. You are a helpful student support assistant. "
    "Give short, concise, conversational answers under 2 sentences."
)

EXIT_PHRASES = frozenset(
    {":quit", "exit", "quit", "goodbye", "offline", "go offline", "exit program"}
)

# Input modes (how the user talks to Sahayak). Not the same as the
# assistant modes (study, campus, ...) that arrive in Stage 3.
INPUT_VOICE = "voice"
INPUT_TEXT = "text"
TEXT_MODE_PHRASES = frozenset(
    {":text", "text mode", "switch to text mode", "use text mode", "use text"}
)
VOICE_MODE_PHRASES = frozenset(
    {":voice", "voice mode", "switch to voice mode", "use voice mode", "use voice"}
)
# Confirmation words. A reply counts as "yes" if it contains one of the
# affirmative words and none of the negative words.
AFFIRMATIVE_WORDS = frozenset(
    {"yes", "yeah", "yep", "yup", "sure", "ok", "okay", "confirm",
     "send", "correct", "affirmative"}
)
NEGATIVE_WORDS = frozenset(
    {"no", "nope", "nah", "not", "cancel", "stop", "never", "don't", "dont"}
)
CONFIRM_VOICE_ATTEMPTS = 2      # voice tries before offering typed confirmation

# Environment variable names. The first name is the preferred one; the
# second is the old name from the original script (still accepted).
ENV_MUSIC_DIR = ("SAHAYAK_MUSIC_DIR", "music_dir")
ENV_CODE_PATH = ("SAHAYAK_CODE_PATH", "code_path")
ENV_EMAIL_ADDRESS = ("SAHAYAK_EMAIL_ADDRESS", "my_email")
ENV_EMAIL_PASSWORD = ("SAHAYAK_EMAIL_PASSWORD", "password")
ENV_EMAIL_TO = ("SAHAYAK_EMAIL_TO", "to_email")


# ----------------------------------------------------------------- settings
@dataclass(frozen=True)
class Settings:
    """Validated settings. Invalid or missing values become None."""

    music_dir: Optional[Path] = None
    code_path: Optional[Path] = None
    email_address: Optional[str] = None
    email_password: Optional[str] = field(default=None, repr=False)  # never shown
    email_to: Optional[str] = None
    warnings: tuple[str, ...] = ()

    @property
    def email_configured(self) -> bool:
        """True only when address, password and recipient are all valid."""
        return all([self.email_address, self.email_password, self.email_to])


def env_first(names: tuple[str, ...]) -> Optional[str]:
    """Return the first non-empty environment variable among names, or None."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None


def _looks_like_email(value: str) -> bool:
    """Very simple check: something@something.something."""
    local, _, domain = value.partition("@")
    return bool(local) and "." in domain and " " not in value


def load_settings() -> Settings:
    """Read the .env file and environment, validate everything, never crash."""
    load_dotenv(ENV_FILE)
    warnings: list[str] = []

    music_dir: Optional[Path] = None
    raw = env_first(ENV_MUSIC_DIR)
    if raw:
        candidate = Path(raw).expanduser()
        if candidate.is_dir():
            music_dir = candidate
        else:
            warnings.append(f"{ENV_MUSIC_DIR[0]} is set but the folder does not exist.")

    code_path: Optional[Path] = None
    raw = env_first(ENV_CODE_PATH)
    if raw:
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            code_path = candidate
        else:
            warnings.append(f"{ENV_CODE_PATH[0]} is set but the file does not exist.")

    address = env_first(ENV_EMAIL_ADDRESS)
    password = env_first(ENV_EMAIL_PASSWORD)
    recipient = env_first(ENV_EMAIL_TO)
    given = {
        ENV_EMAIL_ADDRESS[0]: address,
        ENV_EMAIL_PASSWORD[0]: password,
        ENV_EMAIL_TO[0]: recipient,
    }
    if any(given.values()) and not all(given.values()):
        missing = ", ".join(name for name, value in given.items() if not value)
        warnings.append(f"Email is partly configured. Missing: {missing}.")
        address = password = recipient = None
    for label, value in (("address", address), ("recipient", recipient)):
        if value and not _looks_like_email(value):
            warnings.append(f"The email {label} does not look like a valid address.")
            address = password = recipient = None
            break

    return Settings(
        music_dir=music_dir,
        code_path=code_path,
        email_address=address,
        email_password=password,
        email_to=recipient,
        warnings=tuple(warnings),
    )


def feature_status(settings: Settings) -> dict[str, bool]:
    """Which optional features are ready (used for the startup summary)."""
    return {
        "Music folder": settings.music_dir is not None,
        "VS Code shortcut": settings.code_path is not None,
        "Email": settings.email_configured,
    }


# ------------------------------------------------------------------ logging
def setup_logging() -> None:
    """Log events to sahayak.log. Never pass secrets or spoken text to logs."""
    handlers: list[logging.Handler] = []
    try:
        handlers.append(
            RotatingFileHandler(
                LOG_FILE, maxBytes=500_000, backupCount=2, encoding="utf-8"
            )
        )
    except OSError:
        handlers.append(logging.NullHandler())   # app still runs without a log
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )