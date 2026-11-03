"""Transparent SRL proxy measures used by the TeachCL prototype.

These scores are behavioural indicators, not diagnostic measures of a teacher's
internal cognition. They operationalise selected Winne and Hadwin SRL processes
from the observable teacher turns coded by the pattern detector.
"""


SRL_DIMENSIONS = (
    "task_definition",
    "planning_and_control",
    "monitoring",
    "evaluation_and_justification",
    "metacognitive_regulation",
)


def _count(counts, code):
    value = counts.get(code, 0)
    return value if isinstance(value, (int, float)) else 0


def current_profile(behavior_counts):
    """Derive a 0--5 SRL process profile from observable coded behaviours."""
    counts = behavior_counts or {}
    profile = {
        # Phase 1: task definition / perceived task conditions.
        "task_definition": _count(counts, "A1_context_sharing"),
        # A request alone does not indicate high-quality planning. Explicit
        # regulation (C1) is weighted so that control remains learner-driven.
        "planning_and_control": min(_count(counts, "A2_design_request"), 2)
        + 2 * _count(counts, "C1_metacognitive_regulation"),
        # Ongoing checks of the AI's response against the teacher's concerns.
        "monitoring": _count(counts, "B2_follow_up_question")
        + _count(counts, "B3_challenge"),
        # Evaluation (B4) and reasons/justifications (B5) make standards visible.
        "evaluation_and_justification": _count(counts, "B4_evaluation")
        + _count(counts, "B5_explanation"),
        # Explicit reflection on plans, criteria, uncertainty, or next actions.
        "metacognitive_regulation": _count(counts, "C1_metacognitive_regulation"),
    }
    return {dimension: max(0, min(5, value)) for dimension, value in profile.items()}


def reference_profile(pattern):
    """Return a design reference, not an empirical expert norm."""
    balanced = {dimension: 4 for dimension in SRL_DIMENSIONS}
    if pattern == "goal_misalignment":
        # The aim is productive monitoring, not continually escalating challenge.
        balanced["monitoring"] = 3
    return balanced


def build_srl_profile(pattern, behavior_counts):
    return {
        "current": current_profile(behavior_counts),
        "reference": reference_profile(pattern),
    }
