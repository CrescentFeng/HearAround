# HearAround judging matrix

This matrix maps the published judging weights to concrete review evidence. Confirm the final rubric on Devpost immediately before submission.

| Criterion | Weight | What the judge should notice | Evidence in the project | Demo moment |
| --- | ---: | --- | --- | --- |
| Technical implementation | 30% | End-to-end real inference, policy separation, state, backpressure, tests, deployment boundary | `backend/app/`, `config/`, `backend/tests/`, `eval/`, `Dockerfile` | 0:38–1:42 |
| Creativity and originality | 20% | Agent combines sound evidence with safety rules and multimodal low-literacy communication | Simple/technical modes, pictograms, deterministic/Agent split | 0:00–0:38 |
| Impact and relevance | 20% | Personal inspiration plus a broad, clearly defined accessibility audience | Devpost Inspiration and Who it is for | 0:00–0:38 |
| User experience | 15% | Large targets, short actions, high contrast, color-independent severity, optional speech/vibration | `dist/`, live capability panel | 1:42–2:02 |
| Presentation and documentation | 15% | Reproducible samples, disclosed metrics and failures, privacy and safety boundaries | `README.md`, `docs/`, `submission/`, `/api/project` | 2:02–2:42 |

## Fast reviewer path

1. Open the public HTTPS URL.
2. Press **Load model** if it is not already ready.
3. Select the built-in car-horn CC0 sample and run real inference.
4. Switch to technical mode and inspect the evidence trail.
5. Run the same sample again to see stateful cooldown.
6. Review the holdout metrics and the disclosed doorbell failure.

## Claims reviewers can verify

- `/api/health` reports service and model state.
- `/api/project` exposes the stable project/submission facts.
- `/api/evaluation` exposes aggregate holdout and stress results without serving holdout audio.
- Raw audio does not appear in event history or feedback data.
- The six scenario buttons say interaction preview; uploaded and bundled audio run the real model.
