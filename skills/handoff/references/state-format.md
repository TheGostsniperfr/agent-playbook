# Live state: where it lives and what the state file holds

A fresh chat (Claude Code, claude.ai, Codex, any agent) must rebuild the project's context from
files, never from a previous conversation. Three places hold the live state, each with one job:

| Place | Job | Who reads it |
|---|---|---|
| **State file** `STATE.md` at the root of a private ops repo (`<org>/ops`, or `<owner>/<project>-ops` for a personal project) | The single entry point: what is going on, what was decided, what is next, every link | Any agent with git access; the owner |
| **Review stack** (one long-lived page, e.g. a claude.ai artifact with a database) | The owner's queue of chantiers waiting for a verdict, and their answers | The owner (daily), agents (read answers) |
| **Chat-product project docs** (e.g. a Claude Project's docs) | A copy of `STATE.md` for chats that cannot read the private repo | claude.ai chats |

Public repos never hold the live state: they may become public or already are. They hold the
durable, shareable part (AGENTS.md, docs, ADRs, PROGRESS.md for repo-local work) and point to
the ops repo in one line of AGENTS.md: "Live project state: `<org>/ops` STATE.md (private)".

## Rules for STATE.md
- **Distilled, not a log.** It answers "what would I need to know to continue right now?".
  History goes to git (`git log STATE.md`) and to the chantier issues. Target: under 300 lines.
- **Links, not claims.** Every PR, issue, page or artifact is a full https URL with a one-line
  summary. A fresh agent verifies the live status from the link; the file may be stale.
- **Dated.** The front matter says when it was last written and by which session.
- **No secrets, no unfixed vulnerability details** (the ops repo is private, but copies travel:
  project docs, pasted chats). Name the weakness neutrally and link the private issue.
- **Decisions are final once recorded.** A later change adds a new line ("superseded by ...").
- **Owner's words win.** Rules the owner stated keep their wording (translated if needed), with
  the date. Agents do not soften them.

## Template
```markdown
---
project: <name>
updated: <YYYY-MM-DD>
by: <session or agent link>
ops_repo: https://github.com/<org>/ops
review_stack: <URL>
---
# <Project> state

## Start here
Three to five lines: the exact next actions, specific enough to act on without rereading.

## Rules in force
Owner's standing rules, numbered, each with its date and source (link). Link STANDARDS/
GOLDEN files instead of copying them when they exist.

## Active chantiers
| Chantier | Status | Waiting on | Links (full URLs) | Next step |

## Decisions taken
| Date | Decision | Where it is recorded |

## Open questions for the owner
Each with the recommended default and where to answer (review stack card id).

## Proposed chantiers (not started)
Never expire. Dormant ones stay listed with the date they were proposed.

## Resources and constraints
Machines, budgets (money, tokens, time), what is often offline, access the agents lack.

## Key links
Org, repos, board, docs site, review stack, design pages, dashboards.

## Owner actions (only the owner can do these)
Step-by-step, each with why and what it unblocks.

## Where to find more
Report folders, audits, runbook, harness repo, chat-project docs.
```
