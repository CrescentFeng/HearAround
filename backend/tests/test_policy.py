import unittest
from pathlib import Path

import numpy as np

from app.policy import PolicyCatalog


ROOT = Path(__file__).resolve().parents[2]


class PolicyCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = PolicyCatalog(
            ROOT / "config/audioset_to_product.yaml",
            ROOT / "config/alert_policy.yaml",
        )

    def test_doorbell_requires_two_hits(self):
        names = ["Doorbell", "Music"]
        scores = np.array([[0.4, 0.1], [0.5, 0.1], [0.1, 0.8]], dtype=np.float32)
        events, top = self.catalog.aggregate(scores, names)
        doorbell = next(item for item in events if item["key"] == "doorbell")
        self.assertTrue(doorbell["eligible"])
        self.assertEqual(doorbell["hits"], 2)
        self.assertEqual(top[0].label, "Music")

    def test_single_low_doorbell_does_not_alert(self):
        names = ["Doorbell"]
        scores = np.array([[0.34], [0.1], [0.2]], dtype=np.float32)
        events, _ = self.catalog.aggregate(scores, names)
        doorbell = next(item for item in events if item["key"] == "doorbell")
        self.assertFalse(doorbell["eligible"])

    def test_single_high_doorbell_uses_immediate_rule(self):
        names = ["Doorbell"]
        scores = np.array([[0.4], [0.1], [0.2]], dtype=np.float32)
        events, _ = self.catalog.aggregate(scores, names)
        doorbell = next(item for item in events if item["key"] == "doorbell")
        self.assertTrue(doorbell["eligible"])
        self.assertEqual(doorbell["eligible_by"], "high_confidence")


if __name__ == "__main__":
    unittest.main()
