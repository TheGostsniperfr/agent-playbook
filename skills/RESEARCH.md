# Skills across Claude Code, Codex and OpenCode: research notes

Written 2026-10-29 for the agent-playbook skills base. Versions tested here: Claude Code 2.1.312,
Codex CLI 0.165.0, OpenCode 1.19.5, home-manager master (095fef2). Items marked **tested** were run
in this session; the rest come from the cited pages.

## 1. The open standard: Agent Skills (`SKILL.md`)

Spec: https://agentskills.io/specification

- A skill is a folder with `SKILL.md` (YAML front matter + Markdown body) and optional
  `scripts/`, `references/`, `assets/`.
- Front matter: `name` (required, 1-64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$`, must equal the folder
  name), `description` (required, 1-1024 chars, says what and when), optional `license`,
  `compatibility` (1-500 chars), `metadata` (string to string map), `allowed-tools`
  (experimental, space-separated).
- Progressive disclosure: name + description (~100 tokens) always loaded; body (< 5000 tokens,
  < 500 lines recommended) on activation; resources on demand. Keep references one level deep.
- There is no version field: put semver in `metadata.version` (string). There is no inheritance,
  overlay or variant mechanism in the standard.
- Validator: `skills-ref validate ./my-skill`
  (https://github.com/agentskills/agentskills/tree/main/skills-ref).

## 2. Per tool

### Claude Code (https://code.claude.com/docs/en/skills)
- Locations: managed (enterprise), personal `~/.claude/skills/<name>/`, project
  `.claude/skills/<name>/` (start dir and parents up to the repo root; nested dirs load when Claude
  touches files there), `--add-dir`, plugins (`<plugin>/skills/`, namespaced `/plugin:skill`),
  claude.ai account skills.
- Precedence on the same name: **enterprise > personal > project**. Plugin skills are namespaced,
  so a plugin skill and a local skill both load. **Tested**: a personal `release-train` hid the
  project's `release-train` completely.
- Front matter beyond the spec: `when_to_use`, `argument-hint`, `arguments`,
  `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`,
  `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`. Unknown keys are ignored.
  Only the six spec keys work on claude.ai and the Skills API; the others are a hard error there.
- `description` + `when_to_use` are cut at 1,536 chars in the listing; the listing budget is about
  1% of the context window (`skillListingBudgetFraction`, `skillListingMaxDescChars`).
- Substitutions: `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `$ARGUMENTS`, `$0`... They also
  work in `allowed-tools`, e.g. `Bash(${CLAUDE_SKILL_DIR}/scripts/x.sh *)`.
- Symlinked skill folders are followed and deduplicated. Live reload of skill folders, except a
  top-level skills dir created mid-session (`/reload-skills`).
- Reserved: a folder named `synced`; names starting with `anthropic-skills` outside a plugin.
- `skillOverrides` in any settings file maps a skill **name** to `on`, `name-only`,
  `user-invocable-only` or `off` (https://code.claude.com/docs/en/settings-reference.md). It is
  keyed by name, so it cannot hide only the personal copy of a name; it does not apply to plugins.
- Plugins and marketplaces (https://code.claude.com/docs/en/plugin-marketplaces):
  `.claude-plugin/marketplace.json` with sources `./path`, `github`, `git-subdir` (a plugin inside
  a monorepo), `url`, `archive`, `npm`, `command`; pin with `ref`/`sha`.
  `claude plugin validate <dir>` checks a plugin, a marketplace, or a plain skills folder
  (`claude plugin validate .claude/skills`, v2.1.233+).
- **Personal plugin in the skills folder (tested)**: a folder `~/.claude/skills/<p>/` with
  `.claude-plugin/plugin.json` and `skills/` loads as plugin `<p>@skills-dir` (scope user), with
  namespaced skills `/<p>:<skill>`. A project's `.claude/settings.json`
  `{"enabledPlugins": {"<p>@skills-dir": false}}` switches it off in that project only. This is
  the clean way to keep user-level skills from shadowing a project's patched ones.

### Codex (https://developers.openai.com/codex/skills, now https://learn.chatgpt.com/docs/build-skills)
- Repo: `.agents/skills` in every directory from the working directory up to the repo root.
  User: `~/.agents/skills`. Admin: `/etc/codex/skills`. System: bundled.
- `~/.codex/skills` is the legacy user location. It is still scanned and **not deduplicated**
  against `~/.agents/skills`, so leftovers show twice
  (https://github.com/oomol-lab/oo-cli/pull/254).
- Symlinked skill folders are followed.
- Same name in two places: both appear; no defined winner. **Tested** with
  `codex debug prompt-input`: a project `review-stack` and a user `review-stack` are both listed.
- Disable one skill: `[[skills.config]] path = ".../SKILL.md"` + `enabled = false` in
  `~/.codex/config.toml` (**tested**: works). The same entry in a trusted project's
  `.codex/config.toml` did not hide it (**tested**).
- Optional `agents/openai.yaml`: UI metadata, `policy.allow_implicit_invocation`,
  `dependencies.tools` (e.g. an MCP server).
- Initial skills list budget: 2% of the context window or 8,000 chars
  (`skills.max_context_tokens`, max 10,000 tokens).
- `codex debug prompt-input "hi"` prints the model-visible prompt, including the skills list and
  their roots, without a model call: the best way to test discovery offline.

### OpenCode (https://opencode.ai/docs/skills, https://opencode.ai/v2/docs/skills/)
- Project: `.opencode/skills/` (docs) and the original singular `.opencode/skill/` (**tested**:
  both are scanned in 1.19.5), plus `.claude/skills/` and `.agents/skills/`, from the working
  directory up to the worktree. Global: `~/.config/opencode/skills/`, `~/.claude/skills/`,
  `~/.agents/skills/`. Extra paths and remote catalogs through a `skills` array in
  `opencode.json`. Permissions per skill: `permission.skill` with `allow`/`ask`/`deny`.
- The docs say later sources override earlier ones by name, with `.opencode/` last.
  **Tested in 1.19.5: not true.** With the same name in `.claude/skills`, `.agents/skills` and
  `.opencode/skills`, six runs of `opencode debug skill` returned different winners; even
  `.opencode/skills` versus `~/.config/opencode/skills` is random. The scan is concurrent and the
  last one to finish wins.
- It scans `~/.claude/skills` recursively: the skills inside a Claude plugin folder there show up
  under their bare names (**tested**).
- `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` (and `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`) turn off the
  `.claude` and `.agents` folders, global and project (**tested**).
- `opencode debug skill` lists every skill with its resolved file, without a model call.

## 3. Existing managers and sync tools

| Tool | What it does | Missing for us |
|---|---|---|
| dotagents (Sentry, https://docs.sentry.io/ai/dotagents/) | `agents.toml` + `agents.lock` (commit + sha256 per skill), installs into `.agents/skills`, symlinks each tool's folder to it; MCP and hooks too; `install --frozen` in CI | No patches/overlays, no per-tool variants, symlinks, no user-level shadowing story |
| rulesync (https://github.com/dyoshikawa/rulesync) | One `.rulesync/` source generating rules, commands, subagents, MCP, skills for 60+ tools; global mode for some | Generator, not an overlay system; no layered bases or lockfile |
| Ruler (https://github.com/intellectronica/ruler) | `.ruler/` rules concatenated into each agent's file; skills (experimental) copied into each agent's folder | No versions, no patches |
| OpenSkills (https://github.com/numman-ali/openskills) | `npx openskills install/sync/read`; writes an `<available_skills>` block into AGENTS.md so any agent can `openskills read <name>` | Indirection through a CLI at run time; no overlays |
| SkillPort (https://pypi.org/project/skillport/) | CLI + MCP server: validate, add/update from GitHub, search/load on demand; filtering by env vars | Per-skill version pins absent; MCP indirection |
| Vercel `skills` CLI (https://codex.danielvaughan.com/2026/05/31/codex-cli-vercel-skills-cli-npx-skills-open-agent-skills-ecosystem/) | `npx skills add/find/update`, symlinks into 27+ agents' folders, skills.sh directory | No lockfile, no overlays |

None of them patches a base skill per project, renders per-provider variants, or handles the
Claude "personal beats project" rule. That gap is what `overlay/agentskills` covers.

## 4. Nix / home-manager

- `programs.claude-code` (https://mynixos.com/home-manager/options/programs.claude-code):
  `skills` (attrset of text/path, or a directory), `plugins` (attrset of path/package; since
  Claude Code 2.1.157 each plugin is symlinked into `~/.claude/skills/` and loaded as a personal
  plugin), `marketplaces`, `settings`, `agents`, `commands`, `hooks`, `rules`, `mutableSettings`.
- `programs.codex` (https://nix-community.github.io/home-manager/options/home-manager/programs/codex.html):
  `skills` writes `CODEX_HOME/skills` (= the legacy `~/.codex/skills`), so combining it with
  `~/.agents/skills` produces duplicates in Codex.
- `programs.opencode.skills`: attrset or directory, symlinked into
  `$XDG_CONFIG_HOME/opencode/skills/`.
- Our module (`overlay/nix/home-manager.nix`) does not use those options, so it works whether or
  not Brian enables them, and it renders variants per tool at build time.

## 5. What few people know yet (the short list)

1. A personal Claude skill silently shadows a project skill with the same name. Ship user-level
   skills as a personal plugin folder in `~/.claude/skills/<p>/` and let projects disable
   `<p>@skills-dir` in `.claude/settings.json`.
2. OpenCode 1.19 resolves duplicate skill names at random, contrary to its docs, and reads Claude
   plugin folders recursively. Unique names plus `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` make it
   deterministic.
3. Codex moved user skills to `~/.agents/skills`; home-manager's `programs.codex.skills` still
   writes the legacy folder, which Codex lists a second time.
4. `codex debug prompt-input` and `opencode debug skill` show exactly what the model will see,
   with no API key: use them as discovery tests in CI.
5. Claude-only front matter (`context: fork`, `model`, `hooks`...) makes a skill fail upload to
   claude.ai and the API; render it only into `.claude/skills`, keep spec keys elsewhere.
6. An unquoted ` #` inside a YAML description silently truncates it (found by Arffornia's
   agent-kit lint); always quote descriptions.
7. `claude plugin validate .claude/skills` validates a plain skills folder, not only plugins.
8. Artifact pages run in a frame that refuses microphone access unless a runtime capability
   grants it, and this account's runtime (contract 0.2.92) offers none. OS dictation into a plain
   textarea (phone keyboard mic, macOS Dictation, Windows Win+H) is the voice input that works.
