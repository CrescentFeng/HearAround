# HearAround P5 release verification

Date: 2026-10-03 (Asia/Shanghai)

## Passed

- Automated test suite: **19/19 passed**.
- Docker Compose configuration: valid.
- `submission/PROJECT_FACTS.json`: valid JSON.
- Updated local FastAPI service: started successfully at `http://127.0.0.1:4173`.
- `GET /api/project`: 200 with HearAround v0.5.0 facts.
- `GET /api/health`: 200.
- `POST /api/model/load`: 200; YAMNet ready from the existing local cache.
- Browser smoke check: page rendered, real-service-ready status visible, licensed sample picker populated, simple mode intact.

## Production image build status

The Dockerfile was tested against a running Docker Desktop daemon. The original optional `apt-get` layer was removed, reducing image size and eliminating a Debian-mirror dependency. A second build reached Python dependency installation, then Docker's isolated network repeatedly timed out while connecting to `pypi.org` (including the FastAPI index). The build was stopped after retries because it could not progress to the TensorFlow download.

This is recorded as **network-blocked, not passed**. It is not evidence of a Dockerfile or application failure, but the production image must still be built successfully on a network that can reach PyPI before release.

## Remaining owner-controlled gates

- Select and authorize a cloud/container hosting account and any paid plan.
- Complete the production image build and deployed health/model smoke test.
- Use the public HTTPS hostname to authorize and test a physical microphone.
- Capture final screenshots, record the demo video, and replace public-link placeholders.
