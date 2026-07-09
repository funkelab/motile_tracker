"""Compare two pytest-benchmark JSON files and produce a markdown table.

Usage:
    python benchmark_pr.py <old.json> <new.json> <output.md> [header]

Exits with code 1 if any benchmark regresses by more than REGRESSION_THRESHOLD.
"""

import json
import os
import sys

import pandas as pd

REGRESSION_THRESHOLD = 50  # percent


def load_stats(path):
    with open(path) as f:
        data = json.load(f)

    commit = data["commit_info"]["id"]

    rows = []
    for d in data["benchmarks"]:
        rows.append({"Benchmark": d["name"], "mean": d["stats"]["mean"]})

    return commit, pd.DataFrame(rows)


def _write(out_file, report):
    with open(out_file, "w") as f:
        f.write(report)
    print(report)  # noqa: T201


def make_report(old_path, new_path, out_file, header=None):
    new_commit, new_df = load_stats(new_path)

    # No baseline available (e.g. the first PR introducing benchmarks, or a run on
    # a base commit that predates the suite). Report HEAD-only numbers and pass.
    if not os.path.exists(old_path) or os.path.getsize(old_path) == 0:
        df = new_df.rename(columns={"mean": f"Mean (s) HEAD {new_commit}"})
        df[f"Mean (s) HEAD {new_commit}"] = df[f"Mean (s) HEAD {new_commit}"].map(
            "{:.5f}".format
        )
        report = df.to_markdown(index=False)
        note = "_No baseline found; showing HEAD results only (no comparison)._"
        report = f"{note}\n\n{report}"
        if header:
            report = f"## {header}\n\n{report}"
        _write(out_file, report)
        return

    old_commit, old_df = load_stats(old_path)

    # Merge on benchmark name
    df = old_df.merge(new_df, on="Benchmark", suffixes=("_old", "_new"))
    old = (old_commit,)
    new = (new_commit,)

    pct_change = 100 * (df["mean_new"] - df["mean_old"]) / df["mean_old"]
    df["Percent Change"] = pct_change.map("{:+.2f}".format)

    # Format runtimes
    df["mean_old"] = df["mean_old"].map("{:.5f}".format)
    df["mean_new"] = df["mean_new"].map("{:.5f}".format)

    # Change column names to commit ids
    df = df.rename(
        columns={
            "mean_new": f"Mean (s) HEAD {new[0]}",
            "mean_old": f"Mean (s) BASE {old[0]}",
        }
    )

    report = df.to_markdown(index=False)
    if header:
        report = f"## {header}\n\n{report}"

    with open(out_file, "w") as f:
        f.write(report)

    # Print report to logs
    print(report)  # noqa: T201

    # Fail if any benchmark regressed beyond threshold
    if (pct_change > REGRESSION_THRESHOLD).any():
        print(  # noqa: T201
            f"\nFAILED: Regression exceeds {REGRESSION_THRESHOLD}% threshold"
        )
        sys.exit(1)


if __name__ == "__main__":
    header = sys.argv[4] if len(sys.argv) > 4 else None
    make_report(sys.argv[1], sys.argv[2], sys.argv[3], header)
