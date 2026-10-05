import unittest

from app.agent import HearAroundAgent
from app.schemas import Candidate


class AgentTests(unittest.TestCase):
    def test_duplicate_event_is_suppressed(self):
        agent = HearAroundAgent()
        candidate = {
            "key": "doorbell",
            "display_name": "Doorbell",
            "severity": "attention",
            "score": 0.82,
            "hits": 2,
            "windows": 4,
            "required_hits": 2,
            "eligible": True,
            "cooldown_seconds": 8,
            "vibration": [250, 170, 250],
        }
        top = [Candidate(label="Doorbell", score=0.82)]
        first = agent.create_event("session", candidate, 2000, top)
        second = agent.create_event("session", candidate, 2000, top)
        self.assertTrue(first.decision.alert)
        self.assertFalse(first.decision.suppressed)
        self.assertFalse(second.decision.alert)
        self.assertTrue(second.decision.suppressed)

    def test_feedback_only_for_known_event(self):
        agent = HearAroundAgent()
        self.assertFalse(agent.record_feedback("session", "missing", "incorrect"))


if __name__ == "__main__":
    unittest.main()
