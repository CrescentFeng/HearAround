#!/usr/bin/env python3
"""Evaluate the frozen HearAround mapping/policy on the independent holdout."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import numpy as np

from app.audio import decode_audio
from app.config import CONFIG_DIR
from app.policy import PolicyCatalog
from app.yamnet import YamnetClassifier


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "eval/holdout_manifest.csv"
AUDIO_DIR = ROOT / "eval/holdout_audio"
RESULTS = ROOT / "eval/holdout_results.csv"
METRICS = ROOT / "eval/holdout_metrics.json"
FAILURES = ROOT / "eval/HOLDOUT_FAILURES.md"


def per_class_metrics(labels: list[str], rows: list[dict]) -> dict:
    report = {}
    f1_values = []
    for label in labels:
        tp = sum(label in row["expected"] and label in row["predicted"] for row in rows)
        fp = sum(label not in row["expected"] and label in row["predicted"] for row in rows)
        fn = sum(label in row["expected"] and label not in row["predicted"] for row in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_values.append(f1)
        report[label] = {
            "support": sum(label in row["expected"] for row in rows),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    report["macro_f1"] = round(mean(f1_values), 4)
    return report


def write_failures(rows: list[dict]) -> None:
    failures = [row for row in rows if not row["exact_match"]]
    lines = [
        "# HearAround holdout failure review",
        "",
        "Generated with the policy frozen before holdout collection. No threshold was changed after seeing these results.",
        "",
        "| Clip | Failure | Expected | Predicted | Top YAMNet candidate | Source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in failures:
        if not row["expected"]:
            kind = "false positive"
        elif not row["predicted"]:
            kind = "false negative"
        else:
            kind = "wrong or extra class"
        lines.append(
            f"| `{row['clip_id']}` | {kind} | `{','.join(sorted(row['expected'])) or 'none'}` | "
            f"`{','.join(sorted(row['predicted'])) or 'none'}` | {row['top_label']} ({row['top_score']:.3f}) | "
            f"[source]({row['source_url']}) |"
        )
    if not failures:
        lines.extend(["", "No exact-match failures in this small holdout."])
    lines.extend([
        "",
        "> This small license-cleared set is a hackathon validation set, not a population-level benchmark, medical claim, or safety certification.",
    ])
    FAILURES.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit("Run eval/collect_holdout.py first.")
    catalog = PolicyCatalog(CONFIG_DIR / "audioset_to_product.yaml", CONFIG_DIR / "alert_policy.yaml")
    classifier = YamnetClassifier()
    classifier.load()
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    rows = []
    latencies = []
    for item in manifest:
        waveform, _ = decode_audio((AUDIO_DIR / f"{item['clip_id']}.wav").read_bytes())
        started = perf_counter()
        scores, class_names, model_ms = classifier.classify(waveform)
        aggregated, top_candidates = catalog.aggregate(scores, class_names)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        latencies.append(latency_ms)
        predicted = {event["key"] for event in aggregated if event["eligible"]}
        expected = set() if item["expected_label"] == "none" else set(item["expected_label"].split("|"))
        row = {
            "clip_id": item["clip_id"],
            "source_url": item["source_url"],
            "expected": expected,
            "predicted": predicted,
            "top_label": top_candidates[0].label if top_candidates else "",
            "top_score": top_candidates[0].score if top_candidates else 0.0,
            "model_ms": model_ms,
            "latency_ms": latency_ms,
            "exact_match": expected == predicted,
            "event_scores": ";".join(
                f"{event['key']}={event['score']:.4f}:{event['hits']}/{event['windows']}"
                for event in aggregated
            ),
        }
        rows.append(row)
        print(f"{item['clip_id']:<30} expected={sorted(expected)} predicted={sorted(predicted)} top={row['top_label']}")

    labels = list(catalog.mappings)
    negative_rows = [row for row in rows if not row["expected"]]
    critical = {"fire_alarm", "emergency_siren"}
    critical_rows = [row for row in rows if row["expected"] & critical]
    report = {
        "evaluation_type": "independent_license_cleared_holdout_frozen_policy",
        "policy_version": "1-frozen-before-holdout",
        "clips": len(rows),
        "source_level_independence": True,
        "exact_match": round(sum(row["exact_match"] for row in rows) / len(rows), 4),
        "negative_false_alerts": sum(bool(row["predicted"]) for row in negative_rows),
        "negative_clips": len(negative_rows),
        "critical_misses": sum(not bool(row["expected"] & row["predicted"] & critical) for row in critical_rows),
        "critical_clips": len(critical_rows),
        "latency_ms": {
            "mean": round(mean(latencies), 2),
            "median": round(median(latencies), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2),
            "max": round(max(latencies), 2),
        },
        "per_class": per_class_metrics(labels, rows),
        "warning": "Small license-cleared hackathon holdout; not a population benchmark, medical claim, or safety certification.",
    }
    with RESULTS.open("w", encoding="utf-8", newline="") as handle:
        fields = ["clip_id", "source_url", "expected", "predicted", "top_label", "top_score", "model_ms", "latency_ms", "exact_match", "event_scores"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "expected": "|".join(sorted(row["expected"])),
                "predicted": "|".join(sorted(row["predicted"])),
            })
    METRICS.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_failures(rows)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
