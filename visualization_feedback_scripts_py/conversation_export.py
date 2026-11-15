"""Build research records for local and cloud storage."""

from datetime import datetime, timezone
import json


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
            "message_status": "partial" if message.get("partial") else "complete",
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


def build_session_record(conversation, analysis):
    """Combine completed conversation and analysis into one archival record."""
    return {
        "record_type": "completed_session",
        "participant_id": conversation["participant_id"],
        "session_id": conversation["session_id"],
        "created_at": conversation["created_at"],
        "completed_at": utc_now(),
        "status": "completed",
        "messages": conversation["messages"],
        "coding": analysis.get("interaction_codes"),
        "pattern": analysis.get("pattern"),
        "evidence": analysis.get("evidence"),
        "feedback": analysis.get("feedback_text"),
        "visualization": analysis.get("visualization"),
    }


def format_session_text(record):
    """Render a readable transcript and analysis summary for a local TXT file."""
    lines = [
        f"ID: {record['participant_id']}",
        f"Session: {record['session_id']}",
        f"Started: {record['created_at']}",
        f"Completed: {record['completed_at']}",
        "",
        "Conversation",
        "------------",
    ]
    for message in record.get("messages", []):
        lines.extend([
            f"[{message.get('timestamp', '')}] {message.get('role', '').upper()} "
            f"(turn {message.get('turn_number', '')})",
            message.get("content", ""),
            "",
        ])
    lines.extend([
        "Coding",
        "------",
        json.dumps(record.get("coding"), ensure_ascii=False, indent=2),
        "",
        "Pattern",
        "-------",
        json.dumps(record.get("pattern"), ensure_ascii=False, indent=2),
        "",
        "Feedback",
        "--------",
        record.get("feedback") or "",
        "",
        "Visualization data",
        "------------------",
        json.dumps(record.get("visualization"), ensure_ascii=False, indent=2),
        "",
    ])
    return "\n".join(lines)
