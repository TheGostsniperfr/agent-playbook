---
name: new-project
description: "Onboard a brand-new project from an idea: one batched interview with defaults, a one-page vision (users, problem, scope by milestone, constraints including free-only tooling), architecture options as ADRs, repo and org layout, the first milestone's spec and agent-ready issues, then hand over to bootstrap so the method is in place from day one. Use when the owner has an idea but no code ('nouveau projet', 'I want to build...', 'start a project from scratch', 'onboard a new project'), or asks how to start a project with agents."
compatibility: "Works in any chat for the interview and specs; creating repos needs gh and owner rights (or the owner clicks)."
metadata:
  version: "1.0.0"
  author: "Brian Perret"
---

# New project (from idea to first milestone)

Specs before code. The owner decides the vision and the trade-offs; agents do the rest.

## 1. Interview (one message, defaults filled in)
Ask once, in the owner's language, with your best guesses pre-filled
([references/interview.md](references/interview.md)): the idea in one sentence, users, the
problem today, what success looks like in 3 months, must-haves vs nice-to-haves, platforms,
languages, budget (default: free tiers, open source, self-hosted only; a domain name is fine),
machines and hosting available, deadlines, licence, brand wishes, how much review time per week.

## 2. Vision page
One page: problem, users, the promise, non-goals, milestones M0 (walking skeleton: one path end
to end), M1, M2, risks, open questions with defaults. Publish it as a review page
(`review-stack`), owner validates or challenges.

## 3. Architecture options
For each structural choice (language and framework, data store, auth, hosting, monorepo or
several repos): 2-3 options with cost (money, ops, learning), a recommended default and why,
written as ADRs (`docs/decisions/NNNN-*.md`). Prefer boring, light, self-hostable tools; say
when a heavier one is justified. Research current practice with dated sources.

## 4. Layout and specs
- Repo plan: names, what lives where, the docs repo, the private ops repo.
- M0 spec: user stories with acceptance criteria, the first diagram, test strategy (what runs
  on every PR, what nightly), the deterministic guards for the chosen stack.
- Agent-ready issues for M0, each small and independently verifiable.

## 5. Hand over
Owner creates the org and repos (or approves the agent doing it), then run `bootstrap` with
the decisions already taken: foundation, docs, harness, review stack and STATE.md exist before
the first feature PR. End with `handoff`.
