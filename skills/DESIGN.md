# Skills base and overlays: design

Goal: generic skills live once, in this repository. Brian's machines get them through Nix
(home-manager) or `overlay/install.sh`. Any project adds a thin overlay that references the base,
pins versions and patches only what differs. The same files work in Claude Code, Codex and
OpenCode, with a per-provider (or per-model) variant when one works better.
Background and sources: [RESEARCH.md](RESEARCH.md).

## 1. Principles
- **The open standard is the format.** Every base skill is a valid Agent Skill on its own: a
  project can use a raw base folder without any tooling, and Claude Code can load the repo as a
  plugin. Variants and overlays are deltas on top.
- **Render real files.** Tools differ on symlinks and Nix store links are read-only, so the
  resolver writes plain files (with exec bits) and records their hashes. Commit them in projects so
  cloud sessions and Codex cloud tasks need no install step.
- **Deterministic and checkable.** Same inputs, same bytes: sorted traversal, no timestamps,
  normalised front matter. A lockfile pins sources and output hashes; `check` fails CI on drift.
- **Fail loudly.** A patch whose target section disappeared, a version pin that no longer
  matches, or an unmanaged folder in the way stops the render with a message saying what to do.
- **One name, one level.** A skill name is visible at one level per tool (section 7).
- **Portable tooling.** One Python 3.8+ file, standard library only (macOS ships 3.9 with the
  Command Line Tools); the installer is POSIX `sh` (shellcheck `-s sh` clean, run under dash).

## 2. Base layout
```
skills/
  RESEARCH.md  DESIGN.md
  <name>/
    SKILL.md            spec front matter; metadata.version = "MAJOR.MINOR.PATCH"
    references/ scripts/ assets/
    variants/<provider>[.<model>].md   optional, never rendered as files
    tests/              optional, never rendered
    CHANGELOG.md        one entry per version, never rendered
```
- Front matter uses the six spec keys only (`name`, `description`, `license`, `compatibility`,
  `metadata`, `allowed-tools`) unless a Claude-only key is the point; such keys are dropped from
  the Codex and OpenCode renders.
- Paths in a body are relative to the skill folder (spec), never `${CLAUDE_SKILL_DIR}` in the
  base: put that in a `claude` variant when needed.
- Shared files between skills are copied, and a test asserts the copies are identical
  (`review-stack/assets/style.css` = `artifact-style/assets/style.css`;
  `overlay-apply/scripts/agentskills` = `overlay/agentskills`).

## 3. Versioning
- Each skill carries its own semver in `metadata.version`:
  patch = wording; minor = new optional section, file or variant; major = a section renamed or
  removed, inputs or outputs changed (anything that can break an overlay patch).
- Overlays pin with `version: ^1.0` (same major) or `~1.2` (same minor). A failing pin is the
  signal to read `CHANGELOG.md` and update the patches.
- The base is pinned per project by the lockfile (git commit). Repository tags are optional;
  `ref: main` + lock is enough, `update` moves it.
- The overlay file has `apiVersion: agentskills/v1`; the resolver refuses other versions, so a
  future format change is explicit.

## 4. Variants (provider and model)
`variants/<provider>.md` or `variants/<provider>.<model>.md`, provider in `claude`, `codex`,
`opencode`. Front matter: `mode` (`sections` default, `append`, `replace`), optional
`description`, `set` (front-matter keys), `patches` (same operations as overlays). In `sections`
mode each `## Heading` block of the body replaces the base section with that heading, or is
appended. Selection per target: `<provider>.<model>` if the overlay sets `model: {provider: m}`,
else `<provider>`, else none; an overlay can force `variant: <key>` or `variant: none`. The
rendered skill records `metadata.variant`.

Example: `review-stack/variants/codex.md` replaces "Build the page", "The stack" and "Read the
answers back", because Codex has no Artifact tool.

## 5. Overlays
Full reference (loaded by agents on demand):
[overlay-apply/references/overlay-format.md](overlay-apply/references/overlay-format.md).

