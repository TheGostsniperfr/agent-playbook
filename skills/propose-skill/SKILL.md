---
name: propose-skill
description: "Turn work an agent did twice into a skill proposal: detect repeated procedures (in this session, in harness-feedback issues, or with the repeat_scan.py transcript scanner), pick the right layer (generic base, org layer, project), draft the SKILL.md and open it as a PR with a one-line review card. Use when you notice you are doing the same multi-step thing a second time, when a correction from the owner repeats, when a harness-feedback run lists repeats, or when asked to propose skills."
compatibility: "Needs git and gh for the PR; the scanner needs read access to local agent transcripts (Claude Code, Codex)."
metadata:
  version: "1.0.0"
  author: "Brian Perret"
---

# Propose a skill ("done twice -> skill")

The rule: the second time an agent performs the same procedure, it stops and writes it down
once. The first time is learning; the second is a pattern; a third copy by hand is waste.

## 1. Detect (three sensors)
- **In session.** You are about to repeat a procedure you (or a report you read) already did:
  same commands in the same order, the same kind of document, the same fix. Note it in your
  final report under "Skill candidates" with both occurrences.
- **Transcripts.** `python3 scripts/repeat_scan.py --since <last run date>` lists command
  sequences repeated across at least two sessions (Claude Code and Codex JSONL, offline,
  deterministic). Ignore sequences an existing skill already covers.
- **Feedback loop.** The org's harness-feedback run (weekly or monthly) groups its issues; two
  issues describing the same manual procedure, or the same owner correction twice, are a
  candidate. Label them `skill-candidate`.

## 2. Decide if it earns a skill
Worth it when all hold: at least two real occurrences (links); more than ~3 steps or one hard
gotcha; stable enough to write down; not already a Makefile verb or script (prefer a script or
a `make` target for purely mechanical steps; a skill is for judgement plus steps).

## 3. Pick the layer
| The procedure is about... | Layer | Where |
|---|---|---|
| Any project (review pages, issues on other repos, handoff, publishing pattern) | Generic base | `agent-playbook/skills/<name>` |
| One org's stack, services or conventions (its auth server, its game mod, its infra) | Org layer | the org harness repo, as a `local:` skill or a patch |
| One repo only | Project | `.agents/skills-src/<name>` in that repo |
Generic text with org details mixed in: put the generic part in the base and the details in an
org patch. When unsure, start in the org layer and promote later.

## 4. Draft and propose
1. Write the skill in the open format (front matter `name`, `description` with the triggers,
   `metadata.version: "0.1.0"`): steps, gotchas met in the real occurrences, rules. Keep it
   under ~150 lines; move detail to `references/`.
2. Run the layer's checks (`agentskills validate`, the repo's `make check`) and
   `agentskills preview` so the PR shows the rendered result.
3. Open a PR in the chosen repo: title `feat(skills): <name> (from repeated work)`; body lists
   the occurrences (links), what the skill saves, and the layer choice in one line.
4. Add a small card to the owner's review stack (`review-stack` skill, inline decision
   "adopt / adopt in the other layer / drop", with `why`). Batch several proposals in one card.
Catalogue of candidates seen so far and their status: [references/candidates.md](references/candidates.md).

## Rules
- Never write a skill from one occurrence, except when the owner asks for it.
- A skill never carries secrets, private hostnames or unfixed vulnerability details: base
  skills may be public.
