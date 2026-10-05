from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from uuid import uuid4

from .schemas import AudioEvent, Candidate, Decision, Evidence


MESSAGES = {
    "fire_alarm": ("Possible fire alarm — check your surroundings now", {"home": "Stay calm, leave the danger area, and follow official emergency guidance.", "outdoor": "Move away from the building and follow official emergency guidance.", "sleep": "Get up now and leave the danger area."}),
    "emergency_siren": ("A siren may be nearby — stay aware", {"home": "Check your surroundings and follow official emergency information.", "outdoor": "Pause, move away from traffic, and check your surroundings.", "sleep": "Get up and check your surroundings and official emergency information."}),
    "car_horn": ("A car horn was detected — watch for vehicles", {"home": "If you are near a street, watch for nearby vehicles.", "outdoor": "Pause and check for nearby vehicles before moving.", "sleep": "A car horn was detected nearby. Check if needed."}),
    "baby_crying": ("A baby may be crying — please check", {"home": "Check the baby or caregiver when it is safe to do so.", "outdoor": "A nearby baby may need attention.", "sleep": "Get up and check whether the baby needs care."}),
    "doorbell": ("Someone may be at the door", {"home": "Check the door or a door camera when it is safe to do so.", "outdoor": "A doorbell was detected in the current audio.", "sleep": "A doorbell was detected. Check the door if needed."}),
    "knocking": ("Someone may be knocking", {"home": "Check the door or a door camera when it is safe to do so.", "outdoor": "Knocking was detected in the current audio.", "sleep": "Repeated knocking was detected. Check the door if needed."}),
}


@dataclass
class SessionState:
    last_alert_at: dict[str, float] = field(default_factory=dict)
    recent_events: list[dict] = field(default_factory=list)
    corrections: list[dict] = field(default_factory=list)


class HearAroundAgent:
    """Stateful coordinator. It never overrides deterministic alert eligibility."""

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

    def _state(self, session_id: str) -> SessionState:
        with self._lock:
            return self._sessions.setdefault(session_id, SessionState())

    def create_event(
        self,
        session_id: str,
        candidate: dict,
        duration_ms: int,
        top_candidates: list[Candidate],
        environment_mode: str = "home",
    ) -> AudioEvent | None:
        if not candidate["eligible"]:
            return None
        state = self._state(session_id)
        now = monotonic()
        previous = state.last_alert_at.get(candidate["key"])
        suppressed = previous is not None and now - previous < candidate["cooldown_seconds"]
        if not suppressed:
            state.last_alert_at[candidate["key"]] = now

        event_id = f"evt_{uuid4().hex[:12]}"
        message, actions = MESSAGES[candidate["key"]]
        action = actions.get(environment_mode, actions["home"])
        if candidate.get("eligible_by") == "high_confidence":
            eligibility_reason = f"A high-confidence single-window score of {candidate['score']:.2f} reached the immediate threshold."
        else:
            eligibility_reason = f"{candidate['hits']}/{candidate['windows']} windows reached the policy threshold."
        event = AudioEvent(
            event_id=event_id,
            label=candidate["key"],
            display_name=candidate["display_name"],
            severity=candidate["severity"],
            score=candidate["score"],
            started_at_ms=0,
            duration_ms=duration_ms,
            evidence=Evidence(
                hits=candidate["hits"],
                windows=candidate["windows"],
                required_hits=candidate["required_hits"],
                top_labels=top_candidates,
            ),
            decision=Decision(
                alert=not suppressed,
                suppressed=suppressed,
                rule=f"{candidate['key']}_v1",
                reason=(
                    "A matching event is still in cooldown. The event is recorded without another alert."
                    if suppressed else
                    eligibility_reason
                ),
                cooldown_seconds=candidate["cooldown_seconds"],
            ),
            user_message=message,
            suggested_action=action,
            vibration=candidate["vibration"],
        )
        state.recent_events.insert(0, {
            "event_id": event_id,
            "label": candidate["key"],
            "display_name": candidate["display_name"],
            "severity": candidate["severity"],
            "score": candidate["score"],
            "alert": not suppressed,
            "suppressed": suppressed,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        del state.recent_events[50:]
        return event

    def record_feedback(self, session_id: str, event_id: str, verdict: str) -> bool:
        state = self._state(session_id)
        matching = next((item for item in state.recent_events if item["event_id"] == event_id), None)
        if matching is None:
            return False
        state.corrections.append({
            "event_id": event_id,
            "label": matching["label"],
            "verdict": verdict,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return True

    def recent_events(self, session_id: str) -> list[dict]:
        return list(self._state(session_id).recent_events)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
