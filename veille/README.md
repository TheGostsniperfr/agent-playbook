# Veille: tech-watch cards

When agents build something impressive or state of the art, they write a **card**: how our version
works, what the best teams in the world do, what is ahead of the curve, and what we could do next.
The owner reads cards to learn and to propose improvements. A card is a short course on one topic,
grounded in work we actually shipped.

## Where things live

| Path | What |
|---|---|
| `veille/cards/<yyyy-mm-dd>-<slug>.md` | One card. The date is the day it was written. The slug is kebab-case, at most 5 words. |
| `veille/inbox/<yyyy-mm-dd>-<slug>.md` | Card proposals from agents (10 lines max each). Triaged into cards or deleted. |
| `veille/TEMPLATE.md` | Copy this to start a card. |
| `veille/INDEX.md` | One line per card: date, title, status, review page link. Newest first. |

## Card format

Front-matter (YAML), then the sections below in this order. Keep the whole card readable in
15 minutes; push detail into the sources.

```yaml
---
title: "Automated testing pipeline: how ours works and the state of the art"
date: 2026-10-29
topic: testing            # one word: testing, review, harness, ci, security, docs, i18n, infra, gamedev, ai-agents ...
level: intermediate       # intro | intermediate | advanced (assumed background of the reader)
sources: 24               # number of cited sources
status: new               # new -> read -> applied (or dropped)
page: ""                  # URL of the published HTML review page, filled by the orchestrator
project: arffornia        # where the "how ours works" part comes from; omit for generic cards
---
```

Sections:

1. **The 30-second version.** 4 to 6 sentences. If the reader stops here, they keep the one idea
   that matters.
2. **How ours works.** Precise and checkable: repos, files, commands, test counts, links to PRs.
   Say what is planned or not verified.
3. **How the best do it.** Named teams, papers and posts, with numbers and dates. Explain the
   mechanism, not just the result.
4. **What's ahead of the curve.** What only a few teams do today, plus a **hype check**: what is
   oversold, too early, or irrelevant at our scale.
5. **What we could do next.** A ranked table: proposal, value, effort (S/M/L), first step. Each
   proposal is small enough to become an issue.
6. **Glossary.** Every term of art used in the card, one line each.
7. **Sources.** Full URLs, with publication date and one line on what was taken from each.

Writing rules: English, plain sentences, no marketing words. Every number has a source. Mark
inferences as inferences. Prefer one diagram of our own system over decorative visuals.

## From card to review page

1. The agent writes the card in `cards/` and adds a line to `INDEX.md` with `status: new`.
2. The agent renders the card as one standalone HTML page in the house style (the "Agent Kit v2"
   look: Chakra Petch / Archivo / JetBrains Mono, orange-teal-slate tokens, light and dark, phone
   friendly, no external scripts). It includes at least one diagram of our system (inline SVG or
   `<pre class="mermaid">`). The page is saved next to the work reports, not in this repo.
3. The orchestrator publishes the page as a private artifact, writes its URL into the card's
   `page:` field and `INDEX.md`, and puts it on the owner's **review stack** (the same queue as
   chantier summaries) tagged `veille`, below any chantier that blocks work.
4. The owner reads it and replies with: keep / drop per proposal, and his own ideas. The card's
   status moves to `read`. Proposals he keeps become issues (labelled `agent-ready` or
   `needs-decision`) and their links are added under "What we could do next". When at least one
   ships, the status becomes `applied`.

## When an agent proposes a card

Propose a card only when all three are true:

- **We built or used it.** The card starts from real work in our repos, not from a news item.
- **It is genuinely high value to learn.** It is state of the art, or surprising, or a technique
  the owner can reuse elsewhere. A routine fix, a library upgrade or a config tweak is not a card.
- **There is something to propose.** At least one concrete next step that would improve our setup.

If unsure, write a 10-line proposal in `inbox/` (title, why it matters, what we built, 2-3 links)
instead of a full card. At most one full card per agent run, and only after the main task is done.
No fluff: a card that would only restate documentation is dropped.
