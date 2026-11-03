"""Build privacy-conscious research records without writing them locally."""

from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_conversation_record(messages, participant_id, session_id, created_at, status="in_progress"):
    """Return the full transcript as JSON-ready data; persistence is handled by Drive."""
    normalized = []
    turn = 0
    for index, message in enumerate(messages, start=1):
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue
        if role == "user":
            turn += 1
        normalized.append({
            "role": role,
            "content": str(message.get("content", "")),
            "timestamp": message.get("timestamp") or utc_now(),
            "turn_number": turn,
            "message_index": index,
        })
    return {
        "record_type": "conversation",
        "participant_id": participant_id,
        "session_id": session_id,
        "created_at": created_at,
        "updated_at": utc_now(),
        "status": status,
        "messages": normalized,
    }


def build_analysis_record(participant_id, session_id, conversation_created_at):
    """Create an explicit pending analysis record without inventing results."""
    return {
        "record_type": "analysis",
        "participant_id": participant_id,
        "session_id": session_id,
        "conversation_created_at": conversation_created_at,
        "analysis_timestamp": None,
        "analysis_status": "pending",
        "code_status": "pending",
        "interaction_codes": None,
        "pattern_status": "pending",
        "pattern": None,
        "evidence": None,
        "feedback_status": "pending",
        "feedback_generated": False,
        "feedback_text": None,
        "feedback_features": None,
        "visualization": None,
    }
