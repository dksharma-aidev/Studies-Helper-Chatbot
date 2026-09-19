"""Addix - desktop voice assistant (Stage 1: bug-fixed version).

Same features as the original script, with the known bugs and risky
behaviour fixed. No new features yet (those start in Stage 2).
"""

import datetime
import logging
import os
import random
import re
import smtplib
import tempfile
import webbrowser
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import httpx
import ollama
import pyttsx3
import speech_recognition as sr
import wikipediaapi
from dotenv import load_dotenv

# ---------------------------------------------------------------- constants
OLLAMA_MODEL = "llama3"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}
MAX_LLM_TOKENS = 150          # was 50, which cut answers mid-sentence
MAX_HISTORY_MESSAGES = 7      # system prompt + last 6 messages
SYSTEM_PROMPT = (
    "Your name is Addix, the x is silent. You are a helpful desktop robot "
    "assistant. Give short, concise, conversational answers under 2 sentences."
)
EXIT_PHRASES = {"exit", "quit", "goodbye", "offline", "go offline", "exit program"}
YES_WORDS = {"yes", "yeah", "yep", "send", "send it", "confirm", "yes send it"}

# Network errors that mean "Ollama is not reachable / model missing".
OLLAMA_ERRORS = (ollama.ResponseError, ConnectionError, OSError, httpx.HTTPError)

load_dotenv()

