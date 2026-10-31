# Phase 9 · Continuous improvement and tech watch

**Goal:** every run makes the harness, the skills and this runbook a little better, entropy is
fought on a schedule, and the owner learns the best techniques without having to dig.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Where improvement notes go | Small and certain: patch the skill, rule or runbook page in the same session (own PR). Bigger or uncertain: an issue labelled `harness-feedback` in the harness repo | Notes in chats are lost; issues are triaged like work |
| What triggers a note | The owner corrects an agent; a guard blocks something legitimate; a review finding is wrong; the same mistake happens twice; a tool or doc was out of date | These are the failures that repeat |
| Failures become tests | Each reverted PR or wrong review finding becomes an eval case (`evals/`); each repeated mistake becomes a sensor | Regression-proof the harness |
| Skill candidates | "Done twice -> skill": note repeats in the final report, run `propose-skill`'s `repeat_scan.py` over transcripts in the harness-feedback run, label repeated issues `skill-candidate` | The second manual copy of a procedure is the signal |
| Cadence and cost | Brief weekly (Friday evening, ready Saturday morning); every non-critical recurring task monthly; skip a run when nothing changed since the last one (commits, issues, PRs); one manual "run everything now" | Token budget on a personal project; a month off must not cost four empty runs |
| Self-improvement | A monthly watch run reads release notes and engineering posts and proposes patches to the base or org layer as PRs, with a learning card | New practices reach the skills without the owner digging |
| Scheduled agents | brief, doc gardener, dependency upgrades (one PR per library), review feedback → evals, harness audit, security audit, onboarding audit, quality score | Entropy grows without anyone asking |
| Guardrails for scheduled agents | Read-only except one destination, bookmark, budget cap 3-5x a normal run, draft PRs only, "could not read" is never "nothing new", trifecta card | Unattended runs must fail loudly and cheaply |
| Metrics | Time to first green, first-pass CI success, review rounds, revert rate, useful vs wrong review findings, human minutes per chantier | Measure the harness, not the model |
| Tech watch for the owner | One **learning card** per impressive technique used or found: what it is, how it works here, the state of the art, how to push further, sources | The owner wants to learn and stay ahead, not only receive PRs |

## Steps (agent)

1. At the end of every task, before the final report, ask: did anything surprise me, block me,
   or get corrected? If yes, write the note (patch or `harness-feedback` issue) now.
2. Monthly harness audit: read the `harness-feedback` issues, the eval results and the metrics;
   propose sensors for repeated failures and delete rules the model no longer needs.
3. When a model or tool version changes, re-run the evals and try removing one harness component
   at a time; keep what still earns its cost.
4. Write a learning card when a run uses something non-obvious (headless animation preview,
   GameTests in CI, frozen architecture baselines) or when research finds an idea worth trying.
   Cards go to `veille/`; rank new ideas in [IDEAS.md](../IDEAS.md).
5. Weekly: one digest for the owner with new cards, metric trends and the top 3 ideas.

## Human touchpoints

- Read the weekly digest. Promote ideas into proposals. Correct agents freely: every correction
  becomes a durable change.

## Anti-patterns we hit

- **The owner's corrections lived only in the chat** (link format, review style). They were
  saved to memory and propagated by hand. Write them to the rules file and the harness at once.
- **"Nothing new" when a source was unreadable.** Scheduled agents list what they could not read.
- **Stale READMEs in every repo** at audit time: docs drift silently without a gardener.
- **Lessons buried in long reports** (Noodle export limit, composer disk fill). Lift each one into
  the runbook page it belongs to, in the same session.

## Checklist

- [ ] Final report has a "harness notes" line (or "none")
- [ ] `harness-feedback` label exists in the harness repo; issues triaged monthly
- [ ] Each scheduled agent has guardrails, a bookmark and a trifecta card
- [ ] Metrics written somewhere a scheduled agent can read
- [ ] At least one learning card per significant chantier
