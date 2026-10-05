# HearAround — Important sounds, made visible

> Replace `[LIVE_DEMO_URL]` and `[VIDEO_URL]` before submission.

## One-line pitch

HearAround is a privacy-conscious environmental-sound Agent that turns important sounds into large pictograms, clear visual alerts, optional vibration, and spoken guidance for people who cannot reliably hear or read a text-only notification.

## Inspiration

HearAround began with my grandmother. As she grows older, her hearing has gradually declined, affecting both her independence and her safety. She also has limited literacy, so a transcript-only product would not fully solve the problem. I wanted to create an assistant that communicates through several simple channels at once: recognizable pictures, color plus shape, short words, vibration when available, and optional speech.

That personal observation led to a broader design goal: support people who are Deaf or hard of hearing, older adults with age-related hearing loss, people who find dense text difficult, and the caregivers who support them.

## The problem

Everyday sounds often carry urgent context: a smoke alarm, an emergency siren, a car horn, a baby crying, a doorbell, or knocking. Conventional accessibility tools may rely on text, treat every event with the same urgency, or provide little explanation for why an alert appeared. A usable assistant must also avoid repeated alert fatigue, protect ambient conversations, and stay honest about uncertain model output.

## What HearAround does

HearAround accepts a live microphone stream, a user-uploaded audio file, or one of the bundled license-traceable samples. It runs real YAMNet inference over AudioSet's 521 classes, maps model evidence into six product events, applies deterministic safety rules, and lets one stateful Agent manage context, cooldown, environment mode, feedback, and an explainable decision trail.

The interface offers two layers:

- **Simple mode** uses large pictograms, short actions, color plus shape, optional speech, and progressive vibration.
- **Technical mode** exposes model candidates, rule evidence, Agent decisions, browser capability checks, and evaluation results for reviewers.

## Key features

- Six meaningful sound events: smoke/fire alarm, emergency siren, car horn, baby crying, doorbell, and knocking.
- Real YAMNet AudioSet 521 inference; interaction previews are clearly separated from model results.
- Browser microphone capture through AudioWorklet, a five-second in-memory rolling buffer, overlapping analysis windows, and single-request backpressure.
- Safety-first deterministic alert rules. An LLM is not allowed to freely decide whether a critical warning should fire.
- A single stateful Agent for environment mode, event history, cooldown suppression, user confirmation, and correction feedback.
- Accessible communication through large icons, short instructions, high contrast, optional text-to-speech, and vibration where the browser supports it.
- Privacy by default: raw audio is analyzed in memory and is not saved to event history.
- Reproducible, source-linked evaluation artifacts rather than unsupported accuracy claims.

## How it works

```text
Microphone / audio file / licensed sample
  → AudioWorklet capture and WAV slicing (for microphone input)
  → mono decoding and 16 kHz resampling
  → YAMNet window inference
  → AudioSet-to-product label mapping
  → repeated-window aggregation or high-confidence transient path
  → deterministic alert policy
  → stateful HearAround Agent
  → pictogram, short action, optional vibration and speech
```

The Agent does not expose hidden chain-of-thought. The reviewable trail contains only verifiable evidence: detected label, model score, matched rule, cooldown state, and resulting action.

## Technology

- Front end: responsive HTML, CSS, and JavaScript with Web Audio API and AudioWorklet.
- API: Python, FastAPI, multipart audio endpoints, same-origin static delivery.
- ML: TensorFlow Hub YAMNet, AudioSet 521 label ontology, NumPy/SciPy/SoundFile preprocessing.
- Agent: a deterministic, stateful single-Agent orchestrator with YAML-configured label and alert policies.
- Quality: Python unit and API integration tests, independent holdout evaluation, sequential inference stress test, Docker packaging, CSP and privacy headers.

## Who it is for

HearAround is designed for a spectrum rather than a single diagnosis: Deaf and hard-of-hearing users, older people with acquired hearing loss, users with limited literacy or cognitive load constraints, and caregivers. Users can rely on the modality that works for them; spoken guidance is an optional complement for people with partial hearing and is never the only alert channel.

## Accessibility and privacy choices

- Severity is never communicated by color alone; icons, labels, shapes, and actions accompany it.
- Visual alerts remain the baseline when vibration or speech synthesis is unavailable.
- The browser requests microphone permission only after an explicit user action and keeps a visible listening state.
- Microphone audio is held in a rolling memory buffer of about five seconds and cleared when monitoring stops.
- The application stores event metadata and feedback, not the raw recording.
- The product does not claim sound direction from a single microphone.

## Evaluation

The bundled 20-clip licensed demo set is used only as a development smoke test. A separate 23-clip CC0 holdout is independent by source ID and was evaluated after the rules were frozen.

- Holdout exact match: **65.2%**
- Holdout Macro-F1: **62.8%**
- Difficult negatives causing a product alert: **0/6**
- Critical-event misses: **2/6**
- Sequential inference stress test: **230 runs, 0 exceptions, 0 output drift**
- Known primary failure: **doorbell recall is 0/3**

These are small-hackathon-set engineering results, not population-level accuracy, medical evidence, or safety certification. The doorbell failure is intentionally disclosed instead of being hidden by tuning on the holdout set.

## Challenges

The hardest part was not calling a model; it was translating noisy frame-level evidence into calm, accessible behavior. Transient sounds need a fast path, repeated events need confirmation, uncertain alerts need careful wording, and cooldown must reduce fatigue without suppressing critical safety information. A second challenge was creating an online-only, license-traceable evaluation set without self-recorded audio.

## Accomplishments

- Built a complete real-inference path from microphone/file input to accessible alert.
- Kept emergency decisions outside free-form language-model judgment.
- Made evaluation evidence, failure cases, and privacy boundaries visible to reviewers.
- Preserved usability for older and low-literacy users instead of treating captions as the entire solution.

## What I learned

Accessible AI is a communication system, not only a classifier. A modest model with explicit safety, privacy, and interaction boundaries can be more trustworthy than a larger model wrapped in an opaque interface. I also learned that a useful Agent can be a small stateful orchestrator: it earns its role through tool coordination, memory, and policy—not through unrestricted autonomy.

## What's next

1. Collect a new development set for doorbells and knocking, then recalibrate without touching the frozen holdout.
2. Add optional VAD and live captions while keeping environment-sound detection independent.
3. Package the interface as an Android/iOS app for reliable background capture and haptics.
4. Connect to smartwatches, wristbands, bedside lights, and home gateways for stronger multimodal alerts.
5. Move more inference on-device and allow consent-based personalization for a user's own doorbell or appliance sounds.
6. Run co-design and usability studies with Deaf/hard-of-hearing users, older adults, and caregivers.

## Project links

- Live demo: [LIVE_DEMO_URL]
- Source repository: https://github.com/CrescentFeng/HearAround
- Demo video: [VIDEO_URL]

## Safety boundary

HearAround is an experimental accessibility prototype. It is not a medical device, a certified alarm, or a replacement for smoke detectors, emergency services, or situational awareness.
