# HearAround deployment and acceptance

Updated: 2026-10-05

## Production shape

HearAround is packaged as one FastAPI container serving both the API and the static interface. Run exactly one application worker: each additional worker would load another TensorFlow/YAMNet copy and multiply memory use.

The public deployment must sit behind a managed HTTPS reverse proxy. Browsers allow microphone capture only in a secure context (`https://`) or on local `localhost`. Do not bypass certificate warnings for a demo.

## Hosting decision

HearAround cannot be shipped as a static-only site: the browser interface depends on the FastAPI, TensorFlow, and YAMNet inference service. A static host would display the shell but break model loading and analysis, so no static-host manifest is included.

Two suitable managed-container options are documented without provisioning an account or incurring a charge. Pricing and account requirements below were checked against the providers' official pages on 2026-10-05:

| Option | Fit | Constraint |
| --- | --- | --- |
| Render Docker web service | Simple Git-based deployment, managed HTTPS and health checks | The 512 MB free instance is too small. The 1 CPU / 2 GB `1c-2g` plan is currently $25/month. |
| Hugging Face Docker Space | Docker/FastAPI support, 2 vCPU, 16 GB RAM and 50 GB ephemeral disk on CPU Basic | A personal PRO subscription is currently required to create Docker Spaces and costs $9/month. CPU Basic has no additional hourly charge but sleeps when inactive. |

**Recommended hackathon target:** Hugging Face Docker Space on CPU Basic, if the account owner accepts the $9/month PRO subscription. It provides substantially more memory headroom for TensorFlow than Render `1c-2g` at a lower monthly cost. Render remains the fallback when GitHub-native deployment and fewer cold-start constraints are worth the higher price.

Official references: [Hugging Face Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview), [Hugging Face pricing](https://huggingface.co/pricing), [Hugging Face Docker Spaces](https://huggingface.co/docs/hub/en/spaces-sdks-docker), [Render compute plans](https://render.com/docs/compute-plans), and [Render pricing](https://render.com/pricing).

`deploy/render.yaml.example` intentionally uses Render's `1c-2g` plan and is not named `render.yaml`, preventing an accidental paid-service Blueprint creation. `deploy/HUGGINGFACE_SPACE_README.example.md` contains the Docker Space front matter. The final provider and any paid plan require the account owner's explicit choice.

## Container run

```bash
docker compose up --build
```

Open `http://localhost:8000`. The first model load downloads YAMNet into the named `yamnet-cache` volume. Subsequent container restarts reuse the cache.

For a container hosting platform:

1. Deploy from the repository `Dockerfile`.
2. Expose container port `8000`, or inject the platform `PORT` variable.
3. Keep one replica and one worker for the hackathon demo.
4. Give the container at least 2 GB RAM; verify actual memory on the selected platform before the final demo.
5. Enable the platform's managed HTTPS hostname.
6. Do not add API keys: the current environment-sound MVP needs none.
7. Visit `/api/health`, then press **Load model** in the UI and confirm `model_ready` becomes `true`.
8. Visit `/api/project` and compare the facts with the final Devpost copy before publishing.

The container deliberately does not package the independent holdout WAV files. It includes only aggregate evaluation JSON and the public demo audio.

## Browser acceptance matrix

Run the following on the exact public HTTPS URL used for judging:

| Check | Desktop Chromium | Android Chromium | iOS Safari |
| --- | --- | --- | --- |
| Page and sample picker | Required | Required | Required |
| File/sample inference | Required | Required | Required |
| Microphone + AudioWorklet | Required | Required | Best effort |
| Visual alert | Required | Required | Required |
| Vibration | Usually unavailable | Verify | Usually unavailable |
| Speech synthesis | Verify | Verify | Verify |

Vibration and speech are progressive enhancements. A missing vibration API must never block the visual alert.

## User-authorized microphone acceptance

1. Open the HTTPS deployment or `localhost`.
2. Switch to technical mode and confirm **Secure context** and **Microphone capture** show available.
3. Click **Start live monitoring** yourself and allow microphone access in the browser prompt.
4. Confirm the UI shows a live sample rate and increasing analysis sequence.
5. Play one bundled licensed sample from a second device.
6. Confirm a visual event appears, then confirm cooldown avoids repeated disturbance.
7. Pause monitoring and confirm the five-second memory buffer is cleared.
8. Repeat once with permission denied; the sample picker and upload path must continue working.

## Release gates

- All unit and API integration tests pass.
- `/api/health`, `/api/evaluation` and one multipart `/api/analyze` request work on the deployed hostname.
- `/api/project` contains no unreplaced public-link placeholders in the release copy.
- The page reports secure context before microphone testing.
- No holdout audio is publicly served.
- Raw audio is absent from event history and feedback payloads.
- Known doorbell and knocking limitations are retained in the submission copy.
