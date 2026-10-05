# HearAround release and Devpost checklist

Updated: 2026-10-03

## Deadline safety

The Devpost overview and official-rules pages currently show different deadlines. Treat **October 9, 2026 at 11:45 PM PDT** as the safe submission cutoff unless Devpost support confirms otherwise. Do not plan around the later date shown on the rules page.

## Required submission content

- [ ] Eligibility is confirmed for the entrant/team.
- [ ] Project title and one-line pitch are entered.
- [ ] Detailed description covers problem, solution, features, technology, and target users.
- [ ] At least one screenshot, video, or project file is attached.
- [ ] Public repository link is inserted, with license and setup instructions.
- [ ] Public HTTPS demo link is inserted and does not require evaluator credentials.
- [ ] Two-to-three-minute demo video is uploaded and captions are enabled.
- [ ] `[LIVE_DEMO_URL]`, `[REPOSITORY_URL]`, and `[VIDEO_URL]` are replaced everywhere.

## Code release gates

- [ ] `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v` passes.
- [ ] Production container builds without using a local bind mount.
- [ ] Container `/api/health` returns 200.
- [ ] Model loads in the deployed environment and survives one service restart with cache enabled.
- [ ] One built-in sample completes real inference from the public hostname.
- [ ] Holdout WAV files are absent from public/static/container paths.
- [ ] Raw audio is absent from event-history and feedback payloads.
- [ ] Browser console has no uncaught errors during the review path.

## Device acceptance

- [ ] Desktop Chromium: samples, upload, inference, technical view.
- [ ] Android Chromium: layout, microphone permission, live monitoring, visual alert, haptics if available.
- [ ] iOS Safari: layout, sample inference, visual alert; microphone is best effort.
- [ ] Permission denied: the UI explains the issue and file/sample paths remain usable.
- [ ] Monitoring stopped: buffer is cleared and the listening indicator turns off.
- [ ] High contrast and speech controls work, or unsupported capability is clearly shown.

## Truth and safety review

- [ ] “Real inference” is used only for uploaded, microphone, or bundled audio.
- [ ] The 20-clip demo set is called a development smoke test, not a benchmark.
- [ ] Holdout numbers remain 23 clips, 65.2% exact match, and 62.8% Macro-F1 unless a versioned new evaluation replaces them.
- [ ] Doorbell 0/3 and critical misses 2/6 remain disclosed.
- [ ] No medical-device, safety-certification, or emergency-equipment replacement claim is present.
- [ ] Asset licenses and source links remain visible.

## Final 30-minute pass

- [ ] Open the live URL in a private window.
- [ ] Load the model and run the exact demo sequence.
- [ ] Verify all three public links from another device/network.
- [ ] Check thumbnail, project title, spelling, captions, and audio volume.
- [ ] Submit before the safe cutoff and save the confirmation page.
