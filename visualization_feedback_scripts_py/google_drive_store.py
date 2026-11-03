"""Send research JSON to a private Google Apps Script Drive bridge."""

import requests
import streamlit as st


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


def upload_json_record(config, kind, record, session_id):
    """Upload one private record; the script writes it to the matching folder."""
    if kind not in {"conversation", "analysis"}:
        raise ValueError(f"Unsupported research record type: {kind}")

    response = requests.post(
        config["web_app_url"],
        json={
            "token": config["archive_token"],
            "kind": kind,
            "session_id": session_id,
            "record": record,
        },
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
