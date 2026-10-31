# Start here: set up the method on a repo, an org, or a new idea

Point any agent (Claude Code, claude.ai, Codex) at this page:

> Read https://github.com/TheGostsniperfr/agent-playbook/blob/main/runbook/START.md and set up
> the method on this repo / this org.

The agent then picks one of three paths.

| Situation | Path | Skill |
|---|---|---|
| The project already has live state (an ops repo with `STATE.md`) | Resume it | [`resume`](../skills/resume/SKILL.md) |
| The repo or org exists but has no method yet | Chantier 0: propose and run the standard setup | [`bootstrap`](../skills/bootstrap/SKILL.md) |
| Only an idea | Interview, vision, ADRs, M0 spec, then bootstrap | [`new-project`](../skills/new-project/SKILL.md) |

## If the skills are not installed
Read the `SKILL.md` files from GitHub directly (they are plain Markdown), or install them:
- Nix/home-manager: `programs.agent-playbook.enable = true` (see `skills/DESIGN.md`).
- Anything else: `sh overlay/install.sh` from a clone; skills appear as `/playbook:<name>`
  in Claude Code and `playbook-<name>` in Codex and OpenCode.

## What the owner gets at the end of Chantier 0
- A private ops repo with `STATE.md`: the one file a fresh chat reads to continue.
- A review stack page: the queue of chantiers to validate, decisions with defaults.
- In each repo: README, AGENTS.md map, `make check`, CI with deterministic guards, templates.
- Docs as code with generated diagrams; an org profile; agent-ready issues; a board with lanes.
- The harness: an org layer on top of this playbook, per-repo overlays, the end-of-task review.
- Automations: a weekly brief, monthly upkeep, skipped when nothing changed.
The workflow everyone follows: [WORKFLOW.md](WORKFLOW.md).
