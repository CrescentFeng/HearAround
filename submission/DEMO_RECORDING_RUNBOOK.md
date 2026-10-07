# HearAround demo recording runbook

Target: one English 2:42 video at 1920 × 1080, 30 fps, with captions. Use the public Hugging Face deployment and the prepared narration track.

## Before recording

1. Close unrelated tabs, notifications, bookmarks, and account menus.
2. Open `https://crescentfff-heararound-agent.hf.space/` at 100% browser zoom.
3. Confirm the banner says `Real recognition service is ready`.
4. Start in **Simple mode**, **Home mode**, **Speech: off**, normal contrast, with no event history.
5. Select `Car horn · horn_car_cc0`, click **Load this sample**, and verify the CC0 attribution appears.
6. Do not start microphone monitoring during the main recording; the licensed sample is reproducible and avoids permission interruptions.

## Recording sequence

| Time | Screen action | Evidence shown |
| --- | --- | --- |
| 0:00–0:18 | Hold on the hero, brand, and simple mode | Human motivation and product promise |
| 0:18–0:38 | Point out privacy, speech, contrast, and mode controls | Multimodal accessibility and privacy |
| 0:38–0:48 | Scroll to the licensed sample and briefly play it | Real source-linked audio |
| 0:48–1:08 | Click **Analyze sound** and wait for the car-horn alert | Real model badge, pictogram, action, severity |
| 1:08–1:18 | Immediately click **Analyze sound** again | Ten-second cooldown is still active |
| 1:18–1:42 | Switch to **Technical mode** and show `Duplicate alert avoided` plus the four-step trail | State, rule, suppression, action |
| 1:42–2:02 | Toggle high contrast, show speech control and browser capabilities | Accessibility layers and graceful fallback |
| 2:02–2:27 | Scroll to implementation evidence and the safety boundary | Honest metrics and disclosed failures |
| 2:27–2:42 | Return to simple mode and the product statement | Closing vision |

## Files already prepared

- Narration text: `submission/DEMO_VOICEOVER_EN.txt`
- English captions: `submission/DEMO_CAPTIONS_EN.srt`
- Synthetic English guide track: `submission/media/hearound-demo-voiceover-en.mp3`
- Thumbnail: `submission/media/hearound-devpost-thumbnail.png`
- Final assembly script: `scripts/build_demo_video.sh`

The synthetic track is a timing guide and fallback. A clear human narration is preferred if available.

## Assemble the final video

Save the clean screen recording as:

```text
submission/media/hearound-screen-recording.mp4
```

Then run:

```bash
./scripts/build_demo_video.sh
```

The script creates `submission/media/hearound-demo-final.mp4` with the prepared English narration and burned-in English captions.

## Acceptance checks

- Video is between 2:30 and 3:00 and plays from beginning to end.
- `Real model` is visible during inference; preview buttons are never presented as model results.
- The second car-horn analysis occurs within ten seconds and shows cooldown suppression.
- No personal tabs, notification banners, account details, or API keys are visible.
- Text remains readable on a 1280-pixel-wide player.
- Audio peaks below clipping and narration is understandable on phone speakers.
- The public video is unlisted or public, not private, and works without login.
