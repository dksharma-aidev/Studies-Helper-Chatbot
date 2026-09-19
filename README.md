# Sahayak AI: An Offline, Privacy-First Student Support Assistant

A Windows desktop voice assistant for students, built in Python. Sahayak AI (evolved from the earlier "Addix" chatbot) uses a **locally running Llama 3 model** through Ollama, so AI answers are generated on your own computer without sending your questions to a cloud AI service.

> **Project status:** Work in progress for an academic submission at Lovely Professional University. The features below are marked as **Implemented** or **Planned** so this document stays honest about what works today.

---

## Problem Statement

Students often need quick help with study topics, campus information, and time management, but most AI assistants:

- require constant internet access,
- send personal questions to cloud servers,
- know nothing about the student's own institution.

Sahayak AI aims to provide a **campus-aware, privacy-first assistant** that keeps working for its core features when the internet is unavailable, using a local AI model and an institution-approved local knowledge base.

---

## Features

| Feature | Status |
|---|---|
| Voice input with typed-input fallback | Implemented |
| Spoken and printed responses (text-to-speech) | Implemented |
| General conversation with a local Llama 3 model | Implemented |
| Wikipedia search | Implemented |
| Open YouTube, Google, Stack Overflow | Implemented |
| Play local music (first song, random song, playlist) | Implemented |
| Open VS Code | Implemented |
| Email with spoken confirmation before sending | Implemented |
| Logging without credentials | Implemented |
| Mode system (general, study, campus, focus, emergency) | Planned |
| Study mode: explanations, revision summaries | Planned |
| Quiz generation (5 multiple-choice questions) | Planned |
| Campus knowledge base with keyword search | Planned |
| Focus timer (25 minutes or custom, cancellable) | Planned |
| Emergency contact information (display and speak only) | Planned |
| Privacy-status command | Planned |

---

## What Works Offline and What Does Not

This project does **not** claim to be fully offline. Speech recognition currently uses Google's online service.

| Component | Works offline? | Notes |
|---|---|---|
| AI text generation (Ollama + Llama 3) | Yes | Runs on your computer |
| Text-to-speech (pyttsx3 / Windows SAPI) | Yes | Uses Windows voices |
| Typed input | Yes | Fallback when no microphone |
| Local files, timers, music | Yes | No network needed |
| Voice recognition (SpeechRecognition + Google) | **No** | Audio is sent to Google |
| Wikipedia search | **No** | Needs internet |
| Opening websites | **No** | Needs internet |
| Email (Gmail SMTP) | **No** | Needs internet |

To use the assistant completely offline today, use typed input and avoid the internet-dependent commands.

---

## Requirements

- Windows 10 or 11
- Python 3.10 or newer
- [Ollama](https://ollama.com) installed and running
- The Llama 3 model: `ollama pull llama3`
- A microphone (optional, typed input is used if none is found)

## Installation

```bash
# 1. Get the project
cd sahayak_ai

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the local model (once, needs internet)
ollama pull llama3

# 5. Configure optional features
copy .env.example .env
# then edit .env with your own values
```

### requirements.txt

```
pyttsx3
SpeechRecognition
PyAudio
wikipedia-api
python-dotenv
ollama
```

If `PyAudio` fails to install on Windows, try `pip install pipwin` then `pipwin install pyaudio`, or run the assistant with typed input.

### .env.example

```
# All values are optional. A feature without its values is simply disabled.
SAHAYAK_MUSIC_DIR=C:\Users\YourName\Music
SAHAYAK_CODE_PATH=C:\Users\YourName\AppData\Local\Programs\Microsoft VS Code\Code.exe

# Email (use a Gmail App Password, never your real password)
SAHAYAK_EMAIL_ADDRESS=your_address@gmail.com
SAHAYAK_EMAIL_PASSWORD=your_app_password
SAHAYAK_EMAIL_TO=recipient@example.com
```

Older variable names (`music_dir`, `code_path`, `my_email`, `password`, `to_email`) are still accepted for backward compatibility.

---

## Usage

Make sure Ollama is running, then:

```bash
python addix.py
```

### Example commands

| Say | What happens |
|---|---|
| "What is the time" | Speaks the current time |
| "Wikipedia binary search" | Reads a short Wikipedia summary (internet) |
| "Open YouTube" / "Open Google" / "Open Stack Overflow" | Opens the site (internet) |
| "Play music" / "Play a random song" / "Play my playlist" | Plays local audio |
| "Open VS Code" | Launches VS Code |
| "Send email" | Dictate, hear it read back, say "yes" to send |
| "Exit" / "Goodbye" | Closes the assistant |
| Anything else | Answered by the local Llama 3 model |

---

## Privacy and Security

- AI responses are generated locally; questions to the AI model are not sent to a cloud AI provider.
- Voice recognition sends audio to Google. Use typed input if that is unacceptable.
- Credentials are read from `.env`, are never printed, and are never written to the log.
- The log file (`addix.log`) records events and error types only, not what you say.
- Email is sent **only after** you read it back and confirm with "yes".
- The assistant never contacts anyone automatically.
- Do not commit `.env` or `addix.log`. Add both to `.gitignore`.

---

## Project Structure

Current (Stage 1):

```
sahayak_ai/
├── addix.py          # single-file assistant (bug-fixed)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

Planned modular layout:

```
sahayak_ai/
├── main.py            # entry point and main loop
├── config.py          # constants, validation, logging
├── assistant.py       # command classification and modes
├── llm_service.py     # Ollama and shared chat history
├── knowledge_base.py  # local document search
├── study_mode.py      # explanations and quizzes
├── focus_mode.py      # threaded timer
├── emergency_mode.py  # emergency information
├── media_controls.py  # browser, music, VS Code, Wikipedia
├── email_service.py   # confirmation-gated email
├── tests/
└── knowledge_base/    # sample .txt files (demonstration content only)
```

---

## Campus Knowledge Base (Planned)

The campus feature will read `.txt` files from a local `knowledge_base/` folder, find relevant passages by keyword matching, and give only those passages to Llama 3 with an instruction to answer from them alone. If nothing relevant is found, it will reply: *"I could not find that information in the campus knowledge base."*

**Important:** the bundled files will contain fictional **demonstration content**. They are not official LPU information. Institutions or students must supply approved documents for real use.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "I cannot reach the local AI model" | Start Ollama and run `ollama pull llama3` |
| "No microphone found" | Connect a mic and install PyAudio, or continue with typed input |
| "Speech service unreachable" | Google speech needs internet; use typed input |
| Music does not play | Check `SAHAYAK_MUSIC_DIR` exists and contains .mp3, .wav, .m4a or .flac files |
| Email login failed | Use a Gmail App Password and check the address |
| No voice output | Windows text-to-speech voices may be missing; text output still works |

---

## Roadmap

1. Mode system and study/quiz mode
2. Campus knowledge base with unsupported-answer protection
3. Focus timer, emergency information, and privacy status
4. Modular refactor, unit tests, and demo script
5. Future ideas: offline speech recognition (for example Vosk), Markdown documents, multilingual support

---

## Limitations

- Windows only (uses `os.startfile` and Windows SAPI voices).
- Voice input requires internet until an offline recognizer is added.
- Answers from a small local model can be wrong. Verify important information.
- This is a student project, not an emergency service.

---

## Tech Stack

Python, Ollama (Llama 3), pyttsx3, SpeechRecognition, wikipedia-api, smtplib, python-dotenv.

## Author

Your Name, Registration No., Lovely Professional University