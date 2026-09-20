"""Sahayak email (Gmail SMTP, needs internet). Sends only after confirmation."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from config import Settings
from voice_io import VoiceIO

log = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_TIMEOUT_SECONDS = 15


def send_email(voice: VoiceIO, settings: Settings) -> None:
    """Dictate an email, read it back, and send only after a clear 'yes'."""
    if not settings.email_configured:
        voice.speak("Email is not configured. Please set the email values in the .env file.")
        return

    voice.speak("What is the content?")
    content = voice.listen()
    if not content:
        voice.speak("I didn't catch that. Email cancelled.")
        return

    if not voice.confirm(f"I heard: {content}. Say yes to send it, or anything else to cancel."):
        voice.speak("Email cancelled. Nothing was sent.")
        return

    message = MIMEText(content)
    message["Subject"] = "Automated Message from Sahayak"
    message["From"] = settings.email_address
    message["To"] = settings.email_to
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.login(settings.email_address, settings.email_password)
            server.sendmail(settings.email_address, settings.email_to, message.as_string())
    except smtplib.SMTPAuthenticationError:
        log.error("Email login failed")
        voice.speak("Email login failed. Check your address and app password.")
        return
    except (smtplib.SMTPException, OSError) as err:
        log.error("Email error: %s", type(err).__name__)
        voice.speak("The email cannot be sent right now. Check your internet connection.")
        return
    log.info("Email sent")
    voice.speak("Email has been sent.")