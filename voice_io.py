"""Sahayak voice input/output and input-mode handling.

Two input modes:
  * TEXT  - you type with input(). Works fully offline.
  * VOICE - you speak. Uses Google's online recognizer, so it needs internet.

Speech OUTPUT (pyttsx3) is local and works offline in both modes.
If voice input fails because of the microphone or the network, Sahayak
falls back to text mode instead of crashing.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from config import (
    AFFIRMATIVE_WORDS,
    CONFIRM_VOICE_ATTEMPTS,
    INPUT_TEXT,
    INPUT_VOICE,
    MAX_QUERY_CHARS,
    NEGATIVE_WORDS,
)

try:
    import pyttsx3
except ImportError:          # optional: app still runs, text output only
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:          # optional: voice mode unavailable, text mode works
    sr = None

log = logging.getLogger(__name__)

UNRECOGNIZED_HINT_EVERY = 3   # show a hint after this many failed recognitions


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace and cap the length of user input."""
    return " ".join(text.lower().split())[:MAX_QUERY_CHARS]


def is_yes(text: Optional[str]) -> bool:
    """True if text contains a 'yes' word and no 'no' word.

    Tolerant on purpose: "yes", "yes please", "yeah send it" and "okay" all
    count, while "no", "cancel" and "yes, don't send it" do not.
    """
    if not text:
        return False
    words = set(re.findall(r"[a-z']+", text.lower()))
    if words & NEGATIVE_WORDS:
        return False
    return bool(words & AFFIRMATIVE_WORDS)


