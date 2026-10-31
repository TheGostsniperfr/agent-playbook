# Continuity pack

Default in every project set up with this playbook (`bootstrap` item 1, `new-project` step 0).
Goal: a brand-new chat or agent, on any surface (Claude Code, claude.ai, Codex, OpenCode),
recovers the full working context in seconds, without the owner retyping anything.

| Piece | Where | Written by | Read by |
|---|---|---|---|
| `STATE.md` (rules in force, active chantiers, decisions, open questions, owner wishes, owner actions, links) | private `<org>/ops` repo, `main` | `handoff` (end of task, PreCompact, SessionEnd) | `resume` |
| `START-HERE.md` (who, how we work, where state lives, how to resume) | claude.ai Project docs, and `ops/README.md` | `bootstrap`, updated by `handoff` when rules change | every new chat |
| Copy of `STATE.md` | claude.ai Project docs (`claude/STATE.md`) | `handoff`, when the session can write Project docs | claude.ai chats |
| Review stack page | artifact with a db (`chantiers`, `answers`) | agents | owner, then `resume` |
| "Resuming" line | every repo's AGENTS.md | `bootstrap` | coding agents |
| SessionStart hook | org layer (agent-kit or equivalent) | `bootstrap` | coding agents, automatically |
| Global instruction | user-level `CLAUDE.md` / Codex `AGENTS.md` / OpenCode `AGENTS.md` (installed by the Nix module or `install.sh`) | playbook | every session on the owner's machines |

## Rules
- Never put private state in a public repo: STATE goes to the private ops repo or Project docs.
- `handoff` runs at the end of every chantier report, not only at the end of a session.
- If the ops repo does not exist yet, keep STATE in the Project docs and put "create `<org>/ops`"
  on the owner's first review card.
- `resume` checks STATE against GitHub (`state_lint.py --live`) and briefs the owner in at most
  ten lines before doing anything.
