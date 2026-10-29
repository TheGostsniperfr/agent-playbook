# Phase 6 · Tests and CI

**Goal:** every repo can prove a change works without a human: fast offline tests on every PR,
end-to-end tests that drive the real app, architecture guards, and slower live or mutation jobs
at night. An agent's "done" is a green check plus a test that failed before the fix.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| PR CI scope | Offline only: unit, contract and schema tests, lint, typecheck, build | Network flakiness must not block PRs |
| Live tests | Nightly job (e.g. Nexus_Mods against real mod APIs) | Catches upstream changes without blocking work |
| E2E per stack | Playwright (web), Playwright for Electron (launcher), NeoForge GameTests (mod), JUnit (proxy), kubeconform + render (infra) | Drive the real app the way a user does |
| Contract tests | The API's consumers (mod, proxy, launcher) pinned as tests in the API repo (72 cases) | Cross-repo breakage shows up in one PR |
| Content repos | Schema and consistency tests (duplicates, server ⊆ client, freshness) | Content is code for players |
| Proof of a fix | Write the failing test first; the PR says "N of M tests fail without the fix" | Distinguishes a fix from a coincidence |
| Architecture guards | deptrac (PHP), dependency-cruiser (JS), ArchUnit (Java) with a frozen baseline of current offenders | New violations fail, old ones shrink over time |
| Mutation testing | Nightly, report only, scoped to critical modules | Measures test strength without slowing PRs |
| CI hygiene | Pinned actions and binaries with checksums, `contents: read`, no secrets in PR jobs | Supply chain |
| Platforms | Linux runners in CI; scripts also checked on macOS arm64 | The owner and contributors use Macs |

## Steps (agent)

1. Make tests runnable offline first (sqlite in-memory, fakes behind a seam such as a
   `ProgressionBackend` interface, temp dirs instead of real game folders).
2. Add one E2E scaffold per app with a deterministic seed and mocked external endpoints.
3. For each bug fix: failing test, fix, run the suite several times if timing is involved.
4. Wire guards into `make check` with a teaching message: the failure says how to fix it.
5. Add nightly jobs (live, mutation) as report-only; they open issues, not red PRs.
6. Visual checks: screenshots in both locales and both themes attached to UI PRs.

## Human touchpoints

- None while green. Hand-testing items (login on a real identity provider, installer on Windows)
  go into the chantier page as class C with exact steps.

## Anti-patterns we hit

- **Flaky test from a mock leaking between files** (nock in Nexus_Mods, ~50% failure). Fixed and
  proven with 16 consecutive green runs. Run new tests repeatedly before claiming stable.
- **"Red on purpose" PRs** (a schema test that fails until a content PR merges). Fine, but label it.
- **Guards that could not run here** (deptrac download blocked). Ship them, but mark the first
  adoption as the real test.
- **Tests needing a build artifact** (Vite manifest). Use `withoutVite()` or order `make check`.
- **Heavy builds in parallel** on a small machine. One Gradle build at a time, capped heap.
- **CI only on tags** before the takeover: nothing protected `main`. PR CI comes first.

## Checklist

- [ ] `make check` runs offline and in CI on every PR
- [ ] Each app has at least one E2E test driving the real UI or server
- [ ] Every fix PR states how many new tests fail without the fix
- [ ] Guards have baselines and fix-it messages
- [ ] Nightly jobs report without blocking
- [ ] New tests ran repeatedly green before the PR
