"""Prepare transparent interaction evidence for the app and radar chart."""

from interaction_tracker import CODE_LABELS


TACTICS = {
    "passive_acceptance": "Before using a suggestion, name one criterion you will use to judge whether it fits your learners.",
    "contextual_initiation": "For one major design choice, explain which learner need or classroom constraint shaped it most.",
    "critical_evaluation": "For the next revision, state what classroom evidence would show that the chosen approach works.",
    "reflective_refinement": "Connect one important revision to the learning process it is intended to support.",
    "over_reliance": "Choose one design decision to make independently, then ask AI to help examine its trade-offs.",
    "balanced_codesign": "Keep using your instructional criteria to compare suggestions and make the final design decisions.",
    "minimal_reasoning": "State how one design choice supports a specific learning goal or learner need.",
    "alternative_exploration": "Make the criteria behind your final choice explicit and compare each option against them.",
    "insufficient_evidence": "As you continue, note why you accept, revise, or reject one AI suggestion in relation to your learners and goals.",
}


def select_scaffold(coding_result, pattern_result):
    counts = coding_result.get("code_counts", {})
    return {
        "pattern": pattern_result.get("pattern", "insufficient_evidence"),
        "pattern_label": pattern_result.get("pattern_label", "Insufficient evidence"),
        "visualization_type": "radar",
        "data": {code: counts.get(code, 0) for code in CODE_LABELS},
        "reflection_prompt": pattern_result.get("reflection_prompt", ""),
        "actionable_tactic": TACTICS.get(pattern_result.get("pattern"), TACTICS["insufficient_evidence"]),
        "theory_note": "The chart shows coded teacher-turn frequencies in this conversation. Codes may co-occur on one turn; frequencies are descriptive evidence, not a rating of teacher ability.",
    }
