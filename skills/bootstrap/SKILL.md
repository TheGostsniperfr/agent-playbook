---
name: bootstrap
description: "Set up Brian's agent method on an existing repo or GitHub org (Chantier 0): check access, inventory the repos, then propose and run the standard setup (audit, docs as code with diagrams, org profile, agent-ready issues, board and review stack, harness with org layer and deterministic guards, private ops repo with STATE.md, automations) plus the project-specific items found. Use when pointed at a repo or org with the playbook URL ('set up the method here', 'apply agent-playbook', 'chantier 0', 'onboard this repo/org'), or when a project has no AGENTS.md, no review stack or no ops repo yet."
compatibility: "Claude Code or Codex with git and gh; claude.ai with a GitHub connector can run the plan but not push. The playbook is read from https://github.com/TheGostsniperfr/agent-playbook when not installed."
metadata:
  version: "1.1.0"
  author: "Brian Perret"
---

# Bootstrap (Chantier 0)

The owner opens an agent on a repo or org and says: "Read <playbook URL> and set up the method".
You propose everything in one page, the owner ticks, you build. Background for each step: the
runbook phases (`runbook/phases/` in the playbook). This is for a project that already exists;
for an idea with no code yet, use `new-project` first.

## 1. Access and inventory (no writes)
- Capability matrix: can you push branches, open PRs (REST), create labels, create repos,
  read org settings, use GraphQL (often blocked), publish pages (artifacts)? What must the owner
  do instead? (runbook phase 0)
- Inventory: repos (language, last push, CI, tests, docs, licence, open issues and PRs), org
  profile, boards, existing harness files (AGENTS.md, CLAUDE.md, `.claude/`, `.agents/`), live
  services named in the repos. Note what is clearly off (secrets in git, broken CI).
- Is there already a live state? (`resume`): an ops repo, a STATE.md, a review stack.
- Note the org's **repo naming convention** (e.g. `Arffornia_Launcher`, `Arffornia_Website`) and
  follow it for every repo you propose or name: `Arffornia_Assets`, not `assets`. Record it in
  STATE.md and in the org layer's rules. A deliberate exception (a private `ops` repo) is said
  where repos are listed.

## 2. Propose the setup (one review page)
Build a Chantier 0 page with the `review-stack` skill: one decision per item, default on,
each with a plain `why`. Standard items (details and defaults:
[references/setup-items.md](references/setup-items.md)):
1. **Continuity pack (always first, always on):** so any new chat or agent resumes in seconds.
   See [`../resume/references/continuity-pack.md`](../resume/references/continuity-pack.md).
   Private ops repo `<org>/ops` with `STATE.md` (owner creates the repo), the review stack page,
   a "Resuming" line in every AGENTS.md, a SessionStart hook that prints the STATE head, the
   `handoff` hooks (PreCompact, SessionEnd), and, when the owner uses claude.ai Projects, a
   `START-HERE.md` + a copy of `STATE.md` in the Project docs.
2. Audit per component (evidence report, proposed tickets, at most 5 questions each).
3. Foundation per repo: README, AGENTS.md map, Makefile verbs (`setup`, `check`, `test`, `fmt`,
   `lint`), CI, issue and PR templates. No behaviour change.
4. Docs as code: a docs repo or `docs/` with MkDocs Material, ADRs, Noodle diagrams generated in CI.
5. Org profile: `.github` repo with profile README, banner, issue forms (`github-profile-page`).
6. Tracker: agent-ready issues (one task, acceptance criteria, files to touch), `needs-decision`
   issues with defaults, labels, a board with lanes; chantiers as the owner's unit of review.
7. Harness: org layer on top of this playbook (rules, hooks, skills, review gate), per-repo
   overlays, deterministic guards per stack (`runbook/patterns/deterministic-guards.md`).
8. Automations: weekly brief, monthly maintenance, skipped when nothing changed.
9. Project-specific items you found (each with evidence and a default).
Add the workflow the owner works with (`runbook/WORKFLOW.md` in the playbook) to the
page so the owner validates it once.

## 3. Build
Run the approved items in runbook order (phases 1 to 4 sequential, then 5 to 9 overlapping).
Every item ends as PRs grouped in chantiers on the review stack. Open the PRs yourself; merge
only inside a chantier the owner approved, and only if you are authorised to merge
(`runbook/WORKFLOW.md`: REST API, merge commits). The owner pays for nothing except a domain
name: free tiers, open source, self-hosted. Secret-store changes go through IaC
(`runbook/patterns/secrets-through-iac.md`).

## 4. Close
Run `handoff`: STATE.md in the ops repo lists the chantiers, decisions, owner actions and links;
each repo's AGENTS.md points to it. Report to the owner at high level: done, problems, the
axes taken, what needs them.
