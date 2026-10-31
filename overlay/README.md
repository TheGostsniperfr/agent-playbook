# How the three skill layers work, in plain words

An agent skill is a folder with a `SKILL.md` (instructions) and optional scripts and references.
Three layers build the skills an agent actually reads:

| Layer | Lives in | Holds | Example |
|---|---|---|---|
| 1. Personal base | `TheGostsniperfr/agent-playbook` `skills/` | Generic skills, useful on any project | `review-stack`, `handoff`, `bootstrap` |
| 2. Org layer | the org's harness repo, e.g. `Arffornia/agent-kit` `overlay/<org>.yaml` | Patches every repo of that org gets, plus org-only skills | "merge with a merge commit, never squash"; `mc-gametest` |
| 3. Project layer | each repo's `.agents/overlay.yaml` | Which skills this repo uses, version pins, its own patches | "post the page link in the tracking issue" |

The `agentskills` resolver reads layer 3, follows its `extends:` to layer 2, follows layer 2's
`base:` to layer 1, applies the patches in order (base, then provider variant, then org, then
project) and writes plain files into `.claude/skills` (Claude Code), `.agents/skills` (Codex)
and `.opencode/skills` (OpenCode). A lockfile records the exact commit of each layer and a hash
of each rendered skill.

```
agent-playbook/skills/review-stack/SKILL.md          (1) generic text
  + variants/codex.md                                   per-tool tweak, when needed
  + agent-kit/overlay/arffornia.yaml patches            (2) org rules
  + Arffornia_Website/.agents/overlay.yaml patches      (3) repo rules
  = Arffornia_Website/.claude/skills/review-stack/      what the agent reads (committed)
```

Why it is built like this:
- **No reinvented wheel.** A fix to a generic skill is made once in layer 1; every org and repo
  gets it with `agentskills update` and sees the rendered diff before merging.
- **The render is the truth.** Like rendered Kubernetes manifests, the rendered folders are
  exactly what the agent gets. `agentskills export` writes that full build; `agentskills preview`
  shows the rendered diff of a change; CI posts it on every PR (`overlay/ci/skills-preview.yml`).
- **Fail loudly.** If a base section that a patch targets is renamed, the render stops and says
  which patch to fix, instead of silently producing a different skill.
- **No secrets, no paid service.** Python standard library and git only.

Commands: `agentskills --help`. Format reference:
[skills/overlay-apply/references/overlay-format.md](../skills/overlay-apply/references/overlay-format.md).
Design and limits: [skills/DESIGN.md](../skills/DESIGN.md). Worked example:
[examples/](examples/) (a sample project extending an org layer, tested end to end in
`tests/test_agentskills.py::test_three_levels_from_git`).