```yaml
apiVersion: agentskills/v1
base: {git: https://github.com/TheGostsniperfr/agent-playbook, ref: main}
extends:                                  # optional org layer(s)
  - {git: https://github.com/Arffornia/agent-kit, ref: main, overlay: overlay/arffornia.yaml}
targets: [claude, codex, opencode]
skills:
  - name: review-stack
    version: ^1.0
    patches:
      - append_section: {heading: Rules, text: "- Project rule."}
      - add_files: {references/project.md: .agents/overlay/review-stack/project.md}
local:
  - path: .agents/skills-src/release-train  # project-owned skill, rendered the same way
```
- Operations: `append`, `prepend`, `append_section`, `prepend_section`, `replace_section`,
  `remove_section`, `replace_text` (exact, optional `count`), `description`, `set`, `unset`,
  `add_files`, `remove_files`; skill-level `description`, `targets`, `variant`, `rename`.
- Order per skill and target: base, then provider variant, then each layer's patches from the
  outermost `extends` to the project.
- Layers: `extends` entries are overlays inside another source (git or path). Paths inside a layer
  are relative to that source's root; inside the project overlay, to the repo root.
- `exclude` removes a skill an upper layer or `skills: "*"` selected.

## 6. The resolver: `overlay/agentskills`
```
agentskills init [--skills a,b]        write .agents/overlay.yaml
agentskills render                     render all targets, write .agents/agentskills.lock
agentskills update                     same, moving git sources to the newest commit of their ref
agentskills check [--offline]          exit 1 on hand edits (vs lock) or drift (vs sources)
agentskills list [--json]              effective skills: target, version, variant, patches
agentskills validate <dirs>            spec rules + per-tool limits, variants included
agentskills clean                      remove what it manages
agentskills export --out DIR           full build of every target into DIR, plus BUILD.json
agentskills preview --against REF      full build at REF vs the working tree, unified diff
agentskills diff OLD NEW               diff two export folders (--markdown, --exit-code)
--user  --dest DIR --target t  --base PATH  --overlay FILE|none  --force  --plugin  --prefix
```
- Base resolution: `--base` > `$AGENTSKILLS_BASE` > the overlay's `base`. Git sources are
  fetched shallow into `~/.cache/agentskills/<hash>` at the locked commit (or the ref on `update`).
- Each target folder holds `.agentskills-managed`, the list of folders the resolver owns. Other
  folders are never touched; a same-name unmanaged folder stops the render (`--force` takes over).
- Writes are atomic per skill folder (render to a temp dir, then rename).
- Every rendered `SKILL.md` gets a one-line HTML comment after the front matter naming the base
  skill, version, variant and layers, and saying where to edit. Codex and OpenCode renders keep
  spec front-matter keys only.
- Lockfile (`.agents/agentskills.lock`, JSON, sorted): `sources` (git url, ref, commit; path
  sources unpinned) and, per target, each skill's version, variant, origin and a tree hash
  (`sha256` over sorted path, exec bit and content hash).
- `check`: (1) offline, rendered folders vs lock hashes (catches hand edits); (2) re-render from
  the locked sources and compare (catches overlay edits not rendered, or a moved base);
  (3) stale managed folders; (4) the Claude settings guard (section 7).
- YAML: a small built-in subset parser (block maps and lists, flow `[]`/`{}`, quoted and plain
  scalars, `|`/`>` blocks, comments), checked against PyYAML on 38 real `SKILL.md` files.
  Overlays may also be JSON.

## 7. One name, one level
Measured in this session (RESEARCH.md section 2): Claude Code lets a personal skill hide a project
skill of the same name; Codex lists both; OpenCode 1.19 picks one at random. So:

| Level | Claude Code | Codex | OpenCode |
|---|---|---|---|
| User (Nix, install.sh) | personal plugin `~/.claude/skills/playbook/` = `/playbook:<name>` | `~/.agents/skills/playbook-<name>` | `~/.config/opencode/skills/playbook-<name>` + `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` |
| Project (overlay) | `.claude/skills/<name>` and `.claude/settings.json` `enabledPlugins["playbook@skills-dir"] = false` | `.agents/skills/<name>` | `.opencode/skills/<name>` |

A project with an overlay therefore sees exactly its own rendered set in Claude Code; in Codex and
OpenCode it sees its own set plus the `playbook-` copies, with distinct names. `userSkills: keep`
in an overlay leaves the plugin on. `--plugin ''` / `--prefix ''` restore flat user names for
people who do not use project overlays.

