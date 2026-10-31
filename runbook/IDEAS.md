# Ideas not applied yet (state of the art, Oct 2026)

Ranked by value for "autonomous agents, minimal human attention" divided by effort. Each idea
says what to do on the next project and cites a source (read date: 2026-10-29). When one is
applied, move it to the relevant phase page and log it in [CHANGELOG.md](CHANGELOG.md).

| Rank | Idea | Value | Effort |
|---|---|---|---|
| 1 | Autonomy by blast radius | High | M |
| 2 | End-of-task review with the built-in forked reviewer + `/goal` | High | S |
| 3 | Rule of Two and unreachable credentials | High | S |
| 4 | Dependency-graph "ready" queue for agents | High | M |
| 5 | Harness ablation when models change | High | M |
| 6 | Harness evals with pass^k, re-run on every harness change | High | M |
| 7 | Agent telemetry into Grafana | Medium | S |
| 8 | Blueprints: deterministic + agentic steps, max 2 CI rounds | Medium | M |
| 9 | Stage artifacts with one metric each (intent → spec → plan) | Medium | M |
| 10 | Mutation-guided test generation | Medium | M |
| 11 | Agentic property-based testing | Medium | M |
| 12 | Native worktree tooling: `claude -w`, `.worktreeinclude`, `/batch` | Medium | S |
| 13 | Completion-promise loops for long mechanical work | Medium | S |
| 14 | Scale-adaptive specs (quick flow vs full flow) | Medium | S |
| 15 | Advisor pattern for API-built automations | Low now | M |

## 1. Autonomy by blast radius
Let changes with a tight spec, small blast radius and covering tests merge without the owner;
route the rest to the chantier queue. Define tiers in `risk.yml` (paths → light/standard/deep),
and let the orchestrator merge "light + green + reviewed" PRs on its own, listing them in a
weekly digest. Production deploys stay "agent prepares, human authorises".
Source: Anthropic, *The AI-Native SDLC Playbook*, 21 Aug 2026,
https://claude.com/blog/the-ai-native-sdlc-playbook

## 2. End-of-task review with the built-in reviewer + `/goal`
`/code-review` runs a forked subagent that never saw the conversation, works on any plan (no API
key), takes `--fix`, `--max-findings`, and an effort level (low = fewer false positives). Trigger
it from the Stop gate or the work-ticket skill before the PR. Add "skip style" to custom review
prompts. For unattended runs, `/goal <condition>` has a separate model check after each turn.
Sources: https://code.claude.com/docs/en/code-review-local and
https://code.claude.com/docs/en/best-practices (read Oct 2026).

