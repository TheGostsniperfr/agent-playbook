# review-stack changelog

## 1.0.0 (2026-10-29)
- First version in agent-playbook.

## 1.1.0 (2026-10-31)
- Stack page: approving or "Later" collapses the card, opens the next ready card and scrolls to
  it with an unfold transition (synced from the live Arffornia stack; keeps `safeUrl`).
- Decisions must be readable cold: `why` is required (schema and `--lint-card` for stack
  cards), context has a minimum length, and known jargon must be explained in plain words.
- Dictation hints: macOS "press Fn twice"; Linux pointer to `references/voice-input.md`.
