#!/usr/bin/env python3
"""Exercise repeated sequential inference without changing policy thresholds."""

from __future__ import annotations

import argparse
import csv
import json
import tracemalloc
from pathlib import Path
from time import perf_counter

import numpy as np

from app.audio import decode_audio
from app.config import CONFIG_DIR
from app.policy import PolicyCatalog
from app.yamnet import YamnetClassifier


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "eval/holdout_manifest.csv"
AUDIO_DIR = ROOT / "eval/holdout_audio"
OUTPUT = ROOT / "eval/stream_stress_metrics.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=10, help="Number of complete holdout passes.")
    args = parser.parse_args()
    if args.cycles < 1:
        raise SystemExit("--cycles must be at least 1")
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    catalog = PolicyCatalog(CONFIG_DIR / "audioset_to_product.yaml", CONFIG_DIR / "alert_policy.yaml")
    classifier = YamnetClassifier()
    classifier.load()
    decoded = []
    for item in manifest:
        waveform, _ = decode_audio((AUDIO_DIR / f"{item['clip_id']}.wav").read_bytes())
        decoded.append((item["clip_id"], waveform))

    latencies = []
    errors = []
    outputs_by_clip: dict[str, set[tuple[str, ...]]] = {item["clip_id"]: set() for item in manifest}
    tracemalloc.start()
    started = perf_counter()
    for cycle in range(args.cycles):
        for clip_id, waveform in decoded:
            request_started = perf_counter()
            try:
                scores, class_names, _ = classifier.classify(waveform)
                aggregated, _ = catalog.aggregate(scores, class_names)
                output = tuple(event["key"] for event in aggregated if event["eligible"])
                outputs_by_clip[clip_id].add(output)
            except Exception as exc:  # report the failure and continue the endurance run
                errors.append({"cycle": cycle + 1, "clip_id": clip_id, "error": repr(exc)})
            latencies.append((perf_counter() - request_started) * 1000)
    elapsed = perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    inconsistent = [clip_id for clip_id, outputs in outputs_by_clip.items() if len(outputs) > 1]
    report = {
        "test_type": "sequential_inference_stress_no_threshold_tuning",
        "cycles": args.cycles,
        "clips_per_cycle": len(decoded),
        "total_inferences": len(latencies),
        "elapsed_seconds": round(elapsed, 3),
        "throughput_inferences_per_second": round(len(latencies) / elapsed, 3),
        "latency_ms": {
            "mean": round(float(np.mean(latencies)), 2),
            "p50": round(float(np.percentile(latencies, 50)), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2),
            "p99": round(float(np.percentile(latencies, 99)), 2),
            "max": round(max(latencies), 2),
        },
        "python_tracemalloc_peak_mb": round(peak_bytes / 1024 / 1024, 2),
        "errors": errors,
        "inconsistent_clip_outputs": inconsistent,
        "passed": not errors and not inconsistent,
        "note": "This checks repeated sequential inference stability; browser microphone permission and wall-clock endurance remain separate acceptance tests.",
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
