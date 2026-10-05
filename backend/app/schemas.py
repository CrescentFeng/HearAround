from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["critical", "urgent", "attention", "none"]


class Candidate(BaseModel):
    label: str
    score: float = Field(ge=0, le=1)


class Evidence(BaseModel):
    hits: int
    windows: int
    required_hits: int
    top_labels: list[Candidate]


class Decision(BaseModel):
    alert: bool
    suppressed: bool
    rule: str
    reason: str
    cooldown_seconds: int


class AudioEvent(BaseModel):
    event_id: str
    label: str
    display_name: str
    severity: Severity
    score: float
    started_at_ms: int
    duration_ms: int
    source: str = "yamnet"
    evidence: Evidence
    decision: Decision
    user_message: str
    suggested_action: str
    vibration: list[int]


class AnalysisResponse(BaseModel):
    session_id: str
    model: str
    model_ready: bool
    duration_ms: int
    inference_ms: int
    events: list[AudioEvent]
    top_candidates: list[Candidate]
    raw_audio_retained: bool = False
    notice: str


class FeedbackRequest(BaseModel):
    session_id: str
    event_id: str
    verdict: Literal["correct", "incorrect"]


class FeedbackResponse(BaseModel):
    recorded: bool
    event_id: str
    retained_fields: list[str]