# Log to a file. We log events only, never credentials or spoken text.
logging.basicConfig(
    filename="addix.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("addix")

# Single shared chat history (system prompt is always item 0).
chat_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

_engine: Optional[pyttsx3.Engine] = None
_engine_failed = False


# ------------------------------------------------------------------ config
def env_first(*names: str) -> Optional[str]:
    """Return the first non-empty environment variable among names, or None."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None


def get_music_dir() -> Optional[Path]:
    """Return the music folder as a Path if configured and it exists."""
    raw = env_first("music_dir", "SAHAYAK_MUSIC_DIR")
    if raw is None:
        return None
    path = Path(raw).expanduser()
    return path if path.is_dir() else None


def get_audio_files(folder: Path) -> list[Path]:
    """Return audio files in folder (case-insensitive extension, sorted)."""
    try:
        return sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
        )
    except OSError as err:
        log.error("Cannot read music folder: %s", err)
        return []


def check_config() -> None:
    """Print which optional features are configured (values are never shown)."""
    checks = {
        "Music folder": get_music_dir() is not None,
        "VS Code path": env_first("code_path", "SAHAYAK_CODE_PATH") is not None,
        "Email": all([
            env_first("my_email", "SAHAYAK_EMAIL_ADDRESS"),
            env_first("password", "SAHAYAK_EMAIL_PASSWORD"),
            env_first("to_email", "SAHAYAK_EMAIL_TO"),
        ]),
    }
    for feature, ok in checks.items():
        print(f"[System]: {feature}: {'configured' if ok else 'NOT configured (feature disabled)'}")


# ------------------------------------------------------------------- voice
def speak(text: str) -> None:
    """Speak text aloud. Always prints too, so the app works without audio."""
    global _engine, _engine_failed
    print(f"[Addix]: {text}")
    if _engine_failed or not text:
        return
    try:
        if _engine is None:
            _engine = pyttsx3.init("sapi5")   # created once, not on every call
            _engine.setProperty("rate", 150)
            voices = _engine.getProperty("voices")
            if voices:
                _engine.setProperty("voice", voices[0].id)
        _engine.say(text)
        _engine.runAndWait()
    except (RuntimeError, OSError, ImportError) as err:
        _engine_failed = True
        log.error("Text-to-speech disabled: %s", err)
        print("[System]: Voice output unavailable. Continuing with text only.")


def microphone_available() -> bool:
    """Check once at startup whether a microphone can be opened."""
    try:
        with sr.Microphone():
            return True
    except (OSError, AttributeError, ImportError) as err:
        # AttributeError happens when PyAudio is not installed.
        log.error("Microphone unavailable: %s", err)
        return False


def listen(use_mic: bool) -> Optional[str]:
    """Return lowercase text from the user, or None if nothing was understood."""
    if not use_mic:
        text = input("You (type): ").strip().lower()
        return text or None

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5
    recognizer.energy_threshold = 300
    try:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
    except sr.WaitTimeoutError:
        return None                      # silence: just listen again
    except (OSError, AttributeError) as err:
        log.error("Microphone error: %s", err)
        print("[System]: Microphone problem. Check that it is connected.")
        return None

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio, language="en-in")
    except sr.UnknownValueError:
        print("Say that again please...")
        return None
    except sr.RequestError as err:
        log.error("Speech service error: %s", err)
        print("[System]: Speech service unreachable. Check your internet connection.")
        return None
    print(f"User said: {text}\n")
    return text.lower().strip()


# --------------------------------------------------------------------- LLM
def warm_up_llm() -> bool:
    """Load the model into memory. Uses a throwaway call, not the chat history."""
    try:
        ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            options={"num_predict": 1},
        )
        return True
    except OLLAMA_ERRORS as err:
        log.error("Ollama warm-up failed: %s", err)
        return False


def local_llm(user_prompt: str) -> str:
    """Send a prompt to the local Ollama model and return its reply."""
    global chat_history
    chat_history.append({"role": "user", "content": user_prompt})
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=chat_history,
            options={"num_predict": MAX_LLM_TOKENS, "temperature": 0.5},
        )
        reply = response["message"]["content"].strip()
    except OLLAMA_ERRORS as err:
        chat_history.pop()               # don't keep a question with no answer
        log.error("Ollama error: %s", err)
        return ("I cannot reach the local AI model. "
                "Make sure Ollama is running and llama3 is installed.")
    chat_history.append({"role": "assistant", "content": reply})
    if len(chat_history) > MAX_HISTORY_MESSAGES:
        chat_history = [chat_history[0]] + chat_history[-(MAX_HISTORY_MESSAGES - 1):]
    return reply


# --------------------------------------------------------------- utilities
def open_url(url: str) -> None:
    """Open a website (adds https:// if the scheme is missing)."""
    if not re.match(r"^https?://", url):
        url = "https://" + url
    if not webbrowser.open(url):
        speak("I could not open the browser.")


def start_file(path: Path) -> bool:
    """Open a file with the Windows default app. Returns True on success."""
    try:
        os.startfile(str(path))          # Windows only
        return True
    except (OSError, AttributeError) as err:
        log.error("Cannot open file: %s", err)
        return False


def wikipedia_search(query: str) -> None:
    """Speak the first two sentences of a Wikipedia summary."""
    topic = re.sub(
        r"\b(search|on wikipedia|wikipedia|according to|tell me about)\b", "", query
    ).strip()
    if not topic:
        speak("What should I search for on Wikipedia?")
        return
    speak("Searching Wikipedia...")
    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="AddixAssistant/1.0 (student project)", language="en"
        )
        page = wiki.page(topic)
        if not page.exists():
            speak(f"I could not find an entry for {topic} on Wikipedia.")
            return
    except Exception as err:  # wikipediaapi raises several network error types
        log.error("Wikipedia error: %s", err)
        speak("I could not reach Wikipedia. Check your internet connection.")
        return
    sentences = re.split(r"(?<=[.!?])\s+", page.summary.strip())
    speak("According to Wikipedia. " + " ".join(sentences[:2]))


def play_music(mode: str) -> None:
    """mode is 'first', 'random' or 'playlist'."""
    folder = get_music_dir()
    if folder is None:
        speak("Your music folder is not set or does not exist. Check music_dir in the env file.")
        return
    songs = get_audio_files(folder)
    if not songs:
        speak("I could not find any audio files in your music folder.")
        return

    if mode == "playlist":
        # Written to the temp folder; no race with deleting it, and it never
        # touches the user's music folder.
        playlist = Path(tempfile.gettempdir()) / "addix_playlist.m3u"
        try:
            playlist.write_text("\n".join(str(s) for s in songs), encoding="utf-8")
        except OSError as err:
            log.error("Cannot write playlist: %s", err)
            speak("I could not create the playlist.")
            return
        target = playlist
        speak("Playing your full playlist.")
    else:
        target = random.choice(songs) if mode == "random" else songs[0]
        speak(f"Playing {target.stem}.")

    if not start_file(target):
        speak("I could not open the music player.")


def open_vscode() -> None:
    """Open VS Code from the configured path."""
    raw = env_first("code_path", "SAHAYAK_CODE_PATH")
    if raw is None:
        speak("The VS Code path is not set in the env file.")
        return
    path = Path(raw).expanduser()
    if not path.is_file():
        speak("The VS Code path in the env file does not exist.")
        return
    if not start_file(path):
        speak("I could not open VS Code.")


def send_email(use_mic: bool) -> None:
    """Dictate an email, read it back, and send only after a spoken 'yes'."""
    sender = env_first("my_email", "SAHAYAK_EMAIL_ADDRESS")
    password = env_first("password", "SAHAYAK_EMAIL_PASSWORD")
    recipient = env_first("to_email", "SAHAYAK_EMAIL_TO")
    if not (sender and password and recipient):
        speak("Email is not configured. Please set the email values in the env file.")
        return

    speak("What is the content?")
    content = listen(use_mic)
    if not content:
        speak("I didn't catch that. Email cancelled.")
        return

    speak(f"I heard: {content}. Say yes to send it, or anything else to cancel.")
    answer = listen(use_mic)
    if answer is None or answer.strip(" .!") not in YES_WORDS:
        speak("Email cancelled.")
        return

    msg = MIMEText(content)
    msg["Subject"] = "Automated Message"
    msg["From"] = sender
    msg["To"] = recipient
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        log.error("Email login failed")
        speak("Email login failed. Check your address and app password.")
        return
    except (smtplib.SMTPException, OSError) as err:
        log.error("Email error: %s", type(err).__name__)
        speak("The email cannot be sent right now.")
        return
    log.info("Email sent")
    speak("Email has been sent.")


def greet() -> None:
    """Greet the user based on the time of day."""
    hour = datetime.datetime.now().hour
    part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
    speak(f"Good {part}. This is Addix. Waiting for instructions.")


# ---------------------------------------------------------- command router
def handle_command(query: str, use_mic: bool) -> bool:
    """Run one command. Returns False when the user wants to exit."""
    if query.strip(" .!") in EXIT_PHRASES:
        speak("Going offline. Addix out.")
        return False

    # Order matters: longer/more specific phrases come first.
    if query.strip(" .!") in {"status", "system status"}:
        speak("Welcome back to the terminal, sir.")
    elif "wikipedia" in query:
        wikipedia_search(query)
    elif "open youtube" in query:
        open_url("youtube.com")
    elif "open google" in query:
        open_url("google.com")
    elif "open stackoverflow" in query or "open stack overflow" in query:
        open_url("stackoverflow.com")
    elif "play tutorial" in query:
        open_url("https://www.youtube.com/watch?v=Lp9Ftuq2sVI")
    elif "playlist" in query and "play" in query:
        play_music("playlist")   # checked before "play music" (it used to be unreachable)
    elif "random song" in query:
        play_music("random")
    elif "play music" in query or "play some music" in query:
        play_music("first")
    elif "the time" in query:
        speak(f"The time is {datetime.datetime.now().strftime('%H:%M')}.")
    elif "open code" in query or "open vs code" in query:
        open_vscode()
    elif "send email" in query:
        send_email(use_mic)
    else:
        print("[System]: Asking the local AI...")
        speak(local_llm(query))
    return True


# -------------------------------------------------------------------- main
def main() -> None:
    print("=============================================")
    print("              ADDIX - STARTING               ")
    print("=============================================")
    check_config()

    use_mic = microphone_available()
    if not use_mic:
        print("[System]: No microphone found. Using typed input instead.")

    print("[System]: Loading local AI model...")
    if warm_up_llm():
        print("[System]: Local AI model ready.")
    else:
        print("[System]: WARNING: Ollama not reachable. Start Ollama and run: ollama pull llama3")
        print("[System]: Other commands will still work.")

    greet()
    while True:
        query = listen(use_mic)
        if query is None:
            continue
        try:
            if not handle_command(query, use_mic):
                break
        except KeyboardInterrupt:
            raise
        except Exception:  # last-resort guard so one bad command can't kill the loop
            log.exception("Unexpected error while handling a command")
            speak("Something went wrong with that command. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[System]: Stopped by user.")