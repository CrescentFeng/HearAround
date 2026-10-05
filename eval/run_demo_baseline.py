#!/usr/bin/env python3
"""Run a reproducible model-and-policy smoke test over the licensed demo set."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from time import perf_counter

from app.audio import decode_audio
from app.config import CONFIG_DIR
from app.policy import PolicyCatalog
from app.yamnet import YamnetClassifier


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifest.csv"
RESULTS = ROOT / "eval/demo_baseline_results.csv"
METRICS = ROOT / "eval/demo_baseline_metrics.json"


def metrics_for(labels: list[str], rows: list[dict]) -> dict:
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
        report[label] = {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}
    report["macro_f1"] = mean(f1_values)
    return report


def main() -> None:
    catalog = PolicyCatalog(CONFIG_DIR / "audioset_to_product.yaml", CONFIG_DIR / "alert_policy.yaml")
    classifier = YamnetClassifier()
    classifier.load()
    rows = []
    latencies = []
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    for item in manifest:
        path = ROOT / "data/demo" / f"{item['clip_id']}.wav"
        waveform, _ = decode_audio(path.read_bytes())
        started = perf_counter()
        scores, class_names, model_ms = classifier.classify(waveform)
        aggregated, top_candidates = catalog.aggregate(scores, class_names)
        latency_ms = int((perf_counter() - started) * 1000)
        latencies.append(latency_ms)
        predicted = {event["key"] for event in aggregated if event["eligible"]}
        expected = set() if item["expected_label"] == "none" else set(item["expected_label"].split("|"))
        row = {
            "clip_id": item["clip_id"],
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
        print(f"{item['clip_id']:<28} expected={sorted(expected)} predicted={sorted(predicted)} top={row['top_label']}")

    labels = list(catalog.mappings)
    per_class = metrics_for(labels, rows)
    negative_rows = [row for row in rows if not row["expected"]]
    critical_labels = {"fire_alarm", "emergency_siren"}
    critical_total = sum(bool(row["expected"] & critical_labels) for row in rows)
    critical_misses = sum(bool(row["expected"] & critical_labels) and not bool(row["predicted"] & row["expected"] & critical_labels) for row in rows)
    report = {
        "evaluation_type": "licensed_demo_smoke_test_not_independent_eval",
        "clips": len(rows),
        "exact_match": sum(row["exact_match"] for row in rows) / len(rows),
        "negative_false_alerts": sum(bool(row["predicted"]) for row in negative_rows),
        "negative_clips": len(negative_rows),
        "critical_misses": critical_misses,
        "critical_clips": critical_total,
        "mean_latency_ms": round(mean(latencies), 1),
        "per_class": per_class,
        "warning": "This small licensed demo set is for pipeline verification and must not be presented as an independent accuracy benchmark.",
    }
    with RESULTS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["clip_id", "expected", "predicted", "top_label", "top_score", "model_ms", "latency_ms", "exact_match", "event_scores"], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "expected": "|".join(sorted(row["expected"])), "predicted": "|".join(sorted(row["predicted"]))})
    METRICS.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
