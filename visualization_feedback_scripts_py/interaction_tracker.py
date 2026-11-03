"""Code teacher turns using the project's coding prompt."""

import json
import re

from llm_client import call_openai
from prompts import CODING_PROMPT


CODE_LABELS = {
    "A1": "Context information sharing",
    "A2": "Design request / task initiation",
    "B1": "Request feedback",
    "B2": "Follow-up probing",
    "B3": "Challenging",
    "B4": "Evaluate GenAI feedback",
    "B5": "Justification",
    "C1": "Regulation for collaboration",
    "D2": "Off-task",
}


def _parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("The coding model did not return valid JSON.")
        return json.loads(match.group(0))


def code_interaction(conversation_history, api_key=None):
    """Return per-teacher-turn codes and normalized code frequencies."""
    teacher_turns = [
        {"turn": index, "text": msg.get("content", "")}
        for index, msg in enumerate(conversation_history, start=1)
        if msg.get("role") == "user"
    ]
    raw = call_openai(
        system_prompt=CODING_PROMPT,
        user_input=json.dumps(teacher_turns, ensure_ascii=False, indent=2),
        api_key=api_key,
    )
    result = _parse_json(raw)
    turns = result.get("turns", [])
    if not isinstance(turns, list):
        turns = []
    expected_turns = {item["turn"] for item in teacher_turns}
    counts = {code: 0 for code in CODE_LABELS}
    normalized_turns = []
    seen_turns = set()
    for item in turns:
        if not isinstance(item, dict) or item.get("turn") not in expected_turns:
            continue
        turn_number = item["turn"]
        if turn_number in seen_turns:
            continue
        seen_turns.add(turn_number)
        codes = item.get("codes", [])
        if not isinstance(codes, list):
            codes = []
        codes = list(dict.fromkeys(code for code in codes if code in CODE_LABELS))
        for code in codes:
            counts[code] += 1
        normalized_turns.append({
            "turn": turn_number,
            "codes": codes,
            "evidence": str(item.get("evidence", "")),
        })
    for item in teacher_turns:
        if item["turn"] not in seen_turns:
            normalized_turns.append({"turn": item["turn"], "codes": [], "evidence": ""})
    normalized_turns.sort(key=lambda item: item["turn"])
    return {
        "turns": normalized_turns,
        "code_counts": counts,
        "summary": str(result.get("summary", "")),
    }
