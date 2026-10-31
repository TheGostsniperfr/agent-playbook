# How it works

## Three layers of skills

![Skill layers](diagrams/layers.light.drawio.svg#only-light)
![Skill layers](diagrams/layers.dark.drawio.svg#only-dark)

The personal base (this repo) holds generic skills. An org layer patches them and adds org-only
skills. A project layer pins versions and adds its own patches. The `agentskills` resolver
applies them in order and writes plain files for Claude Code, Codex and OpenCode, plus a
lockfile. Plain-words explanation: [the three layers](overlay/README.md); design:
[skills/DESIGN.md](skills/DESIGN.md).

**The render is the truth.** Like rendered Kubernetes manifests, the rendered skill folders are
exactly what an agent reads. `agentskills export` writes that full build; `agentskills preview`
shows the rendered diff of any change, and CI posts it on every PR.

## The workflow

![Workflow](diagrams/workflow.light.drawio.svg#only-light)
![Workflow](diagrams/workflow.dark.drawio.svg#only-dark)

Seven steps: agents propose, spec, implement and open PRs, review; the owner checks what needs
a human and validates the chantier; agents merge and deploy. Full rules:
[runbook/WORKFLOW.md](runbook/WORKFLOW.md).

## Where state lives

| Place | Holds |
|---|---|
| Public repos | Code, docs, ADRs, AGENTS.md (with a pointer to the ops repo) |
| Private ops repo `STATE.md` | Live project state: chantiers, decisions, rules, links, next steps |
| Review stack page | The owner's queue and answers |
| Chat-project docs | A copy of `STATE.md` for chats without repo access |

Pattern: [live state](runbook/patterns/live-state.md).

## Guards and review

Deterministic guards (types, lint, architecture rules, security patterns, secrets, shell and
workflow linters, mutation where cheap) run in `make check` and CI:
[patterns/deterministic-guards.md](runbook/patterns/deterministic-guards.md). The end-of-task
review (independent finders and verifiers inside the agent's session, no API key in CI) looks
for the rest.

## Getting better over time

- **Done twice, make it a skill**: [`propose-skill`](skills/propose-skill/SKILL.md) detects
  repeated work (in the session, in transcripts, in feedback issues) and proposes a skill in
  the right layer.
- A monthly watch run proposes updates to the base and org layers from new practices; learning
  cards land in [tech watch](veille/README.md).
- Automations run weekly or monthly and skip when nothing changed.
