# Veille index

Newest first. Status: new, read, applied, dropped.

| Date | Card | Topic | Status | Review page |
|---|---|---|---|---|
| 2026-10-29 | [Automated testing pipeline: how Arffornia's works and the state of the art](cards/2026-10-29-testing-pipeline.md) | testing | new | (to be published) |

## Next cards (proposed, not written)

1. **Multi-agent code review with a verifier quorum**: finders by lens, independent verifiers that vote 2 of 3, why it runs in the agent session and not in CI; compare with Anthropic Code Review, Google Critique/ML code review, and research on LLM review false positives.
2. **Harness engineering: guides before, sensors after**: SessionStart cards, Stop gate, PreToolUse guard, teach-on-failure messages; Anthropic long-running harnesses vs OpenAI harness engineering; the reusable core of the runbook.
3. **Ratchets: architecture guards with frozen baselines**: ArchUnit freezing, dependency-cruiser baselines, deptrac; how a codebase gets better without a big-bang refactor; links to Google/Meta "monotonic" quality gates.
4. **Running a project with AI agents instead of a human kanban**: review stack of chantiers, agent-ready vs needs-decision, decision defaults, board sync via Actions; what AI-native teams do (OpenAI, Anthropic, Linear agents). The owner asked this question directly.
5. **Supply chain for small teams**: checksum-verified atomic downloads (NeoForge, Azul JDK, mods index), npm provenance and trusted publishing, pinned gitleaks binary, Dependabot cooldown; compare with SLSA and OpenSSF Scorecard.
6. **Diagram-as-code with Noodle and drift detection**: model/view split, draw.io export in CI, detecting when diagrams lie about the code; compare with Structurizr C4, IcePanel, Mermaid.

Considered, lower value for now: SVG profile engineering (narrow), i18n parity checking with pseudo-locales (good, but small: fold into a "checks that teach" card later).
