# Phase 2 · Foundation per repo

**Goal:** every repo gets the same entry points for humans, agents and CI, in one PR per repo
that changes **no runtime behaviour**. After this phase, `make check` means the same thing
everywhere and an agent never searches for commands.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Universal verbs | `Makefile` with `check` (lint + typecheck + tests + build), `test`, `build`, `lint`, `fmt` as thin wrappers | Six stacks (PHP, Electron, Gradle x2, TypeScript libs, Kubernetes): one vocabulary for humans, hooks, CI and agents |
| Agent entry point | `AGENTS.md` (open standard, read by Codex, Copilot, Cursor...) as a map under ~100 lines; `CLAUDE.md` = one line `@AGENTS.md` | One file for every agent; details live deeper ([phase 5](05-harness-skills.md)) |
| CI | `ci.yml` on PR and push to default = `make check`; `permissions: contents: read`; current major action versions | CI and the local gate run the same thing |
| Bots | Dependabot weekly, grouped, plus `github-actions` | Fewer, larger dependency PRs |
| LICENSE | Never added by an agent; a `needs-decision` issue instead | Legal choice belongs to the owner |
| Stacking | One PR per concern; stacked when files overlap; merged with **merge commits** | Squash breaks every PR stacked on top |
| Portability | Scripts run on macOS arm64 and Linux x86_64/arm64: POSIX sh or bash 3.2, no GNU-only flags, or check for gnu tools and say how to get them | The owner moves to a Mac; contributors on both |

## Foundation PR contents (branch `chore/foundation`)

- `README.md` rewritten (≤150 lines): what it is and where it sits, requirements, quickstart,
  commands, configuration (env vars without values), release process, license. Keep useful
  existing content.
- `AGENTS.md` + `CLAUDE.md`; `Makefile`; `.editorconfig`; `.github/workflows/ci.yml`;
  `.github/dependabot.yml`; PR template (What / Why / How tested / Risk & revert / Checklist);
  issue forms (bug, feature, config); `CONTRIBUTING.md`; `SECURITY.md` (private reporting).
- Leftover non-English comments and docs translated (not player-facing locale files).
- Lint config fixed only as far as `make check` needs (big lint migrations get their own PR).

## Steps (agent)

1. `git fetch origin`, `git worktree add <root>/wt/<repo>-foundation origin/<default>`.
2. Write the files from the audit facts (commands that actually work, real gotchas).
3. Run `make check` from a clean clone state; fix only what blocks it.
4. Open the PR with the commands and results pasted. Label it, link the hygiene issue.
5. Later PRs in the repo are stacked on the foundation when they need `make check`.

## Human touchpoints

- None per PR. The foundation PRs of all repos form one chantier the owner validates once.

## Anti-patterns we hit

- **Squash merges break stacks.** Tested: the PRs behind a squashed base conflict. Use merge
  commits and say so in the chantier page.
- **"Delete branch on merge" off** in three repos: after merging a base, the next PR still
  targets the old branch. Turn it on, or retarget by hand.
- **CI appears only after the foundation merges.** Stacked PRs show no `check` job until then;
  "Update branch" afterwards. Expected red PRs must be labelled as such in the chantier page.
- **`make check` ordered wrong.** Website tests needed the Vite manifest, so `build` must run
  before `test`. Run the full target, not just the parts.
- **Lockfile vs runtime mismatch.** `composer.lock` required PHP 8.4.1, the image and cloud VMs
  ran 8.3. Pin `config.platform.php` to the runtime, and plan the runtime upgrade as its own
  decision (owner later asked for the Laravel and PHP upgrade).
- **Agents switching branches in a shared clone** while others read it. Worktrees only.
- **A `printf` through a symlink** overwrote the docs repo's AGENTS.md. Never write through
  symlinks; make CLAUDE.md a real file.
- **macOS:** bash 3.2, BSD `sed -i ''`, `stat -f`, no `timeout`, no `sha256sum` (`shasum -a 256`).
  Test hooks and scripts against both or use a portable helper.

## Checklist

- [ ] One foundation PR per repo, no behaviour change, `make check` green locally and in CI
- [ ] AGENTS.md under ~100 lines, commands verified, gotchas from the audit
- [ ] No LICENSE added; a `needs-decision` issue exists if missing
- [ ] Merge order and stacking documented for the chantier page
- [ ] Scripts checked for macOS arm64 (bash 3.2, BSD tools) and Linux
- [ ] Worktree removed after the PR is open
