# Phase 1 · Audit

**Goal:** an evidence-based picture of every component, proposed tickets ready to file, and at
most five real design questions per component for the owner.

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Split | One auditor agent per component group, in parallel (5: website, launcher, mod+proxy, provisioning+infra, tracker) | Independent contexts, done in about an hour |
| Where auditors build | A throwaway copy in `/tmp/audit-<repo>/`, never the shared clone | Parallel agents, read-only clones |
| Evidence bar | Every finding has `file:line` or command output | Reports become issues without re-checking |
| Report format | Fixed 10 sections, max ~300 lines (below) | Comparable reports; one merge into a backlog |
| Run things for real | Install, build, run the tests, run `npm audit` / `composer audit` | "Builds" is a claim until you run it: the website image had not built for 5 days |
| Tracker audit | Read the old tracker (Notion) and classify real tasks vs template rows | 8 real tasks hid among sample rows |

## Report template (copy into the auditor prompt)

1. Purpose and role: what it does, how it talks to the others (APIs, URLs, auth, formats).
2. Stack and versions: current vs latest, end-of-life risks.
3. Build / run / test results: exact commands and outcome.
4. Security: vulnerable deps, committed secrets, risky code. Severity H/M/L.
5. Code quality and architecture: smells, dead code, TODO count, ADR candidates, a small diagram.
6. Tests: what exists, what is missing, recommended unit + E2E strategy for this stack.
7. Repo hygiene: README, LICENSE, CONTRIBUTING, SECURITY, CI, bots, templates, AGENTS.md,
   leftover non-English content (count + examples).
8. Small bugs spotted, with evidence.
9. Proposed tickets: title, type, priority P0-P3, effort S/M/L, acceptance criteria,
   agent-ready yes/no (yes = no design decision needed).
10. Questions for the owner: real design decisions only, max 5.

## Steps (agent)

1. Brief each auditor with the shared brief, the hard rules (read-only, copy before building,
   machine limits, the owner's constraints) and the template.
2. Draw the system **from code and manifests, not from docs**. Arffornia's diagrams corrected two
   beliefs: the site was not behind Cloudflare, and in-cluster calls hairpinned through the router.
3. Merge reports: dedupe tickets across components, rank P0 first, collect the questions into one
   decision list with a recommended default for each.
4. File tickets ([phase 4](04-tracker-review.md)) only after the owner has seen the P0 list.

## Human touchpoints

- Read the P0 list (security, data loss) and the batched questions. Answers can come later; every
  question has a default and is tracked as `needs-decision`.

## Anti-patterns we hit

- **Composer filled the shared disk.** A dist download failure made composer fall back to a git
  clone of phpstan's full history (11 GB, and a 6 GB VCS cache). Cap caches, watch `df`, and run
  heavy analysers in CI instead.
- **Live system unreachable.** The homelab was off, so nothing was checked against production.
  Say so in every report; list what must be checked live.
- **Owner's libraries look replaceable.** Auditors will suggest swapping custom libraries for
  popular packages. Forbid it in the brief when the owner wants to keep them; recommend fixes.
- **Template rows mistaken for tasks** in the old tracker. Classify before migrating.

## Checklist

- [ ] Every component has a report in `_audit/<name>.md` with the 10 sections
- [ ] Build and tests actually run (or the reason they could not)
- [ ] Findings carry evidence; P0s summarised for the owner in one message
- [ ] Questions merged into one list, each with a recommended default
- [ ] Throwaway copies deleted, disk back above the threshold
