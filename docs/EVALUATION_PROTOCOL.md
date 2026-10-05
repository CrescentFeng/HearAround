# HearAround independent evaluation protocol

Updated: 2026-10-03

## Purpose

This protocol checks whether the existing YAMNet mapping and safety policy generalize beyond the built-in demonstration audio. It is deliberately small enough for a hackathon and strict enough to prevent the demo set from being presented as an accuracy benchmark.

## Frozen boundary

- Mapping: `config/audioset_to_product.yaml`, version 1.
- Alert policy: `config/alert_policy.yaml`, version 1.
- Freeze label recorded in every holdout row: `1-frozen-before-holdout`.
- Thresholds and label mappings were not changed after holdout results were observed.
- Future improvements must be developed on new development material, then evaluated once on a new holdout version. The current holdout must not become a tuning set.

## Dataset boundary

- 23 source recordings: 17 target events and 6 hard negatives.
- Six product classes: fire alarm, emergency siren, car horn, baby crying, doorbell and knocking.
- Every recording has a distinct Freesound source ID from the demo manifest.
- Every source page is checked automatically for an explicit CC0 deed.
- No augmented copies are counted as additional independent examples.
- Holdout WAV files remain local and are not exposed in the website sample picker.

The manifest and human-readable provenance are in `eval/holdout_manifest.csv` and `eval/HOLDOUT_ATTRIBUTION.md`.

## Reproduction

```bash
.venv/bin/python eval/collect_holdout.py
PYTHONPATH=backend .venv/bin/python eval/run_holdout.py
PYTHONPATH=backend .venv/bin/python eval/run_stream_stress.py --cycles 10
```

## Results

- Exact set match: 65.2% (15/23).
- Macro-F1 across six product classes: 62.8%.
- Hard-negative false alerts: 0/6.
- Critical-event misses: 2/6.
- Doorbell recall: 0/3; this is the clearest current failure.
- Repeated sequential inference: 230 runs, zero exceptions and zero output inconsistencies.

Full machine-readable results are in `eval/holdout_metrics.json`, `eval/holdout_results.csv` and `eval/stream_stress_metrics.json`. Exact-match failures and their original source links are in `eval/HOLDOUT_FAILURES.md`.

## Interpretation

The results verify that the evaluation pipeline works and expose useful failure modes. They do not support a claim of production accuracy. The sample is small, sourced from public recordings rather than representative users and devices, and does not cover room distance, phone microphones, overlapping sources or all cultural variations of an alarm sound.

HearAround remains an experimental assistive prototype. It is not a medical device, certified fire alarm, emergency dispatch system or substitute for established accessibility aids.

## Next remediation cycle

The next model-quality iteration should collect a separate development expansion set for door chimes, wood-block-like knocks, musical alarms and short infant cries. Candidate fixes can include broader AudioSet label groups, class-specific windowing or a small second-stage classifier. None should be accepted merely because they improve the current 23 clips; a new holdout version is required for confirmation.
