from __future__ import annotations

import csv
import json
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import HearAroundAgent
from .audio import AudioInputError, decode_audio
from .config import CONFIG_DIR, DATA_DIR, MAX_AUDIO_BYTES, STATIC_DIR, SUBMISSION_DIR
from .policy import PolicyCatalog
from .schemas import AnalysisResponse, FeedbackRequest, FeedbackResponse
from .yamnet import ModelUnavailableError, YamnetClassifier


app = FastAPI(
    title="HearAround API",
    version="0.6.0",
    description="Environment sound inference and safety-first Agent orchestration.",
)
catalog = PolicyCatalog(
    CONFIG_DIR / "audioset_to_product.yaml",
    CONFIG_DIR / "alert_policy.yaml",
)
classifier = YamnetClassifier()
agent = HearAroundAgent()


@app.middleware("http")
async def security_and_privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "microphone=(self), camera=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; "
        "frame-ancestors https://huggingface.co https://*.huggingface.co"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": "YAMNet",
        "model_ready": classifier.ready,
        "model_error": classifier.load_error,
        "privacy": "raw audio is processed in memory and is not retained",
    }


@app.get("/api/project")
def project_facts() -> dict:
    """Return the submission claims from one reviewable source of truth."""
    facts_path = SUBMISSION_DIR / "PROJECT_FACTS.json"
    if not facts_path.exists():
        raise HTTPException(status_code=503, detail="Project submission facts have not been generated.")
    return json.loads(facts_path.read_text(encoding="utf-8"))


@app.get("/api/demo-assets")
def demo_assets() -> dict:
    manifest_path = DATA_DIR / "manifest.csv"
    metrics_path = DATA_DIR.parent / "eval" / "demo_baseline_metrics.json"
    if not manifest_path.exists():
        return {"assets": [], "metrics": None, "warning": "Demo assets have not been generated."}
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assets = [{
        "clip_id": row["clip_id"],
        "expected_labels": [] if row["expected_label"] == "none" else row["expected_label"].split("|"),
        "kind": "mixed" if row["split"] == "demo_mixed" else "negative" if row["expected_label"] == "none" else "target",
        "audio_url": f"/demo-audio/{row['clip_id']}.wav",
        "source_url": row["source_url"],
        "source_site": row["source_site"],
        "creator": row["creator"],
        "license": row["license"],
        "license_url": row["license_url"],
        "duration_s": float(row["duration_s"]),
    } for row in rows if (DATA_DIR / "demo" / f"{row['clip_id']}.wav").exists()]
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else None
    return {
        "assets": assets,
        "metrics": metrics,
        "warning": "These assets are pipeline smoke tests, not an independent accuracy benchmark.",
    }


@app.get("/api/evaluation")
def evaluation_summary() -> dict:
    """Expose result summaries, never the holdout audio or raw recordings."""
    eval_dir = DATA_DIR.parent / "eval"
    metrics_path = eval_dir / "holdout_metrics.json"
    stress_path = eval_dir / "stream_stress_metrics.json"
    if not metrics_path.exists():
        return {
            "ready": False,
            "holdout": None,
            "stress": None,
            "warning": "The independent holdout evaluation has not been run.",
        }
    return {
        "ready": True,
        "holdout": json.loads(metrics_path.read_text(encoding="utf-8")),
        "stress": json.loads(stress_path.read_text(encoding="utf-8")) if stress_path.exists() else None,
        "warning": "Small hackathon holdout set; not a population benchmark, medical conclusion, or safety certification.",
    }


@app.post("/api/model/load")
def load_model() -> dict:
    try:
        classifier.load()
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"model": "YAMNet", "model_ready": True}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    audio: UploadFile = File(...),
    session_id: str | None = Form(None),
    environment_mode: str = Form("home"),
) -> AnalysisResponse:
    if environment_mode not in {"home", "outdoor", "sleep"}:
        raise HTTPException(status_code=422, detail="Unsupported environment mode.")
    content = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="The audio file cannot exceed 25 MB.")
    try:
        waveform, sample_rate = decode_audio(content)
    except AudioInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    started = perf_counter()
    try:
        scores, class_names, model_ms = classifier.classify(waveform)
    except ModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    aggregated, top_candidates = catalog.aggregate(scores, class_names)
    duration_ms = int(len(waveform) / sample_rate * 1000)
    sid = session_id or uuid4().hex
    events = []
    for candidate in aggregated:
        event = agent.create_event(
            sid,
            candidate,
            duration_ms,
            top_candidates,
            environment_mode=environment_mode,
        )
        if event is not None:
            events.append(event)
    total_ms = int((perf_counter() - started) * 1000)
    return AnalysisResponse(
        session_id=sid,
        model="YAMNet AudioSet 521",
        model_ready=True,
        duration_ms=duration_ms,
        inference_ms=max(model_ms, total_ms),
        events=events,
        top_candidates=top_candidates,
        notice="Model scores are not probability-calibrated. Deterministic rules generate critical alerts.",
    )


@app.post("/api/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest) -> FeedbackResponse:
    if not agent.record_feedback(payload.session_id, payload.event_id, payload.verdict):
        raise HTTPException(status_code=404, detail="The corresponding event was not found.")
    return FeedbackResponse(
        recorded=True,
        event_id=payload.event_id,
        retained_fields=["event_id", "label", "verdict", "created_at"],
    )


@app.get("/api/events/{session_id}")
def recent_events(session_id: str) -> dict:
    return {"events": agent.recent_events(session_id)}


@app.delete("/api/events/{session_id}")
def clear_events(session_id: str) -> dict:
    agent.clear(session_id)
    return {"cleared": True}


app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
app.mount("/demo-audio", StaticFiles(directory=DATA_DIR / "demo"), name="demo-audio")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
