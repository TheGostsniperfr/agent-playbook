# agent-playbook

Brian's generic, reusable material for running software projects and organisations with
autonomous AI agents. Project-specific material lives in each project's own harness repo, and
a project's live state lives in its private ops repo, never here.

**Docs site:** https://thegostsniperfr.github.io/agent-playbook/ (built from `docs/` and the
folders below by `.github/workflows/pages.yml`; needs the repo to be public, or a paid plan).

**Point an agent at the method:** "Read
https://github.com/TheGostsniperfr/agent-playbook/blob/main/runbook/START.md and set up the
method here." It resumes, bootstraps an existing repo or org, or starts a new project.

## Runbook

[`runbook/`](runbook/README.md) is the step-by-step map for taking over and running a project
or a whole organisation with agents: ten phases from access and guardrails to continuous
improvement, each with decisions (and the defaults chosen on Arffornia), steps, human
touchpoints, real anti-patterns and checklists.

- Start here: [runbook/README.md](runbook/README.md), then [runbook/ADAPT.md](runbook/ADAPT.md)
  (scopes, overlays, start questionnaire).
- Why things are the way they are: [runbook/DECISIONS.md](runbook/DECISIONS.md).
- What to try next: [runbook/IDEAS.md](runbook/IDEAS.md) (ranked, with sources).
- How agents keep it current: [runbook/MAINTAIN.md](runbook/MAINTAIN.md).

To use it on a new project, tell the agent: "Read `agent-playbook/runbook/README.md` and run
the takeover for <scope>."

## Skills

[`skills/`](skills/) is the base of generic agent skills (open `SKILL.md` standard, semver in
`metadata.version`, optional per-provider variants), and [`overlay/`](overlay/) is the
`agentskills` resolver that renders them, plus a project's patches, for Claude Code
(`.claude/skills`), Codex (`.agents/skills`) and OpenCode (`.opencode/skills`), with a lockfile
and a CI drift check.

| Skill | What it does |
|---|---|
| [`resume`](skills/resume/SKILL.md) | Rebuild a project's context in a fresh chat from `STATE.md` in the private ops repo |
| [`handoff`](skills/handoff/SKILL.md) | Write the project's live state before stopping, so a new chat can continue |
| [`bootstrap`](skills/bootstrap/SKILL.md) | Chantier 0 on an existing repo or org: propose and run the standard setup |
| [`new-project`](skills/new-project/SKILL.md) | From an idea to a first milestone, then bootstrap |
| [`propose-skill`](skills/propose-skill/SKILL.md) | "Done twice -> skill": detect repeated work and propose a skill in the right layer |
| [`cross-repo-issue`](skills/cross-repo-issue/SKILL.md) | File an issue on another project's repo with a `from: <project>` label |
| [`review-stack`](skills/review-stack/SKILL.md) | Chantier review page (PRs in merge order, decisions with defaults and "Other", proof), answers stored in the artifact database, and the review stack page |
| [`artifact-style`](skills/artifact-style/SKILL.md) | The Agent Kit v2 visual style for HTML pages: tokens, type pairing, components, light and dark |
| [`github-profile-page`](skills/github-profile-page/SKILL.md) | GitHub org or user profile: animated theme-aware SVG banner, live stats card, README |
| [`overlay-apply`](skills/overlay-apply/SKILL.md) | Set up or update a project's overlay and run the resolver |

- Install on a machine: Nix/home-manager module in [`overlay/nix/`](overlay/nix/flake.nix), or
  `sh overlay/install.sh`. User-level skills appear as `/playbook:<name>` (Claude Code) and
  `playbook-<name>` (Codex, OpenCode).
- Use in a project: `agentskills init --skills review-stack`, add patches, `agentskills render`,
  commit, and run `agentskills check` in CI.
- How and why: [skills/DESIGN.md](skills/DESIGN.md); what exists elsewhere and what we measured:
  [skills/RESEARCH.md](skills/RESEARCH.md).
- Full build and change preview: `agentskills export --out build/skills`,
  `agentskills preview --against origin/main` (the rendered diff agents will see); the three
  layers in plain words: [overlay/README.md](overlay/README.md).
- Tests: `python3 -m unittest discover -s overlay/tests` and
  `python3 -m unittest discover -s skills/review-stack/tests`; `nix flake check ./overlay/nix`.

## Docs site

`mkdocs.yml` + `docs/` (pages, Noodle diagrams in `docs/architecture/system/`, rendered in
`docs/diagrams/`). Local preview: `pip install -r requirements-docs.txt && mkdocs serve`.
