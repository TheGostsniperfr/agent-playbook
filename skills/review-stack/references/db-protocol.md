# review-stack database protocol (chantier/v1)

The page declares `capabilities: {"db": {}, "user": {}}`. Default db rules apply: signed-in viewers
with access read; Contributors and up write; Viewers and Commenters cannot write (the page then
shows "Answers cannot be saved in this view" and offers "Copy my answers").

## Chantier page

| Path | Written by | When | Fields |
|---|---|---|---|
| `answers/<decision id>` | the page | a choice changes, or 0.9 s after typing stops, or on blur | `chantier` (id), `decision`, `choice` (option id or `"other"`), `text`, `by` (opaque user id), `at` (ISO time) |
| `verdict/current` | the page | Approve / Needs changes / Hold | `chantier`, `status` (`approved`, `changes`, `hold`), `note`, `answers` (`{<decision id>: {choice, text}}` for every decision, defaults included), `by`, `at` |

- Untouched decisions have no `answers/` doc: their value is the default. `verdict/current.answers`
  is the complete picture at the moment of the verdict.
- A later verdict overwrites the previous one. A changed answer after the verdict updates only
  `answers/<id>`: compare `at` values and ask again if an answer is newer than the verdict.
- Docs carry `chantier` so a page reused for a new chantier ignores old rows.
- Read with `ArtifactData`: `get` `verdict/current`; `list` collection `answers`.

## Stack page

| Path | Written by | Fields |
|---|---|---|
| `chantiers/<id>` | agents | `order` (int), `title`, `summary`, `status` (`building`, `ready`, `done`), optional `detail`, `links` (`[{label, url, note?}]`), `decisions` (`[{id, q, why?, options: [string], default}]`, the page adds "Other") |
| `answers/<id>` | the page (or an agent mirroring a page verdict) | `verdict` (`approve`, `changes`, `later`, or empty), `notes`, `decisions` (`{<id>: {choice, other?}}`), `at` |

Cards sort by state (ready, later, building, done/approved), then `order`.

## Why these choices
- A doc per decision keeps writes small and lets two people answer different decisions at once.
- The verdict snapshot gives the orchestrator one read with no default-resolution logic.
- No `rules` override: the owner and agents must be able to tidy rows.