class VoiceIO:
    """Handles speaking and listening. One instance is shared by the app."""

    def __init__(self) -> None:
        self.input_mode = INPUT_TEXT          # safest default
        self._engine = None
        self._tts_failed = pyttsx3 is None
        self._failed_recognitions = 0

    # -------------------------------------------------------- input modes
    def mode_label(self) -> str:
        """Return 'VOICE' or 'TEXT' for display."""
        return self.input_mode.upper()

    def show_mode(self) -> None:
        """Print the current input mode clearly."""
        note = ("speak your commands (needs internet)"
                if self.input_mode == INPUT_VOICE else "type your commands (works offline)")
        print(f"[Input mode: {self.mode_label()}] {note}")
        print("[System]: Commands: :voice  :text  :quit")

    def microphone_available(self) -> bool:
        """Test right now whether a microphone can be opened."""
        if sr is None:
            log.error("SpeechRecognition is not installed")
            return False
        try:
            with sr.Microphone():
                return True
        except (OSError, AttributeError) as err:
            # AttributeError means PyAudio is not installed.
            log.error("Microphone unavailable: %s", type(err).__name__)
            return False

    def set_input_mode(self, mode: str) -> bool:
        """Switch input mode. Returns True if the requested mode is now active.

        Asking for voice mode when the microphone is unavailable keeps text mode.
        """
        if mode == INPUT_VOICE:
            if not self.microphone_available():
                self.input_mode = INPUT_TEXT
                print("[System]: Voice mode is unavailable (no working microphone "
                      "or PyAudio). Staying in TEXT mode.")
                return False
            self.input_mode = INPUT_VOICE
            self._failed_recognitions = 0
        else:
            self.input_mode = INPUT_TEXT
        self.show_mode()
        return True

    def select_startup_mode(self, requested: Optional[str] = None) -> None:
        """Choose the input mode at startup (from --mode, or by asking)."""
        if requested in (INPUT_VOICE, INPUT_TEXT):
            self.set_input_mode(requested)
            return
        print("Choose input mode:")
        print("  1) Voice  (needs a microphone and internet)")
        print("  2) Text   (type commands, works offline)")
        try:
            choice = input("Enter 1 or 2 (just press Enter for text): ").strip().lower()
        except EOFError:
            choice = ""
        if choice in {"1", "v", "voice"}:
            self.set_input_mode(INPUT_VOICE)
        else:
            self.set_input_mode(INPUT_TEXT)

    def _fall_back_to_text(self, reason: str) -> None:
        """Switch to text mode after a voice failure and tell the user why."""
        self.input_mode = INPUT_TEXT
        print(f"[System]: {reason}")
        print("[System]: Switched to TEXT mode. Type :voice to try voice again.")
        self.show_mode()

    # ------------------------------------------------------------- output
    def speak(self, text: str) -> None:
        """Print text and speak it. If audio fails, keep going with text only."""
        if not text:
            return
        print(f"[Sahayak]: {text}")
        if self._tts_failed:
            return
        try:
            if self._engine is None:
                self._engine = pyttsx3.init("sapi5")   # created once
                self._engine.setProperty("rate", 150)
                voices = self._engine.getProperty("voices")
                if voices:
                    self._engine.setProperty("voice", voices[0].id)
            self._engine.say(text)
            self._engine.runAndWait()
        except (RuntimeError, OSError, ImportError) as err:
            self._tts_failed = True
            log.error("Text-to-speech disabled: %s", type(err).__name__)
            print("[System]: Voice output unavailable. Continuing with text only.")

    # -------------------------------------------------------------- input
    def listen(self, short_answer: bool = False) -> Optional[str]:
        """Return normalized user text, or None if nothing was understood.

        short_answer=True is for one-word replies like "yes": it calibrates
        for background noise and stops listening sooner (voice mode only).
        """
        if self.input_mode == INPUT_VOICE:
            return self._read_microphone(short_answer)
        return self._read_typed()

    def confirm(self, prompt: str) -> bool:
        """Ask a yes/no question. Anything except a clear 'yes' means no.

        In voice mode: tries the microphone a couple of times (showing what
        it heard), then offers typed confirmation so it can never get stuck.
        """
        self.speak(prompt)
        if self.input_mode == INPUT_VOICE:
            for attempt in range(CONFIRM_VOICE_ATTEMPTS):
                if self.input_mode != INPUT_VOICE:
                    break                      # fell back to text mid-way
                answer = self.listen(short_answer=True)
                if answer is not None:
                    print(f"[System]: I heard: '{answer}'")
                    if is_yes(answer):
                        return True
                    if re.search(r"\b(no|nope|cancel|stop)\b", answer):
                        return False
                if attempt < CONFIRM_VOICE_ATTEMPTS - 1:
                    print("[System]: Please say 'yes' or 'no' again.")
            print("[System]: Could not confirm by voice.")
        try:
            typed = input("Type YES to confirm, anything else to cancel: ")
        except EOFError:
            return False
        return is_yes(typed)

    def _read_typed(self) -> Optional[str]:
        try:
            text = normalize_text(input(f"[{self.mode_label()}] You: "))
        except EOFError:
            return ":quit"         # input stream closed: shut down cleanly
        return text or None

    def _read_microphone(self, short_answer: bool = False) -> Optional[str]:
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 0.8 if short_answer else 1.5
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        try:
            with sr.Microphone() as source:
                if short_answer:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"[{self.mode_label()}] Listening...")
                audio = recognizer.listen(
                    source,
                    timeout=8 if short_answer else 10,
                    phrase_time_limit=5 if short_answer else 20,
                )
        except sr.WaitTimeoutError:
            return None            # silence: just listen again
        except (OSError, AttributeError) as err:
            log.error("Microphone error: %s", type(err).__name__)
            self._fall_back_to_text("Microphone problem: it may have been unplugged.")
            return None

        try:
            print("Recognizing...")
            text = recognizer.recognize_google(audio, language="en-in")
        except sr.UnknownValueError:
            self._failed_recognitions += 1
            print("Say that again please...")
            if self._failed_recognitions % UNRECOGNIZED_HINT_EVERY == 0:
                print("[System]: Trouble hearing you? Say 'text mode' to switch to typing.")
            return None
        except sr.RequestError as err:
            log.error("Speech service error: %s", type(err).__name__)
            self._fall_back_to_text("Speech service unreachable (voice needs internet).")
            return None
        self._failed_recognitions = 0
        text = normalize_text(text)
        print(f"User said: {text}\n")
        return text or None