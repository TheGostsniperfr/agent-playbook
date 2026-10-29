# Adapting the runbook

The runbook was written on a one-person project with twelve repos. The same phases work for a
company; what changes is **who decides, at which scope, and how many chantier queues exist**.

## Project or company

| Topic | Single project (Arffornia) | Company with teams |
|---|---|---|
| Decision owner | One maintainer | Per scope: org (platform/CTO), team (tech lead), repo (code owners) |
| Rules file | One `STANDARDS.md` | Org standards + team addendum + repo AGENTS.md |
| Tracker | One org Project | One Project per team plus an org roadmap view |
| Chantier queue | One owner queue | One queue per decision owner; cross-team chantiers go to the org queue |
| Harness | One plugin | Base plugin (org) + team overlays + repo overlays |
| ADRs | One docs repo | Org ADRs in a central repo; team ADRs in team docs; each says its scope |
| Audits | Per component | Per team first, then cross-team dependencies and shared platform |
| Merge authority | Owner validates, orchestrator merges | CODEOWNERS approve per repo; orchestrator merges validated chantiers within its scope only |
| Security | Owner rotates | Security team owns disclosure, rotation and trifecta approvals |

## Scopes and overlays

Three layers, each referencing the one below and adding only a patch:

| Scope | Holds | Lives in |
|---|---|---|
| **Personal / generic** | Generic skills (review page, chantier page, design style, runbook) | `agent-playbook` (this repo), linked from the owner's dotfiles |
| **Org** | Org rules, stack skills, hooks, templates, automations | Org harness repo (Arffornia: `agent-kit` plugin + marketplace) |
| **Repo** | Repo map, path rules, risk map, local skills | `AGENTS.md`, `.claude/`, `.agents/skills/` in the repo |

Rules for overlays (the mechanism itself lives in `../overlay/`):
- A lower layer never copies a skill; it **references** the base and adds a short patch
  (extra steps, different commands, stricter rules). The base stays upgradable.
- A patch states which base version it targets. When the base changes, the overlay is re-checked.
- Agents other than Claude Code read the same content through the open standards
  (`AGENTS.md`, `SKILL.md` in `.agents/skills/`); provider-specific variants are a patch, not a fork.
- If a repo needs to break an org rule, it records why in an ADR, not just in its AGENTS.md.

## Start questionnaire (ask in one message, defaults pre-filled)

The agent sends this once, in the owner's language, with its guesses filled in from the repos.
Unanswered items keep the default and are listed as such in `STANDARDS.md`.

1. **Scope.** Which orgs and repos are in? Any repo off-limits? Is this a project or a company
   with teams (who decides for each team)?
2. **Decision owner(s).** Who validates chantiers? Who may merge? (Default: you validate, an
   orchestrator merges validated chantiers.)
3. **Never-do list.** Anything beyond: merge, tag, release, delete branches, change settings,
   touch secrets, push to default? Libraries or tools that must never be replaced?
4. **Languages.** Language for code and docs (default English)? For chat with you? For users
   (which locales are mandatory)?
5. **Credentials.** May CI hold a model API key? (Arffornia: no; review runs in-session.) Which
   tracker and docs tools are connected?
6. **Tracker.** Keep the current tracker or move to GitHub issues + Project? Existing labels?
7. **Machines.** Your OS and CPU (macOS arm64?), contributors' platforms, CI runners, build sizes.
8. **Live systems.** What is in production, how it deploys, what agents may touch, what is often
   offline.
9. **Brand.** Logo, colours, fonts, tone, a page style you like (Arffornia: the "Agent Kit v2" page).
10. **Attention budget.** How many minutes a day for reviews? Phone or desktop? Voice input?
11. **Learning.** Which topics do you want learning cards on?
12. **Constraints.** Budget or rate limits, deadlines, licences, compliance.

## What to change first on a new project

- Copy `phases/` checklists into the work area and tick them per repo.
- Replace the Arffornia defaults in each "Decisions" table with the questionnaire answers; keep
  the "Why" column so the next agent knows what was traded off.
- Start a new [DECISIONS.md](DECISIONS.md)-style log for the new project; keep this one as reference.
