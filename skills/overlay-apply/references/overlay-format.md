# Overlay format (agentskills/v1)

File: `.agents/overlay.yaml` (or `.agents/overlay.json`). Paths inside it are relative to the
repository root (the parent of `.agents/`). Lockfile: `.agents/agentskills.lock` (JSON, commit it).

```yaml
apiVersion: agentskills/v1
base:                                  # where the generic skills come from (first match wins:
  git: https://github.com/TheGostsniperfr/agent-playbook   # --base, $AGENTSKILLS_BASE, this)
  ref: main                            # branch, tag or commit; the lockfile pins the commit
  # path: ../agent-playbook            # a local checkout instead of git
  # subdir: skills                     # default: skills/ if present, else the root
extends:                               # optional upper layers, applied before this file
  - git: https://github.com/Arffornia/agent-kit
    ref: main
    overlay: overlay/arffornia.yaml    # an overlay file inside that source
targets: [claude, codex, opencode]     # default: all three
paths:                                 # optional per-target folders (defaults below)
  opencode: .opencode/skills
model:                                 # optional: picks variants/<provider>.<model>.md
  claude: opus
skills:                                # or skills: "*" for every base skill
  - name: review-stack
    version: ^1.0                      # must match the base skill's metadata.version
    description: "..."                 # replace the description
    targets: [claude]                  # render this skill for these tools only
    variant: none                      # force a variant key, or none
    rename: arffornia-review           # publish under another name
    patches:                           # applied in order, after the provider variant
      - append_section: {heading: Rules, text: "- Project rule."}
      - replace_section: {heading: "## The stack", file: .agents/overlay/review-stack/stack.md}
      - prepend_section: {heading: Steps, text: "0. Read AGENTS.md first."}
      - remove_section: Voice input
      - append: "## Project notes\n\nText added at the end."
      - prepend: "Read this first."     # after the first H1
      - replace_text: {old: "the owner", new: "Brian", count: 3}
      - set: {allowed-tools: "Bash(gh:*)", metadata: {team: core}}
      - unset: [compatibility]
      - add_files: {references/project.md: .agents/overlay/review-stack/project.md}
      - remove_files: [assets/example.chantier.json]
exclude: [github-profile-page]         # drop skills selected by an upper layer or "*"
userSkills: hide                       # hide (default): switch the user-level "playbook" Claude
                                       # plugin off in .claude/settings.json; keep: leave it on
local:                                 # project-owned skills rendered like base skills
  - path: .agents/skills-src/mc-machine
```

## Section matching
A heading matches by text, case-insensitive, any level, unless the level is written
(`"## Steps"`). A section runs to the next heading of the same or higher level. Headings inside
fenced code blocks are ignored. `append_section` and `prepend_section` create a missing section at
the end of the body (pass `create: false` to fail instead); `replace_section` and
`remove_section` fail when it is missing, so a base change that renames a section breaks the
render loudly instead of silently skipping the patch.

## Variants (in the base)
`variants/<provider>.md` or `variants/<provider>.<model>.md` next to `SKILL.md`. Front matter:
`mode` (`sections` default: each `## Heading` block replaces the same-named base section or is
appended; `append`; `replace`), optional `description`, `set`, `patches`. The model-specific file
wins over the provider file. `variants/`, `tests/` and `CHANGELOG.md` are never rendered.

## Default folders
| Target | Project | User (`--user`) |
|---|---|---|
| claude | `.claude/skills/<name>` | `~/.claude/skills/playbook/skills/<name>` (plugin) |
| codex | `.agents/skills/<name>` | `~/.agents/skills/playbook-<name>` |
| opencode | `.opencode/skills/<name>` | `~/.config/opencode/skills/playbook-<name>` |

Each folder gets `.agentskills-managed`, the list of folders the resolver owns. Other folders are
never touched; an unmanaged folder with the same name stops the render (`--force` takes it over).

## One name, one level
Claude Code ranks a personal skill above a project skill of the same name, Codex lists both, and
OpenCode 1.19 picks one at random. So user-level installs never use the bare names:
- Claude: a personal plugin at `~/.claude/skills/playbook/` (skills show as `/playbook:<name>`).
  Rendering a project for claude sets `"enabledPlugins": {"playbook@skills-dir": false}` in
  `.claude/settings.json`, so in that repo only its own rendered set is visible. `check` verifies it.
- Codex and OpenCode: `playbook-<name>` folders in `~/.agents/skills` and
  `~/.config/opencode/skills`. Set `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` so OpenCode skips the
  Claude and Codex folders (it scans them recursively); projects then need the opencode target.

## Version constraints
`*`, `1.2.3` (exact), `1.2` (prefix), `^1.2` (same major), `~1.2` (same minor), `>=1.2 <2`.
