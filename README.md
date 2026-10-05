# HearAround

> Important sounds, made visible.

HearAround is a privacy-conscious environmental-sound Agent for people who are Deaf or hard of hearing, older adults with age-related hearing loss, people with limited literacy, and caregivers. It turns meaningful sounds into large pictograms, color-plus-shape alerts, short actions, optional vibration, and optional speech.

HearAround was inspired by my grandmother. As her hearing gradually declined, everyday sounds became harder to notice, affecting both independence and safety. Because dense text is not always accessible to her, HearAround treats captions as only one possible channel—not the whole solution.

## What the MVP includes

- Six product events: fire/smoke alarm, emergency vehicle siren, car horn, baby crying, doorbell, and knocking.
- Real YAMNet inference over the AudioSet 521 ontology.
- File upload, licensed built-in samples, and live browser microphone capture.
- Mono decoding, 16 kHz resampling, overlapping windows, request backpressure, and silence validation.
- YAML-configured label mapping and deterministic safety-first alert rules.
- One stateful Agent for environment mode, event history, cooldown suppression, and feedback.
- Simple and technical interface modes, high contrast, browser speech, and progressive vibration.
- A clear distinction between interaction previews and real-model results.
- Twenty license-traceable development clips and a separate 23-source CC0 holdout.
- Public evaluation evidence, known failure disclosure, and 230-run sequential stress testing.
- In-memory raw-audio handling with event-metadata-only history.
- A single-container FastAPI deployment with health checks and security/privacy headers.

## Current evidence

The bundled 20-clip set is a development smoke test, not an independent benchmark. The frozen-policy holdout is separate by source ID:

| Measure | Result |
| --- | ---: |
| Independent holdout clips | 23 |
| Exact match | 65.2% |
| Macro-F1 | 62.8% |
| Hard-negative false alerts | 0/6 |
| Critical-event misses | 2/6 |
| Doorbell recall | 0/3 |
| Sequential inferences | 230 |
| Stress-test exceptions / output drift | 0 / 0 |

The doorbell failure is intentionally disclosed instead of being hidden by tuning on the holdout set. This small evaluation is not population-level evidence, a medical conclusion, or safety certification.

## How it works

```text
Microphone / uploaded audio / licensed sample
  → AudioWorklet capture and client-side WAV slicing (microphone only)
  → in-memory decoding, mono conversion, and 16 kHz resampling
  → YAMNet window inference
  → AudioSet-to-product label mapping
  → repeated-window aggregation or high-confidence transient path
  → deterministic safety policy
  → HearAround Agent context and cooldown
  → pictogram, short action, optional vibration and speech
```

Critical alerts are not delegated to free-form LLM judgment. The Agent coordinates evidence, state, user mode, duplicate suppression, and explainable actions; deterministic policy controls alert eligibility.

## Run locally

Python 3.12 is recommended. Dependency installation and the first YAMNet load require network access.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4173
```

Open `http://127.0.0.1:4173/`. Press **Load model** if YAMNet is not ready. The model is cached under `.cache/tfhub/`.

## Test

```bash
.venv/bin/pip install -r backend/requirements-dev.txt
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

The current suite contains 20 tests covering audio preprocessing, policy behavior, Agent cooldown, multipart analysis, privacy headers, evaluation separation, English interface contracts, and project-fact consistency.

Rebuild the licensed development set and baseline:

```bash
.venv/bin/python scripts/collect_commons_demo.py
PYTHONPATH=backend .venv/bin/python eval/run_demo_baseline.py
```

Rebuild and run the independent holdout and stress evaluation:

```bash
.venv/bin/python eval/collect_holdout.py
PYTHONPATH=backend .venv/bin/python eval/run_holdout.py
PYTHONPATH=backend .venv/bin/python eval/run_stream_stress.py --cycles 10
```

See [`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md) and [`eval/HOLDOUT_FAILURES.md`](eval/HOLDOUT_FAILURES.md) for methodology and source-linked failures.

## API

- `GET /api/health` — service and model state.
- `POST /api/model/load` — explicitly load YAMNet.
- `GET /api/demo-assets` — licensed demo catalog and development metrics.
- `GET /api/evaluation` — aggregate holdout and stress results; holdout audio is not served.
- `GET /api/project` — stable project and submission facts.
- `POST /api/analyze` — multipart `audio`, `session_id`, and `environment_mode` analysis.
- `POST /api/feedback` — correct/incorrect event feedback metadata.
- `GET/DELETE /api/events/{session_id}` — read or clear session event metadata.

## Privacy and accessibility

- Raw audio is processed in memory and is not persisted by the application.
- Live mode keeps about five seconds of rolling audio and clears it when monitoring stops.
- Event history stores labels, scores, rules, timestamps, and correction outcomes—not recordings.
- Microphone access requires an explicit user action and a secure browser context.
- Visual alerts remain the baseline when vibration or speech synthesis is unavailable.
- Severity is communicated with words, icons, and shapes, not color alone.
- HearAround does not claim sound direction from a single microphone.

## Container deployment

```bash
docker compose up --build
```

Production should use one application worker because each worker loads a TensorFlow/YAMNet copy. Use a managed HTTPS hostname and at least 2 GB RAM. See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the deployment and device-acceptance checklist.

## Repository guide

- `backend/app/` — FastAPI, preprocessing, policy, Agent, and YAMNet integration.
- `dist/` — competition-facing English web interface.
- `config/` — versioned label mapping and alert policy.
- `data/` — public demo WAV files, manifest, and attribution.
- `eval/` — reproducible holdout and stress evaluation artifacts.
- `docs/` — implementation, evaluation, live-audio, and deployment documentation.
- `submission/` — Devpost copy, demo script, judging matrix, and release checklist.

## Known limitations

- Doorbell and knocking recall require a new development set and recalibration.
- Live microphone acceptance must still be completed on the final public HTTPS deployment.
- VAD, live captions, native mobile apps, background listening, wearables, and user-trained sounds are future work.
- HearAround is experimental assistive technology. It is not a medical device, certified alarm, emergency service, or replacement for situational awareness.

## License and media attribution

HearAround project source code is released under the [MIT License](LICENSE).

Bundled audio and third-party dependencies are **not relicensed under MIT**. Each audio file remains governed by its source license. See [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md), [`data/manifest.csv`](data/manifest.csv), and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