## 8. Installing on Brian's machines
**Nix (NixOS and macOS with nix-darwin + home-manager)**: the flake lives in `overlay/nix/`.
```nix
# flake.nix of the dotfiles
inputs.agent-playbook.url = "github:TheGostsniperfr/agent-playbook?dir=overlay/nix";
inputs.agent-playbook.inputs.nixpkgs.follows = "nixpkgs";

# NixOS:      home-manager.users.brian.imports = [ inputs.agent-playbook.homeManagerModules.default ];
# nix-darwin: home-manager.users.brian.imports = [ inputs.agent-playbook.homeManagerModules.default ];
# then, in that home-manager configuration:
programs.agent-playbook = {
  enable = true;
  # targets = [ "claude" "codex" "opencode" ];   # default
  # exclude = [ "github-profile-page" ];
  # overlay = ./agent-overlay.yaml;              # a personal layer on top of the base
  # method = "copy";                             # default; "symlink" = read-only store links
};
```
- `copy` (default): an activation step runs `agentskills render --user` from the store base; it
  writes real files and only touches folders it manages. `symlink`: `home.file` links into a
  build-time render (per-file links; Claude Code, Codex and OpenCode follow them).
- Installs the `agentskills` command and sets `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` when OpenCode
  is a target (`opencodeIgnoreExternal = false` to opt out).
- Outputs: `packages.<system>.{agentskills,skills}`, `apps.<system>.default`,
  `checks.<system>.{tests,skills}`, `homeManagerModules.default`, for x86_64/aarch64 Linux and
  Darwin. Updating = `nix flake update agent-playbook`.

**Without Nix**: `sh overlay/install.sh` (or curl it) clones into
`~/.local/share/agent-playbook`, links `~/.local/bin/agentskills`, renders the user level;
re-run to update, `--uninstall` to remove.

## 9. Full build and preview (the Kubernetes-manifest rule)
The rendered `SKILL.md` and its files are the agent's real input, so every change is reviewed as
a rendered diff. `export` writes the full build (all targets, all layers) with `BUILD.json`
(sources, commits, tree hashes); `preview --against <ref>` extracts the ref with `git archive`,
renders both sides with the same resolver and prints a per-skill summary plus a unified diff
(`--markdown` for a PR body or `$GITHUB_STEP_SUMMARY`, `--keep DIR` to keep the new build).
A ref that cannot be rendered (no overlay yet) shows everything as added. The base runs this in
`.github/workflows/ci.yml`; projects copy `overlay/ci/skills-preview.yml`.

## 10. CI in a project
```yaml
- uses: actions/checkout@v5
- run: python3 .claude/skills/overlay-apply/scripts/agentskills check
```
The path exists when the overlay selects `overlay-apply`; otherwise vendor the resolver.
No secrets, no model. Use `--offline` when the runner cannot fetch the base. Offline discovery
tests when the CLIs are installed: `codex debug prompt-input hi`, `opencode debug skill`,
`claude plugin validate .claude/skills`.

## 11. Arffornia's agent-kit
agent-kit stays the Arffornia plugin and becomes the **org layer**:
1. Generic skills move to (or stay in) this base; Arffornia-specific wording moves into
   `agent-kit/overlay/arffornia.yaml` as patches (see `overlay/examples/org-layer/`).
2. agent-kit renders its plugin skills folder from base + its own layer:
   `agentskills render --target claude --dest plugins/arffornia/skills` with its Arffornia-only
   skills listed under `local:`. The marker keeps its hand-written skills safe during the move.
   Its `codex/sync-skills.sh` is replaced by the `codex` target.
3. Each Arffornia repo has `.agents/overlay.yaml` with `extends: [{git: Arffornia/agent-kit,
   overlay: overlay/arffornia.yaml}]` and only its own patches, rendered for all three tools, and
   `agentskills check` in `make check`/CI.
4. The plugin's `_shared/reporting.md` copy-sync becomes an `add_files` or `append_section` in
   the org layer.

## 12. Limits
- Codex and OpenCode still show the user-level `playbook-` copies next to a project's own copies
  (different names, so no ambiguity, but more entries in the listing).
- `replace_section` matches heading text; renaming a heading in the base is a breaking change
  (major version), which the loud failure makes visible.
- No three-way merge: a project that needs to diverge a lot should fork the skill as a `local:`
  skill instead of stacking patches.
