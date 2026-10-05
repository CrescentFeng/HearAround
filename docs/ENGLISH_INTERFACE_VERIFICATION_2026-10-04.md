# HearAround English interface verification

Date: 2026-10-04 (Asia/Shanghai)

## Scope

The competition-facing interface is English-first. Translation covers static content and runtime content, including scenarios, model status, microphone states, Agent evidence, evaluation notes, feedback, error messages, API event names, suggested actions, policy reasons, accessibility labels, and speech synthesis.

## Passed checks

- Public document language is `en`.
- No Han characters remain in `dist/index.html`, `dist/assets/app.js`, `backend/app/`, or `config/`.
- Front-end assets use the `v=0.6.0` cache key so judges do not receive stale Chinese JavaScript.
- Automated suite: **20/20 passed**.
- Real YAMNet car-horn inference returned English event name, message, suggested action, policy reason, and notice.
- Browser simple mode displayed English-only application content.
- Browser technical mode displayed English Agent trace, model evidence, evaluation disclosure, and capability status.

Native browser media-control labels may follow the evaluator's operating-system language. Those controls are browser chrome, not HearAround application copy.
