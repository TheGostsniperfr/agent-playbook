# Deploy it on a new org or repo

## On an existing repo or org (Chantier 0)

1. Open Claude Code (or Codex, or a claude.ai chat with GitHub access) on the repo or org.
2. Say:
   > Read https://github.com/TheGostsniperfr/agent-playbook/blob/main/runbook/START.md and set
   > up the method here.
3. The agent runs the [`bootstrap`](skills/bootstrap/SKILL.md) skill:
    - checks what it can and cannot do (push, PRs, labels, GraphQL, pages);
    - inventories the repos;
    - publishes **one review page** with every setup item, each with a default and a plain
      "why";
    - after you tick it, builds: private ops repo with `STATE.md`, audit, foundation per repo
      (`make check`, CI, templates), docs as code with Noodle diagrams, `.github` org profile,
      agent-ready issues and board, review stack, harness (org layer, overlays, deterministic
      guards), automations;
    - groups everything into chantiers on your review stack.
4. You approve chantiers; agents merge and deploy them.

What you do yourself: create the private ops repo, grant tokens the agent cannot create, rotate
secrets, approve chantiers. Everything else is the agents' job.

## From an idea

Say "I want to start a new project: <idea>". The [`new-project`](skills/new-project/SKILL.md)
skill sends one interview with defaults filled in, writes a one-page vision, architecture ADRs
with options, the first milestone's spec and issues, then hands over to `bootstrap` so the
method is in place before the first feature.

## Coming back later (a fresh chat)

Say "resume <org>" or paste the ops repo URL. The [`resume`](skills/resume/SKILL.md) skill
reads `STATE.md`, checks it against GitHub and the review stack, and briefs you in ten lines.
Before stopping, say "wrap up": [`handoff`](skills/handoff/SKILL.md) writes the state.

## Install the skills on your machines

- **NixOS / nix-darwin**: add the flake input `github:TheGostsniperfr/agent-playbook?dir=overlay/nix`
  and `programs.agent-playbook.enable = true;` in home-manager.
- **Anything else**: `sh overlay/install.sh` from a clone.
- Skills appear as `/playbook:<name>` in Claude Code and `playbook-<name>` in Codex and OpenCode.

## Add the org layer

The org's harness repo (for Arffornia: `Arffornia/agent-kit`) holds `overlay/<org>.yaml` with
the org's patches and org-only skills. Each repo's `.agents/overlay.yaml` extends it; run
`agentskills render`, commit, and add `overlay/ci/skills-preview.yml` to CI.
Details: [the three layers](overlay/README.md).
