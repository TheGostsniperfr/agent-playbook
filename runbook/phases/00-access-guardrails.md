# Phase 0 · Access and guardrails

**Goal:** before any real work, know exactly what agents can and cannot reach, write the shared
rules every agent follows, and set up a workspace where parallel agents cannot collide.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Where agents run | Cloud Claude Code sessions with repos attached; the owner's machine (Mac, Apple Silicon) only for GUI and game checks | No laptop dependency, parallel sessions; GUI checks need a real display |
| Network | Owner allowed all domains | Registries, Maven, Packagist, Mojang all needed. Still record what the proxy blocks (below) |
| Merge rights | Agents open PRs only. Never merge, tag, release, delete branches, change settings, touch secrets | One owner, public repos, irreversible actions. Later relaxed: an orchestrator merges validated chantiers ([phase 4](04-tracker-review.md)) |
| Credentials in CI | **No API key or OAuth token in GitHub.** AI work (including review) runs inside agent sessions | Owner decision: no model spend outside his subscription, no secret to leak |
| Language | Artifacts in English; chat in the owner's language | Contributors and agents read English; the owner dictates in French |
| Reporting | Full clickable URL + one-line summary for every PR, issue, commit, page | The owner acts from the report; a missing link is a search |
| Who creates what | Agents ask the owner to create repos, org Projects, org secrets | The session could not create repos or call org-level APIs |

## Steps (agent)

1. **Inventory.** List orgs, repos (`gh api user/repos`, org repos), trackers (Notion, Jira,
   boards), docs, infra repos, running services. Note which ones are live (the homelab was off:
   nothing could be tested against production).
2. **Probe every capability with a no-op** and write a capability matrix in `STANDARDS.md`:
   REST read/write per repo, GraphQL, org-level REST, repo creation, Actions secrets, package
   registries, GitHub release downloads, tracker API. Do not trust docs: try it.
3. **Write `STANDARDS.md`** (shared rules for all agents; template: [ADAPT.md](../ADAPT.md)):
   language, never-do list, branch and commit conventions with exact trailers, PR body sections,
   issue format and labels, security disclosure rule, machine limits, report format.
4. **Workspace layout.** Shared clones read-only for agents at `<root>/<Repo>`; each agent works in
   its own worktree at `<root>/wt/<name>` (`git worktree add`). Reports go to `_audit/` and
   `_work/`. Keep at least 8 GB free (`df -h /`); every agent deletes its caches and worktrees.
5. **Machine limits** in the rules: one heavy build at a time, Gradle `-Xmx2g --no-daemon`.
6. **Record the owner's hard constraints verbatim** (Arffornia: never replace the owner's own
   libraries; all player text bilingual).
7. **Ask once** for what agents cannot do, as one list with the exact clicks (create repo X,
   create Project Y, add secret Z with scope S).

## Human touchpoints

- Grant access (GitHub app, tracker connector, network) in one sitting.
- Create the resources agents cannot create. Approve installs the safety classifier blocks.
- Nothing else in this phase.

## Anti-patterns we hit

- **Wrong paths in agent prompts.** Auditors were told `/home/claude/arffornia` while clones lived
  in `/root/arffornia`; fixed with symlinks and messages. Give absolute paths and verify them.
- **GraphQL blocked in the session.** The org board could not be created or filled from the agent.
  Fix: the owner created the Project and a fine-grained token as an org secret; a scheduled
  GitHub Action (`scripts/sync_board.py`, GraphQL inside Actions) syncs every issue and PR hourly.
  Lesson: when the session cannot call an API, move the call into CI with a scoped token.
- **Repos starting with `.` could not be attached** (`.github`). Content was zipped for the owner.
- **Release downloads from github.com refused by the proxy** (composer dist zipballs, draw.io,
  some `go install`). Fallbacks: nixpkgs, git clone, or say "not verified" in the PR.
- **Go toolchain DNS failure** behind the proxy until `NO_PROXY=localhost,127.0.0.1`.
- **Classifier blocked a desktop app install** (draw.io) until the owner approved it explicitly.
  Ask early for the tools you will need.
- **Fetch of a key source blocked by a permission prompt** in a sub-agent. Note it in the report
  and cite the secondary source you used instead.

## Checklist

- [ ] Capability matrix written, each line tested, blocked items have a workaround or an owner ask
- [ ] `STANDARDS.md` exists and every sub-agent prompt starts with "read STANDARDS.md"
- [ ] Commit trailers and PR footer copied exactly from the session's attribution rule
- [ ] Worktree root and report folders created; disk headroom checked
- [ ] Owner's hard constraints recorded verbatim
- [ ] One message to the owner with every manual step, numbered, with exact clicks
