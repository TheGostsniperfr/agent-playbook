# Phase 8 · Product work

**Goal:** features arrive at the owner already specified, built, tested in the real app and
shown visually, so the owner approves intent and look, not code.

## The flow

```
intent (owner, voice ok) → spec (agent, docs/specs/) → owner approves spec + visual mock
  → exec plan (agent, repo) → implementation in worktrees → verify in real app (screens, GameTests)
  → in-session review → chantier page → owner validates → orchestrator merges
```

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Spec depth | Scale to size: bug = issue with acceptance criteria; feature = spec page; system change = spec + ADR | Heavy spec frameworks are overkill for small changes |
| Where specs live | `docs/specs/` in the docs repo, kept after the feature ships (spec-anchored) | Next change starts from the spec, not from code archaeology |
| Design choices | `needs-decision` issue with options and a recommended default; never decided in code | Owner's long-lived design |
| Visual validation | Mock first (static render, animation preview, screenshots in both locales), owner approves, then build; the same renders become regression checks | The owner validates look and feel; agents need a target |
| i18n | Every user-visible string through i18n from the first commit, `en` + `fr`, including API and JSON messages; no text in images | Retrofitting cost a full chantier per app |
| Content vs tooling | Separate PRs ("content" label) for data the live system reads (modpack lists) | Main of that repo is live for every player |
| Long features | Exec plan in `docs/exec-plans/active/` with a decision log and verification evidence | Survives sessions and compaction |
| Test environments | Later: per-PR preview servers ([ADR-0007](https://github.com/Arffornia/docs/blob/main/docs/decisions/0007-preview-environments.md)), after secret isolation | Parallel features each need a running server |

## Steps (agent)

1. Turn the owner's intent into a spec: problem, players affected, behaviour, acceptance
   criteria, out of scope, open questions (with defaults).
2. Produce the visual: mock, animation preview or screenshots; publish it on the chantier page.
3. After approval, write the exec plan; split into issues with blockers; implement in worktrees.
4. Verify in the real app: GameTests and screenshots for the mod, Playwright for web and launcher,
   both locales. Attach evidence.
5. Review in-session, fix, open PRs, assemble the chantier.

## Human touchpoints

- Approve the spec and the visual (two clicks plus optional voice notes). Validate the chantier.

## Anti-patterns we hit

- **Hardcoded strings outside UI code**: API messages, JSON config, provisioning data. The i18n
  lint must cover data files and API responses, not only templates.
- **A new feature PR added an English-only notification** while the i18n chantier was open.
  The i18n rule belongs in the guard and the reviewer, not only in docs.
- **Text in PNGs** and generated GUIs: keep text as data so it can be translated.
- **Wrong brand mark** in generated diagrams. Ask for brand assets before drawing.
- **Feature ideas from agents mixed with work**: file them as `proposal`; only the owner promotes.

## Checklist

- [ ] Spec approved before code; spec kept and linked from the PRs
- [ ] Visual approved; screenshots in both locales attached
- [ ] No user-visible literal outside locale files (lint green)
- [ ] Verified in the real app; evidence on the chantier page
- [ ] Content PRs separate from tooling PRs
