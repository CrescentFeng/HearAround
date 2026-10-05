import io
import unittest
from uuid import uuid4

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from app import main


def wav_bytes(seconds: float = 1.0, sample_rate: int = 16_000) -> bytes:
    timeline = np.arange(int(seconds * sample_rate), dtype=np.float32) / sample_rate
    waveform = (0.2 * np.sin(2 * np.pi * 440 * timeline)).astype(np.float32)
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)
        cls.original_classify = main.classifier.classify

        def classify_stub(_waveform):
            scores = np.array([[0.95], [0.93], [0.91]], dtype=np.float32)
            return scores, ["Vehicle horn, car horn, honking"], 4

        main.classifier.classify = classify_stub

    @classmethod
    def tearDownClass(cls):
        main.classifier.classify = cls.original_classify

    def setUp(self):
        self.session_id = f"integration_{uuid4().hex}"

    def tearDown(self):
        main.agent.clear(self.session_id)

    def analyze(self, environment_mode="home"):
        return self.client.post(
            "/api/analyze",
            files={"audio": ("tone.wav", wav_bytes(), "audio/wav")},
            data={"session_id": self.session_id, "environment_mode": environment_mode},
        )

    def test_health_and_security_headers(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("microphone=(self)", response.headers["permissions-policy"])
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])

    def test_multipart_analysis_runs_policy_and_agent(self):
        first = self.analyze()
        self.assertEqual(first.status_code, 200)
        payload = first.json()
        self.assertFalse(payload["raw_audio_retained"])
        self.assertEqual(payload["events"][0]["label"], "car_horn")
        self.assertTrue(payload["events"][0]["decision"]["alert"])

        second = self.analyze()
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["events"][0]["decision"]["suppressed"])

    def test_feedback_history_and_clear_workflow(self):
        event_id = self.analyze().json()["events"][0]["event_id"]
        feedback = self.client.post(
            "/api/feedback",
            json={"session_id": self.session_id, "event_id": event_id, "verdict": "incorrect"},
        )
        self.assertEqual(feedback.status_code, 200)
        self.assertNotIn("audio", " ".join(feedback.json()["retained_fields"]))

        history = self.client.get(f"/api/events/{self.session_id}")
        self.assertEqual(len(history.json()["events"]), 1)
        cleared = self.client.delete(f"/api/events/{self.session_id}")
        self.assertTrue(cleared.json()["cleared"])
        self.assertEqual(self.client.get(f"/api/events/{self.session_id}").json()["events"], [])

    def test_invalid_environment_mode_is_rejected(self):
        response = self.analyze(environment_mode="unknown")
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unsupported", response.json()["detail"])

    def test_evaluation_summary_does_not_expose_holdout_audio(self):
        response = self.client.get("/api/evaluation")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ready"])
        self.assertNotIn("holdout_audio", response.text)

    def test_project_facts_are_consistent_with_submission_boundary(self):
        response = self.client.get("/api/project")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "HearAround")
        self.assertEqual(payload["evaluation"]["holdout_clips"], 23)
        self.assertFalse(payload["claims"]["safety_certified"])
        self.assertFalse(payload["claims"]["medical_device"])


if __name__ == "__main__":
    unittest.main()
