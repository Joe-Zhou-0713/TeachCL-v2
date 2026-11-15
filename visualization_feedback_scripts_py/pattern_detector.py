"""Classify the dominant teacher–AI interaction pattern from coded evidence."""

import json
import re

from llm_client import call_openai
from prompts import PATTERN_DETECTION_PROMPT


PATTERNS = {
    "passive_acceptance": "Passive acceptance and rapid closure",
    "contextual_initiation": "Strong contextual design initiation",
    "critical_evaluation": "Critical evaluation of AI suggestions",
    "reflective_refinement": "Reflective refinement",
    "over_reliance": "Over-reliance on AI",
    "balanced_codesign": "Balanced human–AI co-design",
    "minimal_reasoning": "Minimal instructional reasoning",
    "alternative_exploration": "Iterative exploration of alternatives",
    "insufficient_evidence": "Insufficient evidence",
}


def _parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("The pattern detector did not return valid JSON.")
        return json.loads(match.group(0))


def detect_interaction_pattern(conversation_history, coding_result=None, api_key=None):
    payload = {
        "conversation": [
            {"role": m.get("role"), "content": m.get("content", "")}
            for m in conversation_history
            if m.get("role") in {"user", "assistant"}
        ],
        "coding_result": coding_result or {},
    }
    raw = call_openai(
        system_prompt=PATTERN_DETECTION_PROMPT,
        user_input=json.dumps(payload, ensure_ascii=False, indent=2),
        api_key=api_key,
    )
    result = _parse_json(raw)
    pattern = result.get("pattern", "insufficient_evidence")
    if pattern not in PATTERNS:
        pattern = "insufficient_evidence"
    try:
        confidence = float(result.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "pattern": pattern,
        "pattern_label": PATTERNS[pattern],
        "confidence": max(0.0, min(1.0, confidence)),
        "evidence": str(result.get("evidence", "")),
    }
