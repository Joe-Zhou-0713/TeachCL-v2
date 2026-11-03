import matplotlib.pyplot as plt
from pathlib import Path
import time


def draw_stacked_bar_chart(stage_counts, title="Goal Misalignment Across Dialogue Stages"):
    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)

    path = output_dir / f"stacked_bar_chart_{int(time.time() * 1000)}.png"

    stages = list(stage_counts.keys())

    all_codes = set()
    for counts in stage_counts.values():
        all_codes.update(counts.keys())

    all_codes = sorted(list(all_codes))

    bottoms = [0] * len(stages)

    plt.figure(figsize=(9, 5))

    for code in all_codes:
        values = [stage_counts[stage].get(code, 0) for stage in stages]
        plt.bar(stages, values, bottom=bottoms, label=code)
        bottoms = [bottoms[i] + values[i] for i in range(len(values))]

    plt.title(title)
    plt.xlabel("Dialogue Stage")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()

    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()

    return str(path)
