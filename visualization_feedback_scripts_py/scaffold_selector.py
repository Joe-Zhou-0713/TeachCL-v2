"""Prepare interaction-code counts for the app's radar chart."""

from interaction_tracker import CODE_LABELS


def select_scaffold(coding_result):
    """Return chart data in a stable order, filling missing counts with zero."""
    counts = (coding_result or {}).get("code_counts", {})
    return {
        "visualization_type": "radar",
        "data": {code: counts.get(code, 0) for code in CODE_LABELS},
    }
