"""Анализ событий Unity из ЛР3–4. Используется только стандартная библиотека."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "simulation_log_1795012796.csv"
FIELDS = [
    "player_id", "session_id", "timestamp", "event_type", "object_id",
    "x_position", "y_position", "reaction_time", "score"
]


def analyze(csv_path: Path) -> tuple[dict, list[dict]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != FIELDS:
            raise ValueError("Unexpected CSV schema: " + str(reader.fieldnames))
        rows = list(reader)

    if not rows:
        raise ValueError("Empty event log")
    if any(row["event_type"] not in {"hit", "miss", "move"} for row in rows):
        raise ValueError("Unexpected event type")
    if any(not row["reaction_time"] for row in rows if row["event_type"] == "hit"):
        raise ValueError("Hit event without reaction_time")
    if any(row["reaction_time"] for row in rows if row["event_type"] != "hit"):
        raise ValueError("Reaction time is only defined for hit events")

    counts = Counter(row["event_type"] for row in rows)
    hit_rows = [row for row in rows if row["event_type"] == "hit"]
    values = [float(row["reaction_time"]) for row in hit_rows]
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = [row for row in hit_rows
                if float(row["reaction_time"]) < lower or float(row["reaction_time"]) > upper]
    clicks = counts["hit"] + counts["miss"]

    result = {
        "source": csv_path.name,
        "source_type": "real single-session Unity log",
        "players": len({row["player_id"] for row in rows}),
        "sessions": len({row["session_id"] for row in rows}),
        "events_total": len(rows),
        "hits": counts["hit"],
        "misses": counts["miss"],
        "moves": counts["move"],
        "click_accuracy_percent": round(100 * counts["hit"] / clicks, 3) if clicks else None,
        "reaction_time_unit": "seconds",
        "reaction_samples": len(values),
        "mean_seconds": round(statistics.mean(values), 3),
        "median_seconds": round(statistics.median(values), 3),
        "std_seconds_sample": round(statistics.stdev(values), 3),
        "q1_seconds": round(q1, 5),
        "q3_seconds": round(q3, 5),
        "iqr_upper_seconds": round(upper, 5),
        "outlier_count": len(outliers),
        "outlier_rule": "Tukey 1.5 * IQR, inclusive quartiles",
    }
    return result, outliers


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce analysis of one Unity session")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    result, outliers = analyze(args.input)

    (ROOT / "results").mkdir(exist_ok=True)
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (processed / "outliers.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(outliers)
    with (processed / "event_counts.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["event_type", "count"])
        for typ in ("hit", "miss", "move"):
            writer.writerow([typ, result[{"hit": "hits", "miss": "misses", "move": "moves"}[typ]]])
    with (processed / "player_statistics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "hits", "mean_seconds", "median_seconds"])
        # This sample contains one player, per the source log.
        writer.writerow(["1", result["hits"], result["mean_seconds"], result["median_seconds"]])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
