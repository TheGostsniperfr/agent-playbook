# Skill candidates seen so far

Status: `proposed` (spec only), `pr` (draft open), `adopted`, `dropped`. Org-specific ones live
in the org layer's own list; this file lists the generic ones.

| Candidate | Layer | Occurrences | Status |
|---|---|---|---|
| `handoff` / `resume`: write and read the live state file | base | long chats lost context; repo wrap-up skills | adopted (1.0.0) |
| `cross-repo-issue`: write an issue on another project's repo, with a `from: <project>` label | base | 18 diagram-tool issues from one field report; infra issues from app repos | adopted (1.0.0) |
| `bootstrap`: Chantier 0 on an existing repo or org | base | first takeover (12 repos) | adopted (1.0.0) |
| `new-project`: from idea to first milestone | base | owner request | adopted (1.0.0) |
| `pr-via-rest`: commit, push, open the PR through the REST API when GraphQL is blocked | base | repeated in most agent sessions (`git commit -> gh api` x2+ in the scanner) | proposed |
| `trusted-publishing`: move a package publish workflow to OIDC trusted publishing | base | 3 npm libraries in one week | proposed (pattern written in the runbook) |
| `docs-site`: MkDocs Material + diagrams + Pages workflow for a repo | base | docs repo, playbook site | proposed |
| `secret-rotation-guide`: owner-facing step-by-step for rotating a leaked credential | base | proxy service account, npm token | proposed |
| `stale-pr-salvage`: read an obsolete PR, extract good ideas into a fresh issue, close it | base | 4 stale PRs at cleanup | proposed |
