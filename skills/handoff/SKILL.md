---
name: handoff
description: "Write the project's live state so a brand-new chat can resume without this conversation: distil decisions, rules, active chantiers, links and next steps into STATE.md in the private ops repo, mirror it to the chat-project docs and point the review stack at it. Use at the end of a session or a long chat, before context is compacted, when the owner says they stop or will resume later ('on s'arrête là', 'je reprends demain', 'wrap up', 'save where we are', 'handoff'), or when asked to make a new chat able to continue."
compatibility: "Needs git push access to the ops repo, or the owner pastes the file. Works in Claude Code, claude.ai (with a GitHub or docs connector) and Codex."
metadata:
  version: "1.0.0"
  author: "Brian Perret"
---

# Handoff

The next session starts with no memory of this one. Everything it needs must be in files, found
from one entry point. Where things live and the `STATE.md` template:
[references/state-format.md](references/state-format.md). The reader is the `resume` skill.

## Steps
1. **Find the state file.** The ops repo named in the repo's AGENTS.md ("Live project state:"),
   else `<org>/ops`, else ask the owner once. If it does not exist, write `STATE.md` in your
   scratch directory and add "create the private ops repo" to the owner actions (exact steps:
   GitHub > New repository > owner `<org>`, name `ops`, Private, no template).
2. **Collect, do not recall.** Re-read the sources instead of trusting memory: the reports and
   notes of this session, the review stack (`chantiers` and `answers`), open PRs and issues you
   touched (`gh api repos/<o>/<r>/pulls?state=open`), the owner's latest messages. For a long
   chat, list the owner's messages oldest to newest and extract every wish, rule and decision:
   a small wish that is not written down is lost.
3. **Distil** into the template. For each chantier: status, what it waits on, full links, next
   step. For each decision: date, choice, where it is recorded. Rules keep the owner's wording.
   Proposals never expire: move stale ones to "Proposed chantiers" with their date.
4. **Check before writing.** Every URL is full https; no secret, token, internal hostname or
   unfixed vulnerability detail; under ~300 lines (move detail into linked files);
   `python3 scripts/state_lint.py STATE.md` passes.
5. **Write.** Commit `STATE.md` to the ops repo (`docs(state): <one line>`; normal push, never
   force). Update the copy in the chat-project docs when that tool is available; otherwise put
   "refresh the Project doc copy of STATE.md" in the owner actions.
6. **Point to it.** The review stack's footer or first card links the state file; each public
   repo's AGENTS.md has the one-line pointer.
7. **Tell the owner** in three lines: what was done, what is next, what only they can do.

## Rules
- One state file per project (org), not per repo. Repo-local progress stays in the repo's
  PROGRESS.md and is linked from STATE.md.
- Never paste raw transcripts. Summaries with links only.
- If two sessions wrote the file, merge both; never drop the other session's lines silently.
