import time
from pathlib import Path

import matplotlib.pyplot as plt


def draw_pie_chart(data, title="Interaction Behaviour Distribution"):
    """Save a pie chart and return its path for Streamlit to display."""
    data = {key: value for key, value in data.items() if value > 0}
    if not data:
        return None

    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"pie_chart_{int(time.time() * 1000)}.png"

    labels = [label.replace("_", " ") for label in data]
    values = list(data.values())
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title(title, pad=16)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)
