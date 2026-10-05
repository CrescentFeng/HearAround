import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FrontendContractTests(unittest.TestCase):
    def test_live_controls_and_privacy_copy_exist(self):
        html = (ROOT / "dist/index.html").read_text(encoding="utf-8")
        self.assertIn('id="liveToggle"', html)
        self.assertIn('id="liveDetail"', html)
        self.assertIn("five-second memory buffer", html)

    def test_audio_worklet_is_wired(self):
        app_js = (ROOT / "dist/assets/app.js").read_text(encoding="utf-8")
        worklet = ROOT / "dist/assets/pcm-capture-worklet.js"
        self.assertTrue(worklet.exists())
        self.assertIn("audioWorklet.addModule('/assets/pcm-capture-worklet.js')", app_js)
        self.assertIn("new AudioWorkletNode(context,'hearound-pcm-capture')", app_js)
        self.assertIn("registerProcessor('hearound-pcm-capture'", worklet.read_text(encoding="utf-8"))

    def test_independent_evaluation_is_visible_but_not_served_as_demo_audio(self):
        html = (ROOT / "dist/index.html").read_text(encoding="utf-8")
        app_js = (ROOT / "dist/assets/app.js").read_text(encoding="utf-8")
        self.assertIn('id="holdoutF1"', html)
        self.assertIn("fetch('/api/evaluation')", app_js)
        self.assertNotIn("holdout_audio", html + app_js)

    def test_browser_compatibility_and_secure_context_are_explicit(self):
        html = (ROOT / "dist/index.html").read_text(encoding="utf-8")
        app_js = (ROOT / "dist/assets/app.js").read_text(encoding="utf-8")
        self.assertIn('id="secureStatus"', html)
        self.assertIn('id="micStatus"', html)
        self.assertIn("window.isSecureContext", app_js)
        self.assertIn("Microphone access requires HTTPS or localhost", app_js)

    def test_public_interface_is_english(self):
        html = (ROOT / "dist/index.html").read_text(encoding="utf-8")
        app_js = (ROOT / "dist/assets/app.js").read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', html)
        self.assertIn("Know what is happening around you.", html)
        self.assertIn("Agent decision trail", html)
        self.assertIn("app.js?v=0.6.0", html)
        self.assertNotRegex(html + app_js, r"[\u4e00-\u9fff]")


if __name__ == "__main__":
    unittest.main()
