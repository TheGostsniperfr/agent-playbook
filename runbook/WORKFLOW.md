# The owner's workflow with agents

This is how work flows between the owner and the agents. It overrides older pages where they
disagree (older text kept PR publishing and merging with the owner). Each org's harness repo and docs
copy this page into their GitOps files (AGENTS.md, CONTRIBUTING, the operating-model page).

## The seven steps

| # | Step | Who | Output |
|---|---|---|---|
| 1 | Propose chantiers | Agents | A chantier card on the review stack: what, why, size, risk |
| 2 | Write the spec | Agents | A spec or research page plus decisions, each with a default and a plain `why`. The owner validates or challenges |
| 3 | Implement and open the PRs | Agents | PRs opened by the agents themselves, after `make check` passes and the end-of-task review ran |
| 4 | End-of-task review | Agents | Independent in-session review (finders, verifiers); findings fixed before the chantier is marked ready |
| 5 | Human checks | Owner, via the review stack | Only what needs a human: decisions, high-risk or high-criticality points, manual tests with a guide |
| 6 | Validate the chantier | Owner | Approve on the review stack |
| 7 | Merge and deploy | Agents (orchestrator) | Merges in the chantier's order, deploys, marks the card done |

**Merge authority.** Agents merge only PRs that belong to a chantier the owner approved on the
review stack, in its merge order. Nothing else merges on an agent's initiative.

**New chantiers start with specs.** The first deliverable of a new chantier is a spec or research
page plus decisions with defaults. Agents implement directly only what the owner already asked
for explicitly, or what is clear-cut; everything else is marked "needs decision".

## Reporting to the owner
- High level only: what is done, the problems, the axes taken, what needs the owner.
- No test counts or routine evidence in reports: that stays in the PR.
- Every PR, issue or page mentioned: full URL plus a one-line summary.
- Decisions are readable cold: what it is, why it is asked, what each option changes, and every
  technical term explained in plain words (`review-stack` lints this).

## Money
No paid services. Free tiers, open source and self-hosted tools only; the exceptions are a domain
name or a few euros over a long period, and only when the owner agrees.

## Git, in plain words
- Agents work on their own branches in separate worktrees and open PRs; they never push to the
  default branch and never use plain `--force`.
- **`--force-with-lease`**, where a harness allows it, is only for an agent's own PR branch after
  a rebase (replaying its commits on top of the newest main). It means "overwrite my branch only
  if nobody else pushed to it since I last looked", so it cannot erase someone else's work. Teams
  that do not need it can block it; agents then add a merge commit from main instead.
- PRs merge with merge commits unless the repo says otherwise.

## Owner's time
The owner reviews in batches (evenings, weekends). So: no hard cap on work in flight; the stack
shows a soft "review load" (how many cards wait and their estimated minutes) instead. Proposals
never expire: after 30 days without activity they are marked dormant and resurface in the next
brief, never closed automatically.
