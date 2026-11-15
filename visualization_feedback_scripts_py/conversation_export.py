"""Build research records for local and cloud storage."""

from datetime import datetime, timezone
import json
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_conversation_record(messages, participant_id, session_id, created_at, status="in_progress"):
    """Return the full transcript as JSON-ready data for the participant export."""
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
            "speaker": "AI" if role == "assistant" else "user",
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
            f"[{message.get('timestamp', '')}] {message.get('speaker', message.get('role', '').upper())} "
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


def build_session_xlsx(record):
    """Create a message-level Excel sheet with session analysis alongside each turn."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "实验记录"
    headers = ["被试ID", "AI/user", "对话内容", "对应code", "对应interaction pattern", "feedback文本", "时间戳"]
    sheet.append(headers)

    coding_by_turn = {}
    coding = record.get("coding") or {}
    for item in coding.get("turns", []):
        coding_by_turn[str(item.get("turn"))] = ", ".join(item.get("codes") or [])

    pattern_data = record.get("pattern") or {}
    pattern = pattern_data.get("label") or pattern_data.get("name") or ""
    feedback = record.get("feedback") or ""

    def excel_literal(value):
        text = str(value or "")
        return "'" + text if text.startswith(("=", "+", "-", "@")) else text

    for message in record.get("messages", []):
        code = coding_by_turn.get(str(message.get("turn_number")), "") if message.get("role") == "user" else ""
        sheet.append([
            excel_literal(record.get("participant_id", "")),
            excel_literal("user" if message.get("role") == "user" else "AI"),
            excel_literal(message.get("content", "")),
            excel_literal(code),
            excel_literal(pattern),
            excel_literal(feedback),
            excel_literal(message.get("timestamp", "")),
        ])

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    widths = {"A": 14, "B": 12, "C": 60, "D": 24, "E": 30, "F": 60, "G": 30}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="244062")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    sheet.row_dimensions[1].height = 30
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    if sheet.max_row > 1:
        table = Table(displayName="ConversationRecords", ref=sheet.dimensions)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
            showRowStripes=True, showColumnStripes=False,
        )
        sheet.add_table(table)

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
