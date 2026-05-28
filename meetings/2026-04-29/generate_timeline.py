"""Generate a Gantt chart from timeline.yaml using matplotlib."""

from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import yaml


def load_timeline(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def generate_chart(data: dict, output_path: Path) -> None:
    people = data["people"]
    milestones = data.get("milestones", [])
    sections = data["sections"]

    # Build flat list of rows (tasks + section headers), bottom to top
    rows: list[dict] = []
    for section in reversed(sections):
        for task in reversed(section["tasks"]):
            rows.append(
                {
                    "type": "task",
                    "label": task["name"],
                    "start": datetime.strptime(str(task["start"]), "%Y-%m-%d"),
                    "end": datetime.strptime(str(task["end"]), "%Y-%m-%d"),
                    "color": people[task["person"]]["color"],
                    "person": task["person"],
                }
            )
        rows.append({"type": "section", "label": section["name"]})

    # Figure setup
    fig_height = max(4, len(rows) * 0.45 + 1.5)
    fig, ax = plt.subplots(figsize=(14, fig_height))

    y_pos = 0
    y_ticks = []
    y_labels = []

    for row in rows:
        if row["type"] == "section":
            y_ticks.append(y_pos)
            y_labels.append(row["label"])
            ax.text(
                ax.get_xlim()[0]
                if ax.get_xlim()[0] != 0.0
                else mdates.date2num(datetime(2026, 4, 20)),
                y_pos,
                "",
                fontsize=11,
                fontweight="bold",
                va="center",
            )
            y_pos += 1
        else:
            start_num = mdates.date2num(row["start"])
            end_num = mdates.date2num(row["end"])
            duration = end_num - start_num
            ax.barh(
                y_pos,
                duration,
                left=start_num,
                height=0.6,
                color=row["color"],
                edgecolor="white",
                linewidth=0.5,
                alpha=0.85,
            )
            y_ticks.append(y_pos)
            y_labels.append(row["label"])
            y_pos += 1

    # Y-axis labels
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=9)

    # Bold section headers
    for i, row in enumerate(rows):
        if row["type"] == "section":
            label = ax.get_yticklabels()[i]
            label.set_fontweight("bold")
            label.set_fontsize(11)

    # X-axis date formatting
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

    # Set x limits with padding
    all_dates = []
    for row in rows:
        if row["type"] == "task":
            all_dates.extend([row["start"], row["end"]])
    for ms in milestones:
        all_dates.append(datetime.strptime(str(ms["date"]), "%Y-%m-%d"))

    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        padding = (max_date - min_date).days * 0.03
        ax.set_xlim(
            mdates.date2num(min_date) - padding,
            mdates.date2num(max_date) + padding,
        )

    # Milestones as vertical lines
    for ms in milestones:
        ms_date = datetime.strptime(str(ms["date"]), "%Y-%m-%d")
        ax.axvline(
            mdates.date2num(ms_date),
            color="#cc0000",
            linestyle="--",
            linewidth=1.2,
            alpha=0.7,
            zorder=0,
        )
        ax.text(
            mdates.date2num(ms_date),
            y_pos + 0.3,
            f"  {ms['name']}",
            fontsize=8,
            color="#cc0000",
            rotation=0,
            va="bottom",
            ha="center",
        )

    # Grid
    ax.grid(axis="x", alpha=0.3, which="major")
    ax.set_axisbelow(True)

    # Legend from people
    legend_patches = [
        mpatches.Patch(color=info["color"], label=name) for name, info in people.items()
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        fontsize=9,
        framealpha=0.9,
    )

    # Title
    ax.set_title(data.get("title", "Timeline"), fontsize=14, fontweight="bold", pad=15)

    # Style
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    plt.tight_layout()

    # Save
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    print(f"Saved {output_path} and {svg_path}")
    plt.close(fig)


def main():
    import sys

    yaml_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).parent / "timeline.yaml"
    )
    output_path = yaml_path.with_suffix(".png")
    data = load_timeline(yaml_path)
    generate_chart(data, output_path)


if __name__ == "__main__":
    main()
