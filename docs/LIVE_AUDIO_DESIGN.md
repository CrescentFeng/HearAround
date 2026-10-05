# HearAround live audio design

## Data flow

```text
getUserMedia microphone
  -> AudioWorklet mono PCM frames
  -> rolling in-memory buffer (about 5 seconds)
  -> latest 3-second window every 1.5 seconds
  -> client-side PCM16 WAV encoding
  -> POST /api/analyze
  -> YAMNet + deterministic policy + Agent cooldown
  -> visual, vibration and optional speech alert
```

## Safety and privacy boundaries

- Environment classification always receives the full audio stream; a future VAD must not remove alarms, horns or impacts.
- The browser keeps only a rolling buffer and discards it when monitoring stops or the page closes.
- The server decodes each request in memory and does not write uploaded audio to disk.
- Only event metadata and explicit user correction are retained in session memory.
- Overlapping windows improve transient-event coverage; server-side cooldown prevents repeated alerts.

## Runtime behavior

- Live capture is blocked with an explicit explanation outside HTTPS or localhost secure contexts.
- The technical view reports secure-context, microphone/AudioWorklet, vibration and speech-synthesis support before permission is requested.
- Capture requests mono audio with echo cancellation, noise suppression and automatic gain control disabled where supported.
- The browser's native sample rate is preserved in the WAV header; the backend resamples to 16 kHz.
- Only one analysis request is allowed in flight. If inference is slower than the hop interval, new sends wait rather than queueing indefinitely.
- Near-silent chunks are treated as a quiet environment, not a fatal error.
- A stopped or disconnected microphone closes the `AudioContext`, stops every track and clears buffered frames.

## Manual acceptance test

1. Click **Start live monitoring** and explicitly allow microphone access.
2. Confirm the status changes from permission request to live monitoring.
3. Wait 3 seconds and confirm analysis cycles appear without page flicker.
4. Play a licensed smoke-alarm sample from a second device and confirm a critical alert appears.
5. Keep the sound playing and confirm cooldown suppresses repeated vibration.
6. Click **Pause live monitoring** and confirm the status says the memory buffer was cleared.
7. Deny permission once and confirm uploaded and built-in sample paths still work.
