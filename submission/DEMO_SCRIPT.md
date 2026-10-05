# HearAround 2–3 minute demo script

Target length: 2:40. Record the public HTTPS deployment in a Chromium browser at 1440 × 900 or 1920 × 1080. Keep browser zoom at 100–110% and captions on.

## 0:00–0:18 — Human reason

**On screen:** simple mode landing state.

**Voice-over:**

“This is HearAround, an environmental-sound Agent inspired by my grandmother. As her hearing declined, everyday sounds became harder to notice. Text alone was not enough because she also finds dense reading difficult. HearAround makes important sounds visible, understandable, and optionally speakable.”

## 0:18–0:38 — Product promise and boundaries

**On screen:** point to the privacy card, simple/technical toggle, speech, and high-contrast controls.

**Voice-over:**

“It is designed for Deaf and hard-of-hearing users, older adults, low-literacy users, and caregivers. Raw audio is processed in memory and is not saved. Visual alerts always work; speech and vibration are optional enhancements.”

## 0:38–1:12 — Real model inference

**On screen:** choose the bundled car-horn sample, play one second, click **Load this sample**, then **Analyze sound**.

**Voice-over:**

“I will use a bundled, source-linked CC0 sample so the demo is reproducible. This is not a scripted scenario button. The file is decoded, resampled to 16 kilohertz, and analyzed by the real YAMNet AudioSet model. The result is mapped to a product event and then checked by deterministic alert rules.”

**Pause until result appears.**

“The user receives a large pictogram, severity shown by words and shape as well as color, and one short action.”

## 1:12–1:42 — Agent behavior

**On screen:** switch to technical mode. Show top candidates and the Agent decision trail. Analyze the same sample again.

**Voice-over:**

“The technical view exposes verifiable evidence: model candidates, the matched rule, environment mode, and Agent action. The Agent manages state, feedback, and cooldown. It does not freely decide whether a critical warning is real. Repeating this event demonstrates cooldown suppression, reducing alert fatigue.”

## 1:42–2:02 — Accessibility and device behavior

**On screen:** toggle high contrast and speech. Show browser capability panel. If using a phone, briefly show microphone permission and monitoring state.

**Voice-over:**

“Simple mode is the primary experience. High contrast, large symbols, optional read-aloud guidance, and progressive vibration support different needs. Microphone permission is requested only after a user action, and monitoring remains visibly indicated.”

## 2:02–2:27 — Honest evaluation

**On screen:** technical evidence metrics.

**Voice-over:**

“A separate 23-clip CC0 holdout produced 65.2 percent exact match and 62.8 percent Macro-F1, with zero alerts across six difficult negatives. Two of six critical events were missed, and doorbell recall is currently zero of three. I disclose that failure because this is a prototype—not a certified safety device.”

## 2:27–2:42 — Close

**On screen:** return to simple mode and show the alert card.

**Voice-over:**

“Next, HearAround can become a mobile app connected to a smartwatch, wristband, or bedside light, with more on-device inference and user-specific sounds. HearAround: important sounds, made visible.”

## Recording checklist

- Preload YAMNet before recording so the download is not part of the video.
- Use the bundled car-horn sample for the main inference; keep a second sample ready.
- Close unrelated tabs and hide private bookmarks or notifications.
- Do not claim production readiness, medical benefit, sound direction, or certified emergency detection.
- Keep the failure disclosure in the video; it supports technical credibility.
- Add English captions even if the narration is Chinese.
