"""Send research records to a private Google Apps Script Drive bridge."""

import requests
import streamlit as st


_fallback_participant_counter = 0


def load_drive_config():
    """Read the bridge URL and shared secret from Streamlit secrets."""
    try:
        settings = st.secrets["google_drive"]
    except (KeyError, FileNotFoundError):
        return None

    web_app_url = str(settings.get("web_app_url", "")).strip()
    archive_token = str(settings.get("archive_token", "")).strip()
    if not web_app_url or not archive_token:
        raise ValueError("Google Drive bridge URL/token is missing from Streamlit secrets.")
    return {"web_app_url": web_app_url, "archive_token": archive_token}


def _post(config, payload):
    response = requests.post(
        config["web_app_url"],
        json={"token": config["archive_token"], **payload},
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError as error:
        raise RuntimeError("Google Drive bridge returned an unreadable response.") from error
    if not result.get("ok"):
        raise RuntimeError("Google Drive bridge rejected the research record.")
    return result


def allocate_participant_id(config):
    """Ask the Drive bridge for the next persistent participant number."""
    global _fallback_participant_counter
    if config is None:
        _fallback_participant_counter += 1
        return f"{_fallback_participant_counter:02d}"
    return _post(config, {"action": "allocate_participant_id"})["participant_id"]


def upload_record(config, kind, record, session_id):
    """Upload a text or feedback record; the bridge stores it in Drive."""
    if kind not in {"content", "analysis", "feedback", "sheet"}:
        raise ValueError(f"Unsupported research record type: {kind}")
    return _post(config, {"kind": kind, "session_id": session_id, "record": record})
