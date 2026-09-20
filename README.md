# Sahayak: An Offline, Privacy-First Student Support Assistant

A Windows desktop voice assistant for students, built in Python. Sahayak uses a **locally running Llama 3 model** through Ollama, so AI answers are generated on your own computer instead of a cloud AI service.

> **Status:** work in progress for an academic submission at Lovely Professional University. Features are marked **Implemented** or **Planned** so this document stays honest.

## Problem Statement

Students need quick help with study topics, campus information and time management, but most AI assistants need constant internet access, send questions to cloud servers, and know nothing about the student's own institution. Sahayak aims to be a **campus-aware, privacy-first assistant** whose core features keep working without internet, using a local AI model and an institution-approved local knowledge base.

## Features

| Feature | Status |
|---|---|
| Voice and text input modes, with safe switching and fallback | Implemented |
| Spoken and printed responses | Implemented |
| General conversation with local Llama 3 | Implemented |
| Wikipedia search | Implemented |
| Open YouTube, Google, Stack Overflow | Implemented |
| Play local music (first, random, playlist) | Implemented |
| Open VS Code | Implemented |
| Email with spoken confirmation | Implemented |
| Configuration validation and safe logging | Implemented |
| Modular code structure | Implemented |
| Modes: general, study, campus, focus, emergency | Planned |
| Study explanations and 5-question quizzes | Planned |
| Campus knowledge base search | Planned |
| Focus timer | Planned |
| Emergency contact information | Planned |
| Privacy-status command | Planned |

## What Works Offline and What Does Not

Sahayak is **not** fully offline. Speech recognition currently uses Google's online service.

| Component | Offline? | Notes |
|---|---|---|
| AI text generation (Ollama + Llama 3) | Yes | Runs on your computer |
| Text-to-speech (pyttsx3 / Windows voices) | Yes | |
| Text input mode | Yes | Used when no microphone is found |
| Music, VS Code, local files | Yes | |
| Voice recognition (Google) | **No** | Audio is sent to Google |
| Wikipedia search | **No** | |
| Opening websites | **No** | |
| Email (Gmail SMTP) | **No** | |

## Installation (Windows)

Requires Python 3.10+ and [Ollama](https://ollama.com).

```bash
cd sahayak_ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3
copy .env.example .env
```

Edit `.env` with your own values (all optional). If `PyAudio` fails to install, Sahayak still works with typed input.

## Run

Make sure Ollama is running, then:

```bash
python main.py
```

Sahayak asks whether to start in **voice** or **text** mode (press Enter for text). To skip the question:

```bash
python main.py --mode text
python main.py --mode voice
```

If the microphone or internet fails in voice mode, Sahayak switches to text mode automatically instead of crashing.

## Input Modes

| Command | Effect |
|---|---|
| `:text` (or say "text mode") | Switch to typing. Works fully offline |
| `:voice` (or say "voice mode") | Switch to speaking. Needs a microphone and internet |
| `:quit` (or "exit") | Close Sahayak |

In voice mode you cannot type, so say "text mode" to switch back. The current mode is shown as `[TEXT]` or `[VOICE]` at every prompt.

## Commands

| Say | Result |
|---|---|
| "What is the time" | Speaks the time |
| "Wikipedia binary search" | Short Wikipedia summary (internet) |
| "Open YouTube / Google / Stack Overflow" | Opens the site (internet) |
| "Play music" / "Play a random song" / "Play my playlist" | Plays local audio |
| "Open VS Code" | Launches VS Code |
| "Send email" | Dictate, hear it read back, say "yes" to send |
| "Exit" / "Goodbye" / "Go offline" | Closes Sahayak |
| Anything else | Answered by local Llama 3 |

## Privacy and Security

- AI replies are generated locally; questions to the AI are not sent to a cloud AI provider.
- Voice recognition sends audio to Google. Use typed input if that is not acceptable.
- Credentials come from `.env`, are never printed, and are never written to the log.
- `sahayak.log` records events and error types only, not what you say.
- Email is sent only after you hear it read back and say "yes".
- Sahayak never contacts anyone automatically.
- Never commit `.env` or `sahayak.log` (already in `.gitignore`).

## Project Structure

```
sahayak_ai/
├── main.py            # entry point and main loop
├── config.py          # constants, settings validation, logging
├── voice_io.py        # speech output, microphone input, typed fallback
├── llm_service.py     # Ollama and the shared chat history
├── assistant.py       # command classification and routing
├── media_controls.py  # websites, music, VS Code, Wikipedia
├── email_service.py   # confirmation-gated email
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Later stages add `knowledge_base.py`, `study_mode.py`, `focus_mode.py`, `emergency_mode.py`, `tests/` and a `knowledge_base/` folder. That folder will contain fictional **demonstration content only**, not official LPU information.

## Troubleshooting

| Problem | Fix |
|---|---|
| "I cannot reach the local AI model" | Start Ollama and run `ollama pull llama3` |
| "Voice mode is unavailable" | Connect a mic and install PyAudio, or keep using text mode |
| "Speech service unreachable" | Voice needs internet; Sahayak already switched to text mode |
| Music does not play | Check `SAHAYAK_MUSIC_DIR` exists and holds .mp3/.wav/.m4a/.flac files |
| Email login failed | Use a Gmail App Password and check the address |

## Limitations

- Windows only (`os.startfile`, SAPI voices).
- Voice input needs internet until an offline recognizer is added.
- Small local models can be wrong; verify important information.
- Until the privacy-status command is added, the local AI may answer "is this offline?" from general knowledge rather than from Sahayak's actual state.

## Author

Dhruv Kumar Sharma, Registration No.: 12611792, Lovely Professional University