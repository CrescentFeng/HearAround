from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from .schemas import Candidate


@dataclass(frozen=True)
class EventMapping:
    key: str
    display_name: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class AlertPolicy:
    severity: str
    min_score: float
    required_hits: int
    immediate_score: float | None
    window_count: int
    cooldown_seconds: int
    vibration: tuple[int, ...]


class PolicyCatalog:
    def __init__(self, mapping_path: Path, policy_path: Path):
        mapping_doc = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
        policy_doc = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        self.mappings = {
            key: EventMapping(key, value["display_name"], tuple(value["labels"]))
            for key, value in mapping_doc["events"].items()
        }
        self.policies = {
            key: AlertPolicy(
                severity=value["severity"],
                min_score=float(value["min_score"]),
                required_hits=int(value["required_hits"]),
                immediate_score=(float(value["immediate_score"]) if value.get("immediate_score") is not None else None),
                window_count=int(value["window_count"]),
                cooldown_seconds=int(value["cooldown_seconds"]),
                vibration=tuple(int(item) for item in value["vibration"]),
            )
            for key, value in policy_doc["policies"].items()
        }
        missing = set(self.mappings) - set(self.policies)
        if missing:
            raise ValueError(f"Missing policies for: {sorted(missing)}")

    def aggregate(
        self,
        scores: np.ndarray,
        class_names: list[str],
        top_k: int = 5,
    ) -> tuple[list[dict], list[Candidate]]:
        if scores.ndim != 2:
            raise ValueError("YAMNet scores must be a 2D [window, class] array")
        class_index = {name: idx for idx, name in enumerate(class_names)}
        mean_scores = scores.mean(axis=0)
        best_indices = np.argsort(mean_scores)[::-1][:top_k]
        top_candidates = [
            Candidate(label=class_names[int(idx)], score=float(mean_scores[int(idx)]))
            for idx in best_indices
        ]

        aggregated: list[dict] = []
        for key, mapping in self.mappings.items():
            indices = [class_index[label] for label in mapping.labels if label in class_index]
            if not indices:
                continue
            per_window = scores[:, indices].max(axis=1)
            policy = self.policies[key]
            window_count = min(policy.window_count, len(per_window))
            recent = per_window[-window_count:]
            hits = int(np.count_nonzero(recent >= policy.min_score))
            aggregate_score = float(np.max(recent)) if len(recent) else 0.0
            high_confidence = policy.immediate_score is not None and aggregate_score >= policy.immediate_score
            repeated_hits = hits >= policy.required_hits
            aggregated.append({
                "key": key,
                "display_name": mapping.display_name,
                "severity": policy.severity,
                "score": aggregate_score,
                "hits": hits,
                "windows": int(window_count),
                "required_hits": policy.required_hits,
                "eligible": high_confidence or repeated_hits,
                "eligible_by": "high_confidence" if high_confidence else "repeated_hits" if repeated_hits else "not_eligible",
                "immediate_score": policy.immediate_score,
                "cooldown_seconds": policy.cooldown_seconds,
                "vibration": list(policy.vibration),
            })
        priority = {"critical": 0, "urgent": 1, "attention": 2}
        aggregated.sort(key=lambda item: (not item["eligible"], priority[item["severity"]], -item["score"]))
        return aggregated, top_candidates
