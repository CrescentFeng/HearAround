# HearAround implementation status

Updated: 2026-10-03

## Completed

- Accessible Chinese-first UI based on the approved dark, high-contrast prototype.
- Separate simple and technical views.
- Familiar event pictograms instead of letter abbreviations.
- FastAPI endpoints for health, model loading, analysis, feedback and history.
- Real YAMNet loading and inference path.
- Audio decoding, mono conversion, resampling, length and silence validation.
- Six-class AudioSet mapping and versioned alert policy.
- Stateful single Agent with cooldown suppression.
- Optional TTS, vibration and high-contrast mode.
- Unit tests for policy, Agent and audio processing.
- 20 license-traceable demo clips from Wikimedia Commons and Freesound, including four hard negatives and two derived mixes.
- Reproducible asset collector, attribution manifest and real YAMNet baseline report.
- Built-in sample picker with playback, source link and one-click real inference path.
- Deterministic high-confidence fast path for transient events alongside repeated-window confirmation.
- Browser microphone capture with AudioWorklet, a five-second rolling buffer and overlapping live inference windows.
- Live start/pause, quiet-audio handling, request backpressure, device-disconnect cleanup and privacy status.
- 23-source independent CC0 holdout, verified disjoint from the 20-clip demo set.
- Frozen-policy per-class evaluation, source-linked failure report and website evaluation summary.
- 230-run sequential inference stress test with zero exceptions and zero output drift.
- Multipart API integration coverage for inference, cooldown, feedback, history, clearing and privacy headers.
- Portable single-worker Docker deployment, persistent model cache and container health check.
- In-product secure-context, microphone, vibration and speech capability diagnostics.
- CSP, no-sniff, no-referrer, same-origin microphone policy and no-store API headers.
- One source of truth for submission claims exposed through `/api/project`.
- English Devpost copy, 2–3 minute demo script, judging matrix, screenshot plan and release checklist.
- Provider-ready but non-activating Render and Hugging Face container examples.
- English-first competition interface, English runtime/API messages and English `en-US` speech output.
- Versioned front-end assets to prevent stale Chinese JavaScript from being served to judges.

## Still required before submission

- Complete the user-authorized physical microphone acceptance test.
- Complete a production image build once outbound package mirrors are reachable; the local Docker daemon is available, but the Debian/Python package network path must succeed.
- Deploy to a managed HTTPS hostname and run the documented desktop/mobile browser matrix.
- Build a new development expansion set for the documented doorbell and knocking failures; do not tune on the current holdout.
- Optionally add Silero VAD and live captions after the core environment-sound MVP is stable.
- Record the 2–3 minute demo, capture final screenshots and replace the three public-link placeholders.

## Product boundary

The six visible scenario buttons are interaction previews. Uploaded files and built-in licensed samples run the real model. The bundled 20-clip report is a development smoke test. The separate 23-clip frozen-policy holdout is independent by source ID, but remains too small for production or safety claims. Raw analyzed audio is not stored by the application. Browser microphone acceptance remains a user-authorized manual gate.
