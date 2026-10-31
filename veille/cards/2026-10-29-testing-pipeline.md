---
title: "Automated testing pipeline: how Arffornia's works and the state of the art"
date: 2026-10-29
topic: testing
level: intermediate
sources: 27
status: new
page: ""
project: arffornia
---

# Automated testing pipeline: how Arffornia's works and the state of the art

## The 30-second version

Arffornia now tests every repository at four levels: the agent cannot finish a task until
`make check` passes (Stop hook), every pull request runs that same check plus real end-to-end
suites (a browser for the website, the real Electron app for the launcher, a headless Minecraft
server for the mod), nightly jobs run the slow or networked tests, and architecture guards fail
any new layering violation. About 450 automated tests now exist where there were a handful a
week ago. The best teams in the world (Google, Meta) add three things we do not have yet:
**mutation testing on each diff** (it tells you whether the tests would catch a bug, not just
whether they pass), **automatic flaky-test quarantine**, and **LLM-generated tests that are
only kept when they provably kill a planted bug**. The step that would put Arffornia ahead of
most game studios is ADR-0007, resized to the homelab: a test server for any PR in one
command, where bots and then an agent play the feature before a human sees it. Updated
2026-10-31: five proposals kept (the high-value ones), the 2019 Meta source marked as dated.

## How ours works

### Level 1: inside the agent's session (agent-kit v2)

- **Format as it goes**: a PostToolUse hook formats and lints only the file just edited.
- **Stop gate**: the Stop hook runs `make check` before the agent may hand back, cached per tree
  state, with a loop guard (`plugins/arffornia/scripts/stop.sh`, 82 offline hook tests).
  https://github.com/Arffornia/agent-kit/pull/2
- **Independent test-writer**: the `test-writer` subagent writes tests from the issue's
  acceptance criteria only, in a worktree of the default branch, so it cannot see the
  implementation (no self-grading). The `verifier` subagent has no edit tools.
  https://github.com/Arffornia/agent-kit/pull/3
- **Proof by breaking**: every fix PR in the merge pack reports that the new tests fail on the
  old code ("the old code failed 4 tests", "4 of 8 new tests fail on the old code", the
  GameTest suite exits 1 when the unlock check is disabled). This is mutation testing done by
  hand, one mutant at a time.
- **Stability runs**: suites suspected of flakiness are run repeatedly before claiming green
  (Nexus_Mods 16/16 after fixing a nock leak that failed about 50% of runs; contract tests
  3 runs; Nexus_Logger 15 runs).
- **In-session AI review** at the end of the task (finders, then independent verifiers that
  vote). The owner decided against AI review as a CI job and against API keys in GitHub.

### Level 2: every pull request (GitHub Actions)

