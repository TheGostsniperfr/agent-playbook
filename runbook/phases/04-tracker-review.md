# Phase 4 · Tracker and review stack

**Goal:** one tracker where agents and humans meet, and a review flow where the human spends
minutes per **chantier** (a group of PRs plus its decisions), never hours per PR.

A human kanban stretched over agents fails: agents produce more cards than a person can scan,
and every column fills up. Split the board into two lanes with different rules.

| Lane | Who works it | Unit | Rule |
|---|---|---|---|
| **Work lane** | Agents | Issue (one outcome, acceptance criteria) | Pull the next *ready* issue: `agent-ready`, no open blocker, highest priority |
| **Attention lane** | The owner | Chantier page | A short stack, ordered by what unblocks the most work; WIP limit 3 |

## Decisions to take

| Decision | Arffornia default | Why |
|---|---|---|
| Tracker | GitHub issues in the repo they change + one org Project ([ADR-0004](https://github.com/Arffornia/docs/blob/main/docs/decisions/0004-github-issues-as-tracker.md)) | Agents and contributors live on GitHub; Notion keeps long-form ideation only |
| Labels | `type:*`, `area:*`, `priority:P0-P3`, `effort:S/M/L`, plus `agent-ready` / `needs-decision` / `proposal` | The labels *are* the routing: agents take `agent-ready`, never `needs-decision` |
| Milestones | M1 Foundation & security, M2 Tests & CI, M3 Product foundations | Coarse order without sprint ceremony |
| New ideas from agents | `proposal` issues; only the owner promotes them | The owner asked for proposals, not additions |
| Board filling | Scheduled Action syncing every open issue and PR (GraphQL inside Actions, scoped PAT) | The session had no GraphQL |
| Unit of human review | **Chantier page** (artifact or doc): what it is, PRs in merge order, decisions with a recommended default, what was verified and what was not | The owner refused to review and merge PRs one by one |
| Who merges | An orchestrator agent merges a chantier after the owner validates it | Validation is the human act; clicking merge is not |
| Answer format | Each decision: Agree / Other / Later, a free-text field, and voice dictation; answers stored and read back by the agent | Fast, mobile, no retyping; nothing lost between sessions |
| Queue location | A board column "Ready for owner" holding one card per chantier, linking its page | One place to find every pending review; the owner lost artifacts before |

## Chantier page template

1. **Verdict line:** "Validate to merge N PRs in M repos; K decisions; risk low/medium/high."
2. **Decisions** first, each with question, recommended default, links, answer controls.
3. **PRs in merge order**, each: full URL, one-line summary, CI state, class
   (A merge on green / B look at one thing / C test by hand first).
4. **Verified** (commands and results) and **not verified** (and why, in plain words).
5. **After merge:** owner actions (restart, rotate, tag), in order.

## Steps (agent)

1. Create labels and milestones in every repo (REST). File audit tickets with Context /
   Evidence / Acceptance criteria / Notes. Skip ones an open issue already covers.
2. Migrate real tasks from the old tracker; leave template rows.
3. Group open PRs into chantiers by theme and dependency (foundation, security, i18n, harness...).
4. Publish one page per chantier; add one card per chantier to the queue column.
5. Read answers back at the start of each session; apply them (labels, issue comments, merges).
6. Close the card when merged; post the chantier summary on each PR.

## Human touchpoints

- Pop the queue: open the top chantier, answer the decisions, validate. Nothing else.

## Anti-patterns we hit

- **One giant handover**: 71 PRs, 34 decisions and 14 proposals on one page, plus separate
  artifacts the owner could not find again. Cap a chantier at ~15 PRs and ~8 decisions; index
  every page in the queue.
- **A merge guide was needed** to explain stacking, merge commits and retargeting. Fold that
  into the chantier page and, better, into the orchestrator.
- **Expected-red PRs** (red until another merges) look broken. Mark them on the page.
- **Many tickets in the same column**: status columns do not scale for agent throughput. Use
  readiness (labels + blockers) for agents, the chantier queue for humans.
- **AI review built as a CI workflow** needing an API key the owner would never add. Ask about
  credentials before building review automation ([phase 5](05-harness-skills.md)).

## Checklist

- [ ] Labels and milestones identical in every repo; board synced automatically
- [ ] Every issue is `agent-ready` (with criteria), `needs-decision` (with a default) or `proposal`
- [ ] Every open PR belongs to exactly one chantier; every chantier has a page and a queue card
- [ ] Pages store answers; the agent reads them back before acting
- [ ] Queue has at most 3 open chantiers; the rest wait in the work lane
