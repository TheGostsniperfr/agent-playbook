# Maintaining the runbook

The runbook is a living document. Agents improve it as they use it; the owner reads the changes
in the weekly digest, not page by page.

## When to patch

Patch in the **same session** that taught the lesson, before the final report:

| Trigger | What to change |
|---|---|
| An anti-pattern hit for real (with an incident) | Add it to the phase page's "Anti-patterns we hit": what happened, the fix, the lesson |
| The owner corrects an agent or overrides a default | Update the "Decisions" table default and its "Why"; add a line to [DECISIONS.md](DECISIONS.md) for that project |
| A step was missing or wrong | Fix the "Steps" list; add a checklist item if it is checkable |
| An idea from [IDEAS.md](IDEAS.md) was applied | Move it into the phase page, remove it from IDEAS, note the result |
| Research finds a better practice | Add it to IDEAS.md with value, effort, source URL and read date |
| A rule needs a sensor | Do not patch the runbook only: open a `harness-feedback` issue in the harness repo |

Do not patch for one-off environment quirks of a single session (a flaky network call). Patch
when the lesson would change what the next agent does.

## How to patch

1. Work in a worktree of this repo; branch `runbook/<slug>`.
2. Keep each page under ~150 lines. If a page grows, move detail into a new page and link it
   (map, not manual). English, imperative, concrete; every claim from outside has a URL and a date.
3. Name projects only as examples ("on Arffornia, ..."); the rule itself stays generic.
4. Never write secrets, private URLs that leak data, or unfixed vulnerability details.
5. Add a line to [CHANGELOG.md](CHANGELOG.md) under "Unreleased": date, page, one-line change,
   source (session link, PR or issue).
6. Commit with Conventional Commits (`docs(runbook): ...`) and the session trailers. Open a PR;
   runbook PRs are class A unless they change a default (then class B, listed on a chantier page).

## Versioning

- Semantic versions on the whole runbook: **major** = a phase added, removed or reordered, or a
  default reversed; **minor** = new decisions, steps, anti-patterns or ideas; **patch** = wording.
- A release moves "Unreleased" under a version heading and tags `runbook-vX.Y.Z`.
- Overlays and project copies record the runbook version they follow, so a reader can diff.

## Review loop

- Monthly (with the harness audit): an agent reads the changelog since the last tag, checks each
  page is under the size budget, that links resolve, that IDEAS are still ranked sensibly, and
  proposes a release.
- When a model or tool generation changes, re-read the "Decisions" tables: some defaults exist to
  work around model limits that may be gone ([IDEAS.md](IDEAS.md) #5).
