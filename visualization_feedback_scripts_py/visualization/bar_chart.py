import time
from pathlib import Path

import matplotlib.pyplot as plt


def draw_bar_chart(data, title="Interaction Pattern Frequency"):
    """Save a bar chart and return its path for Streamlit to display."""
    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"bar_chart_{int(time.time() * 1000)}.png"

    labels = [label.replace("_", " ") for label in data]
    values = list(data.values())
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values, color="#4C78A8")
    ax.set_title(title, pad=16)
    ax.set_ylabel("Frequency")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)
