# Decision log: the Arffornia takeover (Oct 2026)

Each line: context → decision → alternatives considered → status. ADRs live in
https://github.com/Arffornia/docs/tree/main/docs/decisions. Status: **accepted** (owner said so),
**applied** (done, owner can still veto), **proposed** (waiting for the owner), **superseded**.

## Working model

| # | Context | Decision | Alternatives | Status |
|---|---|---|---|---|
| D01 | Solo owner, little time, 12 repos | Agents do the work; owner decides and validates | Owner codes with AI assist | accepted |
| D02 | Irreversible actions, public repos | Agents never merge, tag, release, delete branches, change settings, touch secrets | Trusted agent with admin token | accepted |
| D03 | Owner did not want to merge PRs one by one | Owner validates **chantiers** (PRs + decisions on one page); an orchestrator merges them | Owner merges each PR; auto-merge on green | accepted (wave 3) |
| D04 | Owner refused API keys in GitHub | No AI job in CI; AI review runs in the agent's session at task end | Claude GitHub App + secret; managed Code Review | accepted (wave 3) |
| D05 | Mixed French/English history, FR/EN players | English for code, docs, issues, PRs; i18n `en`+`fr` for every user-visible string ([ADR-0002](https://github.com/Arffornia/docs/blob/main/docs/decisions/0002-english-codebase-bilingual-players.md)) | French codebase; English-only players | accepted |
| D06 | Owner's own libraries look replaceable | Keep and improve them; replacing needs a new ADR ([ADR-0003](https://github.com/Arffornia/docs/blob/main/docs/decisions/0003-keep-owner-libraries.md)) | Swap for popular packages | accepted |
| D07 | Owner lost links in long reports | Every mention = full URL + one-line summary, grouped by action | Short prose reports | accepted |
| D08 | Parallel agents broke shared clones | Worktrees under `wt/<name>`, never switch branches in shared clones; ≥8 GB free | One clone per agent; containers | accepted |
| D09 | Owner moving to Apple Silicon | Everything runs on macOS arm64 and Linux x86_64/arm64 | Linux-only dev | accepted (wave 3) |
| D10 | Generic material is not Arffornia's | Generic runbook, base skills, learning cards in personal `agent-playbook` repo; org specifics in `agent-kit` | Everything in agent-kit | accepted (wave 3) |

## Structure and process

| # | Context | Decision | Alternatives | Status |
|---|---|---|---|---|
| D11 | Decisions lived in one head | ADRs in the docs site ([ADR-0001](https://github.com/Arffornia/docs/blob/main/docs/decisions/0001-record-decisions.md)) | Wiki; none | accepted |
| D12 | Notion board with 8 real tasks | GitHub issues + org Project "Arffornia Roadmap"; Notion for ideation ([ADR-0004](https://github.com/Arffornia/docs/blob/main/docs/decisions/0004-github-issues-as-tracker.md)) | Keep Notion; Linear | proposed (in use) |
| D13 | Agents need routing without asking | Labels `agent-ready` / `needs-decision` / `proposal` + type/area/priority/effort; milestones M1-M3 | Status columns only | applied |
| D14 | GraphQL blocked in the session | Board synced hourly by a GitHub Action with a scoped PAT org secret | Manual "add items"; add-to-project action | applied |
| D15 | No overview of the ecosystem | Central MkDocs docs repo + Noodle diagrams from one model ([ADR-0005](https://github.com/Arffornia/docs/blob/main/docs/decisions/0005-docs-as-code.md)) | Per-repo docs only; hand-drawn diagrams | proposed (in use) |
| D16 | Six stacks, different commands | Makefile verbs `check/test/build/lint/fmt` in every repo | Per-stack scripts; Taskfile; just | applied |
| D17 | Overlapping fixes in same files | Stacked PRs, merged with merge commits in a given order | Squash; one big PR per repo | applied |
| D18 | Foundation must be safe to merge | Foundation PR changes no behaviour; behaviour changes need a ticket | Fix while tidying | applied |
| D19 | Kanban columns overflowed | Two lanes: agents pull ready issues; owner pops a chantier queue (WIP 3) with page links | Classic kanban | proposed |
| D20 | Owner answers from phone | Decision pages: Agree / Other / Later + text + voice; answers stored and read back | Answers in chat; GitHub comments | proposed |

## Harness

| # | Context | Decision | Alternatives | Status |
|---|---|---|---|---|
| D21 | v1 "too simple" | agent-kit v2: hooks (start card, guard, post-edit, stop gate, handoff), path rules, 23 skills, 6 subagents, evals | Templates only | proposed (PRs open) |
| D22 | Rules agents ignore | A rule broken twice becomes a sensor (hook, lint, test, CI) | More prose | applied |
| D23 | Self-grading agents | Independent reviewer and verifier subagents; test-writer cannot see the implementation | Same agent reviews | applied |
| D24 | Review cost: 5 Opus runs per PR, 8 when sensitive | Opus for main work and verification; Haiku for mechanical subagents; raise effort before model; review once at task end | Opus everywhere; Sonnet everywhere | proposed |
| D25 | Codex/OpenCode use too | Open SKILL.md standard, synced to `.agents/skills` | Claude-only plugin | applied |
| D26 | Sandbox in template | On by default with a registry allow-list | Opt-in | proposed |
| D27 | Force-push needs | `--force-with-lease` allowed on feature branches only | Block all force | proposed |
| D28 | Website layering guard | deptrac forbids controllers → Eloquent; route-model binding question open | Allow `Model` in controllers | proposed |
| D29 | Unfixed security findings as eval cases | Held out of the public repo until fixed | Commit with neutral wording | proposed |
| D30 | Work-ticket skill and pushing | Skill stops before push; `/publish` is manual | Agent opens draft PRs itself | proposed |

## Product and platform

| # | Context | Decision | Alternatives | Status |
|---|---|---|---|---|
| D31 | Website lock needed PHP 8.4, image ran 8.3 | Pin lock to 8.3 now; owner wants Laravel + PHP upgrade next | Move to 8.4 immediately | superseded by owner (upgrade) |
| D32 | Website language selection | Cookie switcher → Accept-Language → default `fr`; no URL prefix | `/en` `/fr` prefixes | applied (vetoable) |
| D33 | Recipes over HTTP, fail-open | Generated datapack with a real recipe type ([ADR-0006](https://github.com/Arffornia/docs/blob/main/docs/decisions/0006-recipes-as-datapack.md)) | Keep HTTP; harden it | proposed |
| D34 | Parallel features need servers | Per-PR preview environments after secret isolation ([ADR-0007](https://github.com/Arffornia/docs/blob/main/docs/decisions/0007-preview-environments.md)) | One staging server first | proposed |
| D35 | Hardening could break prod | CSP report-only first; NetworkPolicies as a draft with staged apply | Enforce immediately | applied |

Full list of 34 product decisions with defaults: the Chantier 0 handover page
https://claude.ai/artifact/D35xReunfKfovJYNyL4wzi (private to the owner).
