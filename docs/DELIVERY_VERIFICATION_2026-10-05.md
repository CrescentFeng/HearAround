# HearAround delivery verification

Date: 2026-10-05 (Asia/Shanghai)

## Passed locally

- Public source repository: `https://github.com/CrescentFeng/HearAround`.
- Git author attribution: `CrescentFeng` with the GitHub-provided noreply address.
- Automated suite: **20/20 tests passed**.
- Production Docker image built successfully from the repository Dockerfile.
- Image acceptance: Linux container, non-root user, healthy container health check.
- `GET /api/health`: HTTP 200.
- `POST /api/model/load`: model ready when the verified YAMNet cache is available.
- Real container inference over `fire_smoke_alarm.wav`: fire-alarm critical alert, 0.9909 product score, approximately 80 ms model inference on the local host.
- Local and remote Git commit SHAs matched before delivery-stage edits.
- No API keys or credentials are required by the six-event environment-sound MVP.

## Important deployment observation

The local network proxy interrupted one fresh 14 MB TensorFlow Hub archive download after approximately 4.5 MB. This made `tensorflow_hub` report the partial archive as an invalid module. The same container passed model loading and real inference with the already verified official YAMNet cache mounted read-only.

This is a local proxy-transfer failure, not a model-format or application-code failure. The selected public cloud must still pass a fresh first-load test from its own network before the live URL is accepted.

## Selected recommendation

Use a public Hugging Face Docker Space on CPU Basic if the owner accepts the required personal PRO subscription. Official documentation currently lists 2 vCPU, 16 GB RAM, 50 GB ephemeral disk, and no additional hourly cost for CPU Basic. The required personal PRO plan is currently $9/month.

Render `1c-2g` is the fallback. It provides 1 CPU and 2 GB RAM and is currently $25/month. The 512 MB Render free service is not a safe target for TensorFlow/YAMNet.

## Remaining owner-controlled gates

- Authorize the selected hosting account and any subscription or billing step.
- Create the public service and complete its build.
- Verify fresh YAMNet loading, `/api/health`, one real sample inference, and service restart behavior on the public hostname.
- Complete desktop and mobile HTTPS microphone acceptance.
- Capture final screenshots and record the captioned 2–3 minute demo.
- Replace `[LIVE_DEMO_URL]` and `[VIDEO_URL]`, push the final release commit, and submit on Devpost.
