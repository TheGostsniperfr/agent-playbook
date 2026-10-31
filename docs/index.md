# agent-playbook

**Run software projects with autonomous AI agents, and keep the human for what matters.**

This is Brian Perret's method, written so any agent can apply it: a runbook, a base of generic
skills, an overlay system that adapts them to an org and a repo, and the conventions that let a
brand-new chat pick up a project where the last one stopped.

## The vision

- **The owner decides, agents do the rest.** Agents propose work, write specs, implement, open
  PRs, review each other, and merge once the owner approves. The owner spends minutes per
  *chantier* (a group of PRs plus its decisions), never hours per PR.
- **Nothing lives only in a chat.** Rules live in files, the live state of a project lives in
  one `STATE.md` in a private ops repo, and the review queue is one page.
- **Generic once, adapted thinly.** A skill is written once in the base; an org and a repo add
  small patches; the rendered result is what agents read, and changes are reviewed as a diff.
- **Tools before opinions.** Deterministic checks (static and dynamic analysis) run before any
  AI review. AI review looks for what tools cannot see.
- **Free.** Free tiers, open source, self-hosted.

![How work flows](diagrams/workflow.light.drawio.svg#only-light)
![How work flows](diagrams/workflow.dark.drawio.svg#only-dark)

## Where to go next

| I want to... | Read |
|---|---|
| Set the method up on an existing repo or org | [Deploy it](deploy.md) |
| Start a project from an idea | [Deploy it](deploy.md#from-an-idea) |
| Understand how the pieces fit | [How it works](how-it-works.md) |
| See the skills | [Skills](skills-catalog.md) |
| Follow the takeover step by step | [Runbook](runbook/README.md) |
| Read the tech-watch cards | [Tech watch](veille/README.md) |
