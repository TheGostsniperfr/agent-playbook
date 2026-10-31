---
name: overlay-apply
description: "Set up or update a project's skills overlay: pick generic skills from Brian's agent-playbook base, pin their versions, patch only what differs for this project, and render them for Claude Code (.claude/skills), Codex (.agents/skills) and OpenCode (.opencode/skills) with the agentskills resolver, lockfile and CI drift check. Use when asked to add, update, patch or sync shared skills in a repo, to fix an 'agentskills check' failure, or to change a generic skill for one project."
compatibility: "Needs python3 (3.8+) and git."
metadata:
  version: "1.1.0"
  author: "Brian Perret"
---

# Overlay apply

Generic skills live once in the base (`TheGostsniperfr/agent-playbook`, folder `skills/`). A
project keeps a thin overlay, `.agents/overlay.yaml`, that lists the base skills it uses, pins
their versions and patches only what differs. The resolver renders real files into each tool's
folder and writes `.agents/agentskills.lock`. Full format:
[references/overlay-format.md](references/overlay-format.md).

## Find the resolver
`agentskills` on PATH (installed by the Nix module or `overlay/install.sh`). Otherwise use the copy
in this skill: `python3 <this skill's folder>/scripts/agentskills`. Below, `agentskills` means
either.

## Set up a project
1. `agentskills init --skills review-stack,artifact-style` at the repo root. It writes
   `.agents/overlay.yaml` pointing at the base on GitHub (`--git`, `--ref` to change).
2. Write the patches the project needs. Prefer, in order: nothing; `append_section` to an
   existing section; a new file through `add_files` plus one line pointing at it;
   `replace_section` only when the base text is wrong for this project. Keep long project text in
   `.agents/overlay/<skill>/*.md` and reference it with `file:`.
3. `agentskills render`, then `agentskills list` to see versions, variants and patches per tool.
4. `agentskills validate .claude/skills .agents/skills .opencode/skills` must report no errors.
5. Add the drift check to CI (one step, no secrets, needs network to fetch the base):
   `python3 <path>/agentskills check` (or `--offline` to only detect hand edits).
6. Commit `.agents/overlay.yaml`, `.agents/agentskills.lock`, any `.agents/overlay/` files,
   `.claude/settings.json` (the render switches the user-level `playbook` plugin off there, so the
   project's own copies win) and the rendered folders. Rendered files are committed so cloud sessions and Codex cloud tasks get
   them without running anything.

## Update
- New base version: `agentskills update` (moves the lock to the newest commit of `ref`), read the
  diff of the rendered folders, run the project's checks, commit. A failing `replace_section` or
  `replace_text` means the base changed that text: rewrite the patch, do not force it.
- A version pin fails (`overlay pins ^1.0`): the base made a breaking change. Read the skill's
  `CHANGELOG.md` in the base, adapt the patches, then raise the pin.
- `agentskills check` fails in CI: someone edited rendered files or the overlay without
  rendering. Move the edit into the overlay (or the base), run `agentskills render`, commit.

## Full build and change preview
The rendered skills are exactly what the agent reads, like rendered Kubernetes manifests are
exactly what the API server gets. So review the render, not only the patch:
- `agentskills export --out build/skills`: the full build (every target, every layer applied)
  plus `BUILD.json` (sources and hashes). Use it to share or archive a snapshot.
- `agentskills preview --against origin/main [--markdown]`: renders the working tree and the
  ref, prints the per-skill summary and the unified diff of the rendered files. Paste the
  `--markdown` output in the PR body when a change touches skills or an overlay layer.
- `agentskills diff OLD NEW`: the same diff between two export folders (for example the build
  before and after `agentskills update`).
- CI: copy `overlay/ci/skills-preview.yml` from the base; it writes the preview to the job
  summary and attaches the full build. In the base itself, `ci.yml` does the same.
- A change in an upper layer (base or org layer) changes every project that extends it: run
  `preview` in one or two consumer repos before merging it, and paste their summaries too.

## Where a change belongs
- Useful to any project: change the base skill in agent-playbook, bump `metadata.version`
  (patch: wording; minor: new optional section or file; major: renamed or removed section, changed
  inputs), add a line to its `CHANGELOG.md`, open a PR there.
- Better for one provider or model only: a `variants/<provider>[.<model>].md` file in the base.
- Specific to this project or org: the overlay. Org-wide patches go in an upper layer that projects
  `extends` (for Arffornia: `Arffornia/agent-kit` `overlay/arffornia.yaml`).
- Never edit the rendered folders: the next render overwrites them and `check` flags them.
- When a project patch turns out to be generic, propose it upstream and drop it from the overlay.

## Rules
- Do not commit tokens or local paths in the overlay; `path:` bases are for local trials only.
- Keep the generated header line in each rendered `SKILL.md`: it tells agents where to edit.
- User-level copies (Nix or `install.sh`) are `/playbook:<name>` in Claude Code and
  `playbook-<name>` in Codex and OpenCode, so they never collide with a project's own copies
  (see "One name, one level" in the reference).
- Codex and OpenCode get spec front matter only; Claude-only fields (`context`, `model`,
  `disable-model-invocation`, ...) stay in the Claude render.
