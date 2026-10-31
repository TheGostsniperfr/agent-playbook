# Brian's global agent instructions (installed by agent-playbook)

- At the start of any session on a project, look for live state before anything else: a
  `STATE.md` in the project's private ops repo, a `START-HERE.md` or `STATE.md` in the claude.ai
  Project docs, or a "Resuming" line in AGENTS.md. If found, run the `resume` skill.
- If there is none and the work is more than a one-off question, propose to set up the method:
  `bootstrap` for an existing repo or org, `new-project` for an idea. The continuity pack
  (ops repo + STATE.md + START-HERE) is always its first item.
- Before ending a task, run `handoff` so the next session can resume.
- Talk to Brian in French; code, docs, issues and PRs in English. No paid tools or services.
- Report at high level: done, problems, axes taken, what needs Brian. Every link as a full URL
  with a one-line summary.
