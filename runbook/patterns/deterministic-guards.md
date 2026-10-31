# Pattern: deterministic guards next to the AI harness

**Rule.** Every check that can be done by a tool is done by a tool, in `make check` (local, in
the agent's Stop gate) and in CI. The AI review looks for what tools cannot see. All tools below
are free and open source (or free for public repos).

| Concern | Tool (free) | Where | Notes |
|---|---|---|---|
| PHP types and bugs | PHPStan + Larastan (Laravel) | `make check`, CI | Level raised over time with a baseline file (ratchet) |
| PHP architecture | deptrac | CI | Layers as config; frozen baseline for old violations |
| JS/TS bugs and style | ESLint (flat config), `tsc --noEmit` | `make check`, CI | `typescript-eslint` strict on new code |
| JS/TS architecture | dependency-cruiser | CI | Forbidden imports (renderer -> main, cycles) |
| Java/Kotlin architecture | ArchUnit (`FreezingArchRule`) | test suite | Frozen violations file committed |
| Java static analysis | Error Prone or SpotBugs | build | Pick one; fail on new findings |
| Go | `go vet`, staticcheck, govulncheck | CI | |
| Security patterns (all languages) | Semgrep CE rules or GitHub CodeQL | CI | CodeQL is free on public repos only; Semgrep CE works everywhere |
| Secrets | gitleaks | pre-commit, CI | Pinned version, checksum-verified download |
| Dependencies | Dependabot or Renovate, `npm audit`/`composer audit`/OSV-Scanner | CI, monthly | Cooldown before taking new releases |
| Shell | shellcheck (and `shfmt`) | `make check` | `-s sh` for POSIX scripts |
| GitHub Actions | actionlint, zizmor | CI | zizmor finds injection and permission problems |
| Kubernetes and Helm | kubeconform, `helm lint`, kube-linter | CI | Validate rendered manifests, not templates |
| Docs and diagrams | `mkdocs build --strict`, Noodle lint, link check (lychee) | CI | |
| Tests that test | Mutation testing on changed lines (Infection, Stryker, PIT) | nightly, or verify step when cheap | Only where unit tests are fast |
| Dynamic checks | Playwright E2E, GameTests or the real app headless, fuzz/property tests on parsers | PR (fast set), nightly (full) | |

How to adopt in an existing repo: add the tool with a baseline (today's findings frozen), fail
only on new findings, shrink the baseline over time. Agents read the tool's message, so make it
say what to do ("fix-it" messages).
