import csv
import re
import unittest
from pathlib import Path

from app.main import demo_assets, evaluation_summary


ROOT = Path(__file__).resolve().parents[2]


class DemoAssetsTests(unittest.TestCase):
    def test_manifest_is_complete_and_license_filtered(self):
        payload = demo_assets()
        self.assertEqual(len(payload["assets"]), 20)
        self.assertEqual(payload["metrics"]["evaluation_type"], "licensed_demo_smoke_test_not_independent_eval")
        for asset in payload["assets"]:
            license_name = asset["license"].lower()
            self.assertNotIn("noncommercial", license_name)
            self.assertNotIn("sharealike", license_name)
            self.assertTrue(asset["source_url"].startswith("https://"))
            self.assertTrue(asset["audio_url"].endswith(".wav"))

    def test_holdout_is_independent_and_summary_is_available(self):
        with (ROOT / "data/manifest.csv").open(encoding="utf-8", newline="") as handle:
            demo = list(csv.DictReader(handle))
        with (ROOT / "eval/holdout_manifest.csv").open(encoding="utf-8", newline="") as handle:
            holdout = list(csv.DictReader(handle))
        demo_ids = {
            int(value)
            for row in demo
            for value in re.findall(r"freesound\.org/people/[^/]+/sounds/(\d+)/", row["source_url"])
        }
        holdout_ids = {int(row["source_id"]) for row in holdout}
        self.assertEqual(len(holdout), 23)
        self.assertFalse(demo_ids & holdout_ids)
        self.assertTrue(all(row["license"] == "CC0 1.0" for row in holdout))

        payload = evaluation_summary()
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["holdout"]["evaluation_type"], "independent_license_cleared_holdout_frozen_policy")
        self.assertTrue(payload["stress"]["passed"])
        self.assertNotIn("audio", payload)


if __name__ == "__main__":
    unittest.main()
