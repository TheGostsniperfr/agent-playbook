# Phase 5 · Harness and skills

**Goal:** an agent starts every session already knowing the repo state, what to do next and how to
verify it; cannot break the rules that matter; proves its work before a human sees it; and leaves
state the next session can pick up. "The harness makes the quality, not the model."

## Layers (Arffornia agent-kit v2)

| Layer | Lives in | Job |
|---|---|---|
| Context | `AGENTS.md` map, `.claude/rules/*.md` with `paths` front-matter, GOLDEN_PRINCIPLES.md | Load only what the touched files need |
| Start card | `SessionStart` hook | Branch, dirty files, last commits, PR + CI state, PROGRESS "Now", top 3 ready issues, verify commands (≤40 lines, cached) |
| Issue injection | `UserPromptSubmit` hook | `#12` in a prompt → title, labels, acceptance criteria, marked as data |
| Guard | `PreToolUse` hook + deny rules + sandbox | Blocks force-push, push to main, merges, releases, secrets, hand edits to lockfiles and generated files; every block says what to do instead |
| Per-edit sensor | `PostToolUse` hook | Format + lint the edited file only |
| Done gate | `Stop` hook | `make check` must pass on a changed tree (cached per tree), docs and PROGRESS reminders |
| Handoff | `PreCompact` / `SessionEnd` hooks | Append to PROGRESS.md automatically |
| Skills | Plugin `skills/` (open SKILL.md standard) | work-ticket, verify, review, exec-plan, threat-model, i18n-sync, stack skills... |
| Subagents | Plugin `agents/` | reviewer, verifier (no edit tools), test-writer (worktree, cannot see the implementation) |
| Evals | `evals/` | Trigger tests per skill, reviewer cases from real findings |

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Distribution | A plugin in a marketplace repo, enabled at project scope; repos keep a tiny `settings.json` | One update reaches every repo; no copy drift |
| Scopes | Personal generic base (this repo) → org plugin (agent-kit) → repo `.claude/` overlay | See [ADAPT.md](../ADAPT.md); generic skills do not belong to one org |
| Escalation | A rule an agent breaks twice moves from guide to sensor (hook, lint, test, CI) | Written rules alone are suggestions |
| Review | **At the end of the task, inside the agent's session**: a fresh-context reviewer (custom subagent or `/code-review`), findings fixed before the PR. No AI review job in CI | No API key in GitHub; the agent that has context and budget fixes its own findings |
| Model per role | Main session: Opus, medium effort. Verifier and security review: Opus. Mechanical subagents (link checks, file collection, lang parity): Haiku. Raise *effort*, not model, for tricky bugs | Sources below |
| Agents beyond Claude | Same skills exposed to Codex/OpenCode via `.agents/skills` (sync script) | Open standard; test each skill in two agents |
| Sandbox | On by default with a registry allow-list | Shell commands confined; deny rules still apply first |

**Model cost evidence.** Agents use ~4x the tokens of chat and multi-agent systems ~15x; token use
explained 80% of performance variance in Anthropic's research eval
([Anthropic, Jun 2025](https://www.anthropic.com/engineering/multi-agent-research-system)).
Claude Code docs: Opus handles most coding, Sonnet costs less on routine work, Haiku fits simple
subagents, effort is the main quality dial, and low-effort review reports fewer false positives
([best practices](https://code.claude.com/docs/en/best-practices),
[/code-review](https://code.claude.com/docs/en/code-review-local), read Oct 2026). Managed PR
review costs $15-25 per review ([Claude blog, Mar 2026](https://claude.com/blog/code-review)).
On a flat subscription the budget is rate limits, not dollars: spend Opus where judgment matters.

## Steps (agent)

1. Read the current official docs for hooks, plugins, skills, subagents, settings, memory before
   writing any file. Formats change; validate with `claude plugin validate`.
2. Build hooks as portable bash with an offline test suite; each hook does nothing quietly when
   a tool is missing. Escape hatches via environment, not files the agent can edit.
3. Write skills as workflows with `references/` and tested `scripts/`; descriptions say when to
   trigger. Run trigger evals; sharpen descriptions that miss.
4. Pilot in one or two repos (stacked on their foundation PR), then roll out.
5. Present the harness as one chantier with a page explaining each layer.

## Anti-patterns we hit

- **v1 was "too simple".** The owner wanted state of the art first. Research before building.
- **Unquoted ` #` in YAML front-matter** silently cut a skill description at `Closes #n`.
  Quote descriptions; lint skills.
- **`skills: [review]` preloaded the bundled `/review`**, not ours. Use scoped names
  (`plugin:skill`) and avoid names that shadow built-ins.
- **Subagent spawn depth** capped by an environment variable blocked nested finders. Fall back
  to sequential passes and say so.
- **Hooks in both settings.json and the plugin** run twice. Plugin only.
- **The CI review pipeline** (5 Opus agents per PR, 8 on sensitive PRs) was built before asking
  about credentials, then dropped. Ask first.

## Checklist

- [ ] Plugin validates; hook test suite green; shellcheck clean; works on macOS bash 3.2
- [ ] Start card under 40 lines and under 1 s warm
- [ ] Every guard block message says why and what to do instead
- [ ] End-of-task review runs in-session with fresh context; findings fixed or justified in the PR
- [ ] Skill trigger evals pass; skills tested in a second agent (Codex or OpenCode)
