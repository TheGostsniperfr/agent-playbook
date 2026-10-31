# review-stack changelog

## 1.0.0 (2026-10-29)
- First version in agent-playbook.

## 1.1.0 (2026-10-31)
- Stack page: approving or "Later" collapses the card, opens the next ready card and scrolls to
  it with an unfold transition (synced from the live Arffornia stack; keeps `safeUrl`).
- Decisions must be readable cold: `why` is required (schema and `--lint-card` for stack
  cards), context has a minimum length, and known jargon must be explained in plain words.
- Dictation hints: macOS "press Fn twice"; Linux pointer to `references/voice-input.md`.

## 1.1.1 (2026-10-31)
- Fix (stack page): after a radio click, `render()` restored focus and called
  `setSelectionRange` on the radio, which throws, so the `save()` after it never ran: choices
  looked clicked but were never stored and came back as before on reload. Focus restore now
  only touches text fields, inside `try/catch`; handlers save before rendering; `render()` catches
  its own errors and shows them.
- Stack page: save status per card ("Saving…", "Saved", red "Not saved (...)") survives
  re-renders, and a failed write also shows a page alert.
- Chantier page: a synchronous throw from the db call is caught like a rejected one, so the status
  never sticks on "Saving..." and later saves are not blocked.
- New `tests/test_browser.py` + `tests/browser_save.js`: headless regression test (skipped without
  Node and Playwright). New rule: a render error must never swallow a save.
