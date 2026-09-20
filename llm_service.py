"""Sahayak local LLM service (Ollama + Llama 3). Runs on this computer."""

from __future__ import annotations

import logging

from config import (
    MAX_HISTORY_MESSAGES,
    MAX_LLM_TOKENS,
    OLLAMA_MODEL,
    SYSTEM_PROMPT,
)

try:
    import httpx
    import ollama
    OLLAMA_ERRORS: tuple = (ollama.ResponseError, ConnectionError, OSError, httpx.HTTPError)
except ImportError:          # optional: app starts, AI replies say it is unavailable
    ollama = None
    OLLAMA_ERRORS = (ConnectionError, OSError)

log = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = (
    "I cannot reach the local AI model. "
    "Make sure Ollama is running and llama3 is installed."
)


class LLMService:
    """Owns the single shared chat history."""

    def __init__(self, model: str = OLLAMA_MODEL) -> None:
        self.model = model
        self.history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def warm_up(self) -> bool:
        """Load the model into memory. Uses a throwaway call, not the history."""
        if ollama is None:
            log.error("ollama package is not installed")
            return False
        try:
            ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                options={"num_predict": 1},
            )
            return True
        except OLLAMA_ERRORS as err:
            log.error("Ollama warm-up failed: %s", type(err).__name__)
            return False

    def ask(self, prompt: str) -> str:
        """Send a prompt to the local model and return a short reply."""
        prompt = prompt.strip()
        if not prompt:
            return "Please say or type something."
        if ollama is None:
            return UNAVAILABLE_MESSAGE

        self.history.append({"role": "user", "content": prompt})
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.history,
                options={"num_predict": MAX_LLM_TOKENS, "temperature": 0.5},
            )
            reply = response["message"]["content"].strip()
        except OLLAMA_ERRORS as err:
            self.history.pop()          # don't keep a question with no answer
            log.error("Ollama error: %s", type(err).__name__)
            return UNAVAILABLE_MESSAGE
        except (KeyError, TypeError) as err:
            self.history.pop()
            log.error("Unexpected Ollama response: %s", type(err).__name__)
            return "The local AI gave an unexpected answer. Please try again."

        self.history.append({"role": "assistant", "content": reply})
        self._trim_history()
        return reply or "I do not have an answer for that."

    def _trim_history(self) -> None:
        """Keep the system prompt plus the most recent messages only."""
        if len(self.history) > MAX_HISTORY_MESSAGES:
            keep = MAX_HISTORY_MESSAGES - 1
            self.history = [self.history[0]] + self.history[-keep:]