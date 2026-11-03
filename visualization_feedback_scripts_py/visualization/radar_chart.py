import time
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


LABELS = {
    "task_definition": "Task\ndefinition",
    "planning_and_control": "Planning &\ncontrol",
    "monitoring": "Monitoring",
    "evaluation_and_justification": "Evaluation &\njustification",
    "metacognitive_regulation": "Metacognitive\nregulation",
}


def _closed_values(profile, labels):
    values = [profile.get(label, 0) for label in labels]
    return values + values[:1]


def draw_radar_chart(profile_data, title="SRL Process Profile"):
    """Draw current SRL indicators against a transparent design reference."""
    if "current" in profile_data:
        current = profile_data.get("current", {})
        reference = profile_data.get("reference", {})
    else:
        current = profile_data
        reference = None

    labels = list(current.keys()) or list(LABELS)
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    closed_angles = angles + angles[:1]

    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"radar_chart_{int(time.time() * 1000)}.png"

    fig, ax = plt.subplots(figsize=(7.2, 6.4), subplot_kw={"polar": True})
    ax.plot(closed_angles, _closed_values(current, labels), linewidth=2.4, color="#2F6B9A", label="Current interaction")
    ax.fill(closed_angles, _closed_values(current, labels), color="#2F6B9A", alpha=0.20)

    if reference:
        ax.plot(
            closed_angles,
            _closed_values(reference, labels),
            linewidth=2,
            linestyle="--",
            color="#D97706",
            label="Prototype reference",
        )

    ax.set_xticks(angles)
    ax.set_xticklabels([LABELS.get(label, label.replace("_", " ").title()) for label in labels])
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_title(title, size=14, pad=24)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def draw_interaction_radar_chart(code_counts, output_dir=None):
    """Plot the frequency of each collaboration code for one conversation."""
    labels = list(code_counts)
    values = [max(0, float(code_counts.get(code, 0) or 0)) for code in labels]
    labels = [f"{code} · {code_counts_label(code)}" for code in labels]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    closed_angles = angles + angles[:1]
    closed_values = values + values[:1]
    target = Path(output_dir) if output_dir else Path(__file__).resolve().parents[1] / "outputs" / "visualizations"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"interaction_radar_{int(time.time() * 1000)}.png"
    fig, ax = plt.subplots(figsize=(8.4, 7.2), subplot_kw={"polar": True})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, max(1, max(values, default=0)) * 1.2)
    ax.set_yticks(range(1, int(max(values, default=0)) + 1))
    ax.plot(closed_angles, closed_values, color="#2563eb", linewidth=2.2, marker="o")
    ax.fill(closed_angles, closed_values, color="#2563eb", alpha=0.2)
    ax.set_title("Teacher interaction coding frequency", pad=28, fontsize=15, fontweight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def render_interaction_radar_chart(code_counts):
    """Render the participant-facing radar in memory; never writes a local file."""
    labels = list(code_counts)
    values = [max(0, float(code_counts.get(code, 0) or 0)) for code in labels]
    tick_labels = [f"{code} · {code_counts_label(code)}" for code in labels]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    fig, ax = plt.subplots(figsize=(8.4, 7.2), subplot_kw={"polar": True})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(tick_labels, fontsize=8)
    ax.set_ylim(0, max(1, max(values, default=0)) * 1.2)
    ax.set_yticks(range(1, int(max(values, default=0)) + 1))
    ax.plot(angles + angles[:1], values + values[:1], color="#2563eb", linewidth=2.2, marker="o")
    ax.fill(angles + angles[:1], values + values[:1], color="#2563eb", alpha=0.2)
    ax.set_title("Teacher interaction coding frequency", pad=28, fontsize=15, fontweight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def code_counts_label(code):
    names = {
        "A1": "Context", "A2": "Design request", "B1": "Feedback request",
        "B2": "Probe", "B3": "Challenge", "B4": "Evaluate AI",
        "B5": "Rationale", "C1": "Regulate", "D2": "Off-task",
    }
    return names.get(code, code)