| Repo | Suite | What it proves |
|---|---|---|
| Arffornia_Website | PHPUnit, 104 tests on sqlite and 104/104 on Postgres 16 | Services, controllers, a concurrency test for atomic shop purchases |
| Arffornia_Website | API contract tests (72 on their branch, PR #95) | The endpoints the mod, proxy and launcher call keep their shape and auth rules |
| Arffornia_Website | Playwright E2E, 7 journeys (`e2e.yml`, deterministic seed, PR #96) | Podium, news, shop/stages/rules pages, profiles, OAuth redirect carries `state`, admin closed to anonymous users |
| Launcher | Vitest, 152 tests | Main process: IPC validation, log redaction, RAM settings, checksum downloads |
| Launcher | Playwright-for-Electron, 5 tests under xvfb (PR #65) | Real app boots on mocked endpoints, routes, language persists, renderer has no Node access, CSP set |
| Arffornia_Mods | GameTests, 15 (`gametest.yml`, `runGameTestServer`, PR #48) | Crafter energy, output full, save/load, locked recipes rejected, packets rejected without menu or from far away, elevator credits its owner. Runs against an in-memory `ProgressionBackend` fake |
| Arffornia_Mods / Proxy | JUnit (stub `HttpServer`) | API client timeouts and bounded 401 re-auth; reward command allow-list |
| Arffornia_Provisioning | Jest, 40 tests | modList and index schema, no duplicates, server mods subset of launcher mods, index fresh, paths stay inside `storage/` |
| Nexus_Mods / Java / Logger / Saver | Jest, 60 / 20 / 17 / 19 | Offline: axios mocked, fake JDK archives built in a temp dir, a run with the proxy pointed at a dead port proves no network |
| infra | Helm render + kubeconform (infra PR #42) | Every manifest is valid Kubernetes before Argo CD sees it |
| All repos | CodeQL, Trivy (`security.yml`), gitleaks template with a checksum-pinned binary | Code scanning, vulnerable dependencies, committed secrets |
| Mod, launcher, website | Architecture guards: ArchUnit (frozen store), dependency-cruiser (baseline of 11), deptrac | Today's violations are frozen; any new one fails with a message that says how to fix it |

### Level 3: nightly

- **Mutation testing templates** (agent-kit PR #1): Infection (PHP), Stryker (JS), PIT through an
  init script (Gradle), report only, scoped to critical modules (shop, votes, users,
  middleware). Not run yet.
- **Nexus_Mods live tests** against Modrinth, CurseForge mirror and GitHub, kept out of PR CI
  so PRs never fail because a third-party API is down.

### Level 4: planned

- **Per-PR preview servers** (ADR-0007, M3): a `preview` label builds an immutable bundle, an
  Argo CD ApplicationSet creates `arffornia-pr-<repo>-<n>`, a Job runs GameTests and scripted
  RCON checks, scans logs and posts on the PR. Guardrails: own AppProject, quota, default-deny
  network policies, lifetime cap.
- **Client screen harness** (spec 004): `runClientTest` under xvfb, one screenshot per screen,
  locale and GUI scale, a contact sheet and a `report.json` (no raw keys, no overflow).
- **Harness evals**: skill trigger evals 34/34, reviewer cases 5/5; the `review-feedback`
  automation turns review comments marked `wrong` or `noise` into new eval cases.

### Gaps

No flaky-test detection beyond manual reruns. Mutation testing never executed. No visual
regression baselines. No property-based tests or fuzzing. Nothing tested on macOS. `check` is
not yet a required status check on `main`. No coverage measurement anywhere.

## How the best do it

### Running the right tests: Google TAP and Meta predictive test selection

Google's TAP runs about 150 million test executions a day over more than 13,000 projects, with
roughly one commit per second. It selects tests by walking the build graph backwards from the
changed files, batches commits into "milestones" cut about every 45 minutes, and observed that
of 5.5 million affected tests only 63,000 ever failed; targets more than 10 dependency hops from
the change never caused a breakage in their data (Memon et al., ICSE-SEIP 2017).
Meta replaced "run everything the build graph reaches" with a gradient-boosted model trained on
three months of results: it runs under a third of those tests, still catches over 99.9% of
faulty changes, and halved the infrastructure cost (Machalica et al., 2018/2019).
**Dated source, checked 2026-10-31:** the paper is old, but the technique is still current: a
2025 replication study confirms it (Aichmann, TU Wien), and Gradle Develocity and Launchable
sell it. It only pays off with hours of tests per change; background only for us.

### Flaky tests: measure, quarantine, file a ticket

Google reported in 2016 that 1.5% of test runs were flaky, 16% of tests had some flakiness, and
84% of pass-to-fail transitions involved a flaky test. Their tools quarantine highly flaky
tests out of the critical path and file a bug to the owner.
Slack (2022) automated the whole loop: parse CI results, open a PR that disables the test with
a link to an auto-created ticket for the owning team, merge it through the queue. Test job
failure rate went from 56.76% to 3.85%.
Atlassian's Flakinator (December 2025) scores each test from 0 to 1 with a Bayesian moving
window (retry flips, duration variance, environment), quarantines it, files a ticket with a
deadline and brings it back once healthy; 350 million test executions a day, 7,000 flaky tests
found in a quarter.

### Mutation testing on the diff: Google

A mutant is a small planted bug (flip `<` to `<=`, drop a call). If no test fails, the tests
are blind there. Google's trick is to mutate only the lines changed in a code review, at most
one mutant per line, and to suppress "arid" code (logging, plumbing) with more than a hundred
rules learned from developer feedback. Median mutants per change dropped from 820 to 7. Across
776,740 changes, 2.1 million mutants were surfaced as review comments, and 82% of those with
feedback were rated productive (Petrović et al., TSE 2021).

### LLM test generation that has to prove itself: Meta

**TestGen-LLM** (February 2024) asks an LLM to extend existing test classes and keeps a test
only if it builds, passes repeatedly and adds coverage. Of generated tests, 75% built, 57%
passed reliably and 25% raised coverage; 73% of its recommendations were accepted by engineers.
**ACH** (January 2025) starts from a plain-text concern ("this must not leak user data"),
has an LLM plant mutants that match that concern, uses an LLM judge to drop equivalent mutants
(precision 0.95, recall 0.96 after stripping comments), then generates tests that kill the
rest. 571 privacy-hardening tests, 73% accepted by engineers.
Mark Harman's FSE 2025 keynote names the next step: **just-in-time catching tests**, generated
when a pull request is opened, designed to fail on that PR if it has a bug. Regression tests
cannot do this, because they must pass on the current code.

### Property-based testing and fuzzing

Property-based testing generates hundreds of random inputs and checks a rule that must always
hold, then shrinks a failure to the smallest example. Jane Street (30 developers interviewed,
ICSE 2024) gets most value from a few patterns: round-trip (encode then decode), comparing
against a simple model, and "never crashes". The main cost is writing generators.
Google's OSS-Fuzz now has LLMs write fuzz targets, fix their compile errors and triage
crashes: 26 new vulnerabilities, including CVE-2024-9143 in OpenSSL (probably two decades old),
370,000 new lines covered across 272 projects (November 2024).

### Visual regression

Playwright's `toHaveScreenshot()` stores golden images per browser and platform, compares with
pixelmatch (per-pixel `threshold`, total `maxDiffPixels`) and warns that baselines must be made
in the same environment that checks them; teams run it in a pinned container.
Fabric (another Minecraft mod loader) now ships client game tests: `runClientGameTest`
launches the real client, scripts input, takes screenshots, and runs under XVFB on CI.

### Ephemeral preview environments and agent self-verification

Argo CD's ApplicationSet pull-request generator creates one Application per open PR, filtered
by label, templated with `{{.number}}` and `{{.head_sha}}`, deleted when the PR closes.
OpenAI's harness engineering post (February 2026) goes further for agents: each git worktree
boots its own app and its own short-lived logs/metrics/traces stack, the agent drives the UI
through the Chrome DevTools Protocol, records a video of the bug, fixes it, and checks targets
such as "startup under 800 ms" with PromQL. About 1,500 PRs were merged in five months that way.

### Game test automation

- **Minecraft GameTest** (built into the game, exposed by NeoForge): structure templates,
  tick-based assertions, a headless server that exits non-zero. This is what our mod uses.
- **EA SEED** added reinforcement-learning agents to the scripted test bots of Battlefield 2042
  and Dead Space (CoG 2023). Their main lesson: getting research agents into a production
  pipeline is the hard part.
- **Ubisoft La Forge + McGill (CA2, May 2026)**: give the test agent the game's live call stack
  and a target function to reach; function coverage rose from 92.96% to 96.92% on Crafter.
- **TITAN (September 2025)**: LLM agents testing two commercial MMORPGs, 95% task completion,
  four previously unknown bugs, deployed in eight QA pipelines.
- **BugCraft (2025)**: turns Minecraft crash reports into steps and has a vision LLM agent
  replay them in the game; 34.9% of crashes reproduced end to end with GPT-4.1.
- **Voyager (May 2023)**: a GPT-4 agent in Minecraft that writes its own skills as code on
  Mineflayer, keeps a skill library, and has a second model judge success. 15.3x faster
  through the tech tree than earlier agents.
- **SIMA 2 (DeepMind, November 2025)**: one Gemini-based agent that plays many 3D games,
  including held-out MineDojo (Minecraft), and improves through self-directed play.

### Evals for the agents themselves

Anthropic's "Demystifying evals for AI agents" (January 2026): start with 20 to 50 tasks taken
from real failures; separate capability evals (low pass rate, room to grow) from regression
evals (near 100%); use code graders first, model graders where needed, and read transcripts;
report pass^k (all k tries succeed) when consistency matters, not only pass@k.
Claude Code's best-practices guide says the same thing from the other side: give the agent a
check it can run, ask for evidence, and use a fresh reviewer that has not seen the reasoning,
told to skip style.

## What's ahead of the curve

- **Tests that must prove their worth.** Few teams outside Meta and Google reject generated or
  new tests that do not kill a mutant. Combining our independent test-writer with diff-scoped
  mutants would put Arffornia in that group.
- **Just-in-time catching tests** at PR time are still an open research problem (Harman 2025).
  An agent session can approximate it today: the test-writer writes tests from the issue, they
  run against the PR, and any failure is a finding.
- **Agents that verify in a live environment**, per worktree or per PR, with their own
  observability (OpenAI 2026). For a game, that means a per-PR server and a bot that plays.
- **LLM playtesters** (TITAN, BugCraft) are in early production at a few studios.

### Hype check

- **Test impact analysis** matters at 150 million runs a day. Our slowest suite (GameTests)
  takes minutes. Not worth building; at most run the closest tests first in the Stop hook.
- **RL or LLM playtesters as a merge gate**: not reliable enough. BugCraft reproduces about
  one crash in three; EA reports integration as the main cost. Use them for exploration
  reports, never to block a PR.
- **Coverage percentage targets** reward tests that execute code without checking it. Mutation
  score answers the real question.
- **"AI writes all the tests"**: Meta keeps only tests that pass hard filters, and engineers
  still accept only about 73% of those. Generation without filters adds noise.

## What we could do next

Only the high-value proposals are kept (owner's request, 2026-10-31). Each becomes a spec first.

| # | Proposal | Value | Effort | First step |
|---|---|---|---|---|
| 1 | **Diff-scoped mutation in the agent's verify step.** Plant small bugs only in changed lines, one per line, about 7 per file; surviving ones are listed in the evidence. Automates our "break it, watch it fail" habit. | High | S-M | `make mutate-diff` wrapper: Infection with `--git-diff-lines --git-diff-base=origin/main`, Stryker with `--mutate <file>:<lines>`, PIT with `targetClasses` from the diff. Pilot on the website shop service. |
| 2 | **Mini-ACH: new tests must kill a planted bug.** The test-writer gets a concern ("a locked recipe must never be selectable"), plants 3-5 matching bugs, and keeps only tests that build, pass 5/5 on the base, and catch at least one. Runs in the agent session (no API key in CI). | High | M | Add an acceptance filter script to the `test-writer` agent; trial on Mods security issues. |
| 3 | **One-command test server per PR, then an agent that plays it** (ADR-0007, resized). Small single-mod servers are cheap; the full 330-mod pack runs one at a time on the homelab. Step 1: `make preview PR=<n>` starts server and client on the PR (locally is fine) with a test guide: what changed, what to check, what to report. Step 2: scripted bots per feature (join, place the Crafter, craft, check the reward, read RCON and logs). Step 3: an agent drives the game itself, the way Claude in Chrome drives a browser, as the last check before the owner tests; its report never blocks a merge. | Very high | L | A spec plus a benchmark of existing tools (Mineflayer, GameTest, BugCraft, Voyager, Mindcraft), then `make preview` for one Mods PR. |
| 4 | **Visual baselines for everything the owner reviews by eye**: Playwright `toHaveScreenshot` for website and launcher in a pinned container, the spec-004 client harness contact sheet for Minecraft screens, and the custom loading animation he asked for. The diff image goes on the review page. | High | M | Add 5 screenshot assertions to the website E2E inside the Playwright Docker image. |
| 5 | **Property-based tests and fuzzing where input is hostile**: jqwik on serverbound packet handlers and Crafter energy maths, fast-check on Nexus_Mods path confinement and index parsing. | High (security) | S-M | One fast-check property: no index entry can resolve outside the game directory. |

Dropped from the card: light flaky detection (nightly 5x rerun), pass^k evals and a required
`check` status are small hygiene already covered by the harness work, no decision needed; test
impact analysis is not worth it at our scale.

## Glossary

- **Architecture guard / frozen baseline**: a test that fails on forbidden dependencies; known
  violations are stored and only new ones fail (a ratchet).
- **Arid node**: code where a mutant is never useful (logging, plumbing), so it is not mutated.
- **ApplicationSet**: Argo CD object that generates many Applications, here one per PR.
- **Catching vs hardening test**: a catching test fails on a buggy change now; a hardening test
  passes now and guards against a future regression.
- **Contract test**: checks the shape and rules of an API that another component depends on.
- **Equivalent mutant**: a change that does not alter behaviour, so no test can kill it.
- **Flaky test**: passes and fails on the same code. **Quarantine**: still runs, no longer blocks.
- **Fuzzing**: feeding generated, often malformed input to find crashes. **Fuzz target**: the
  entry point that receives that input.
- **GameTest**: Minecraft's built-in test framework; a test is a structure plus tick-based
  assertions, run by a headless server.
- **Golden image**: the approved screenshot a visual test compares against.
- **Mutation testing / mutant / killed / survived**: plant a small bug; killed = a test failed,
  survived = the tests did not notice. **MSI**: share of mutants killed.
- **Oracle problem**: knowing what the correct output is; the hard part of generating tests.
- **pass@k / pass^k**: at least one of k tries succeeds / all k tries succeed.
- **Preview environment**: a short-lived copy of the system for one PR.
- **Property-based testing**: random inputs checked against a rule; failures are shrunk to a
  minimal example.
- **RCON**: Minecraft's remote console protocol, used to send commands to a server.
- **Stop hook**: a Claude Code hook that runs when the agent wants to end; ours blocks until
  `make check` passes.
- **Test impact analysis / test selection**: running only the tests a change can affect.
- **xvfb**: a virtual display so GUI apps run headless in CI.

## Sources

- Memon et al., "Taming Google-Scale Continuous Testing", ICSE-SEIP 2017. https://huang.isis.vanderbilt.edu/cs8395-f23/paper/google-testing-icse-seip-17.pdf (TAP volumes, milestones, distance finding)
- Machalica et al., "Predictive Test Selection", arXiv Oct 2018 / ICSE-SEIP 2019. https://arxiv.org/abs/1810.05286 (99.9% faulty changes, under 1/3 of tests). Dated; see the replication below.
- Aichmann, "Predictive Test Selection: A Replication Study", TU Wien, 2025. https://repositum.tuwien.at/handle/20.500.12708/215633
- J. Micco, "Flaky Tests at Google and How We Mitigate Them", 27 May 2016. https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html (figures as summarised in https://talent500.com/blog/google-flaky-test-mitigation-strategies/)
- A. Patel, "Handling Flaky Tests at Scale: Auto Detection & Suppression", Slack Engineering, 5 Apr 2022. https://slack.engineering/handling-flaky-tests-at-scale-auto-detection-suppression
- N. Malik, "Taming Test Flakiness", Atlassian, 8 Dec 2025. https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests
- Petrović, Ivanković, Fraser, Just, "Practical Mutation Testing at Scale: A view from Google", TSE 2021 (arXiv Feb 2021). https://homes.cs.washington.edu/~rjust/publ/practical_mutation_testing_tse_2021.pdf
- Alshahwan et al., "Automated Unit Test Improvement using Large Language Models at Meta" (TestGen-LLM), 14 Feb 2024, FSE 2024. https://arxiv.org/abs/2402.09171
- Foster et al., "Mutation-Guided LLM-based Test Generation at Meta" (ACH), 22 Jan 2025. https://arxiv.org/abs/2501.12862
- M. Harman et al., "Harden and Catch for Just-in-Time Assured LLM-Based Software Testing", FSE 2025 keynote, 14 May 2025. https://arxiv.org/abs/2504.16472
- Goldstein et al., "Property-Based Testing in Practice", ICSE 2024. https://cis.upenn.edu/~bcpierce/papers/icse24-pbt-in-practice
- Chang, Liu, Metzman, "Leveling Up Fuzzing: Finding more vulnerabilities with AI", Google Security Blog, 20 Nov 2024. https://security.googleblog.com/2024/11/leveling-up-fuzzing-finding-more.html
- Playwright docs, "Visual comparisons". https://playwright.dev/docs/test-snapshots
- Fabric docs, "Automated Testing" (client game tests). https://docs.fabricmc.net/1.21.11/develop/automatic-testing
- NeoForge docs, "Game Tests". https://docs.neoforged.net/docs/1.21.4/misc/gametest
- Argo CD docs, "Pull Request Generator". https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset/Generators-Pull-Request/
- R. Lopopolo, "Harness engineering: leveraging Codex in an agent-first world", OpenAI, 11 Feb 2026. https://openai.com/index/harness-engineering
- EA SEED, "Challenges of deploying RL agents for game testing", CoG 2023, 26 Jul 2023. https://www.ea.com/seed/news/cog23-challenges-deploying-rl-agents-game-testing
- Adaikkappan, Martineau, Romoff, Meger, "CA2: Code-Aware Agent for Automated Game Testing" (Ubisoft La Forge, McGill), May 2026. https://arxiv.org/abs/2605.13918
- Wang et al., "Leveraging LLM Agents for Automated Video Game Testing" (TITAN), 26 Sep 2025. https://arxiv.org/abs/2509.22170
- "Agents in the Sandbox: End-to-End Crash Bug Reproduction for Minecraft" (BugCraft), 25 Mar 2025, v2 10 Oct 2025. https://arxiv.org/abs/2503.20036
- Wang et al., "Voyager: An Open-Ended Embodied Agent with Large Language Models", May 2023. https://arxiv.org/abs/2305.16291
- Google DeepMind, "SIMA 2", 13 Nov 2025. https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/
- Anthropic, "Demystifying evals for AI agents", 9 Jan 2026. https://anthropic.com/engineering/demystifying-evals-for-ai-agents
- Claude Code docs, "Best practices". https://code.claude.com/docs/en/best-practices
- Stryker, "Incremental mode". https://stryker-mutator.io/docs/stryker-js/incremental/
- PIT, "Incremental analysis". https://pitest.org/quickstart/incremental_analysis/
- Arffornia internal: merge pack, agent-kit v2 PRs https://github.com/Arffornia/agent-kit/pull/1 , /pull/2 , /pull/3 ; ADR-0007 (docs, proposed).