## 3. Rule of Two and unreachable credentials
Stricter than the trifecta: in one session an agent may have at most two of (A) untrusted input,
(B) sensitive systems or private data, (C) changing state or communicating externally. Opening a
PR is (C), reading issues is (A): an issue-driven agent must not also hold secrets. Make tokens
structurally unreachable: wire the git token into the remote at sandbox setup, keep OAuth tokens
behind an MCP proxy. Sources: Meta, 31 Oct 2025, https://ai.meta.com/blog/practical-ai-agent-security/ ;
Anthropic, *Scaling Managed Agents*, Apr 2026 (summary:
https://businessdatasolutions.github.io/ai-wiki/sources/2026-05-07-anthropic-managed-agents-decoupling-brain-hands).

## 4. Dependency-graph "ready" queue for agents
Replace status columns with a graph: blockers, parent/child, `ready` = no open blocker; atomic
claim; hash IDs that do not collide across branches; old closed items summarised ("memory decay").
On GitHub: sub-issues and "blocked by" links plus a `ready` query in the start card.
Source: Steve Yegge, Beads, https://github.com/steveyegge/beads
Evaluation (2026-10-31): Beads (`bd`, MIT, ~28k stars) stores issues in Dolt (a versioned SQL
database) inside `.beads/`, synced through a git ref; `bd ready`, atomic `--claim`, dependency
links, messages between agents. It has no GitHub Issues sync. Verdict: **complement, not
replace**. GitHub issues stay the shared record (humans, PRs that close issues, links on the
review stack); Beads fits as an agent's scratch queue for a multi-step chantier, kept in the
ops repo, and only once several agents run in parallel on the same chantier. Trial on one
chantier before adopting.

## 5. Harness ablation when models change
Harness components encode assumptions about model weaknesses that go stale (a context-reset
workaround needed for one model was useless for the next). On each model upgrade, disable one
rule or hook at a time, re-run evals, delete what no longer earns its cost.
Sources: Anthropic, *Harness design for long-running application development*, Mar 2026,
https://www.anthropic.com/engineering/harness-design-long-running-apps ; *Scaling Managed Agents* (above).

## 6. Harness evals with pass^k
Start with 20-50 tasks from real failures; split capability evals (low pass rate) from regression
evals (~100%); measure pass^k (all k trials pass) for reliability, read transcripts before
trusting scores; re-run whenever AGENTS.md, skills or hooks change.
Source: Anthropic, *Demystifying evals for AI agents*, 9 Jan 2026,
https://anthropic.com/engineering/demystifying-evals-for-ai-agents

## 7. Agent telemetry into Grafana
Claude Code exports OpenTelemetry metrics (`claude_code.session.count`, `token.usage`,
`cost.usage`, `pull_request.count`, `commit.count`, `code_edit_tool.decision`, `active_time.total`)
and events (tool decisions, API errors, subagent completions) once `CLAUDE_CODE_ENABLE_TELEMETRY=1`
and an OTLP or Prometheus exporter are set. Send them to the existing Prometheus/Grafana stack;
chart tokens per merged PR, guard blocks per week and first-pass CI success.
Source: https://code.claude.com/docs/en/monitoring-usage (read Oct 2026)

## 8. Blueprints
Encode workflows as code mixing deterministic nodes (lint, push, open PR) with agentic nodes
(implement, fix CI); cap at one or two CI rounds before handing to a human; shift lint left into
pre-push hooks; warm environment pool (our cloud setup snapshot is a start). Stripe merges 1,300+
agent PRs a week this way. Source: Stripe, *Minions part 2*, 2026,
https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2

## 9. Stage artifacts with one metric each
`intent.md` → `spec.md` → `plan.md` → PR, each committed; metrics: first-pass merge rate, rework
cycles, time waiting at each approval gate, first-pass CI success. Incidents re-enter as intents.
Source: *The AI-Native SDLC Playbook* (idea 1).

## 10. Mutation-guided test generation
Generate realistic mutants for a concern (privacy, auth, money), then have the LLM write tests that
kill them; an LLM filter drops equivalent mutants. Pairs with our nightly mutation jobs.
Source: Meta, *Mutation-Guided LLM-based Test Generation at Meta*, Jan 2025, https://arxiv.org/abs/2501.12862

## 11. Agentic property-based testing
An agent reads a module, infers properties, writes property-based tests and triages failures;
it found real bugs across popular Python packages. Apply to Nexus libraries and parsers.
Source: *Agentic Property-Based Testing*, arXiv 2510.09907, Oct 2025 (presented at NeurIPS 2025),
https://arxiv.org/abs/2510.09907

## 12. Native worktree tooling
`claude -w <name>` starts a session in a new worktree; `.worktreeinclude` copies gitignored files;
`/batch` splits a mechanical change into 5-30 worktree units with one PR each; `claude agents`
shows all background sessions. Replaces our hand-rolled worktree rule.
Source: https://code.claude.com/docs/en/best-practices (read Oct 2026).

## 13. Completion-promise loops
For long mechanical tasks, a Stop hook refuses to end until a completion tag appears, with
`--max-iterations`; run only in a sandbox. Source: VentureBeat on the "Ralph Wiggum" loop,
6 Jan 2026, https://venturebeat.com/ai/how-ralph-wiggum-went-from-the-simpsons-to-the-biggest-name-in-ai-right-now

## 14. Scale-adaptive specs
Spec frameworks overload small changes (4 user stories and 16 criteria for a small bug). Pick the
flow by size: issue only, quick spec, or full spec with constitution and checklists.
Sources: Böckeler, martinfowler.com, 15 Oct 2025,
https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html ; BMAD v6 quick vs full
flow, https://github.com/bmad-code-org/BMAD-METHOD ; GitHub spec-kit constitution.

## 15. Advisor pattern
Opus advises a Sonnet or Haiku executor within one API call (+2.7 points on SWE-bench Multilingual
at ~12% lower cost than Sonnet alone, per Anthropic). API only, not Claude Code; relevant once
automations run on the SDK. Source: https://claude.com/blog/the-advisor-strategy (Apr 2026).
