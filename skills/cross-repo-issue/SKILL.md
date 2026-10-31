---
name: cross-repo-issue
description: "Write a good issue on another project's repository (a tool, library or service you depend on) from work on your own project: search duplicates, follow the target's templates and contributing rules, give a minimal reproduction and the expected behaviour, tag the origin with a 'from: <project>' label (or an Origin line), and link both ways. Use when a bug, gap or feature request in a dependency shows up while working, when turning a field report into upstream issues, or when asked to file issues on another repo."
compatibility: "Needs gh (REST is enough) with issue write access on the target, or produces ready-to-paste issue text."
metadata:
  version: "1.0.0"
  author: "Brian Perret"
---

# Issue on another project's repo

The target's maintainers did not see your context. The issue must stand alone, be easy to
triage, and say where it came from so both sides can trace it.

## Steps
1. **Read the target's rules first**: `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/*`, labels
   (`gh api repos/<o>/<r>/labels --paginate --jq '.[].name'`), an AGENTS.md if any. Use their
   template's fields and their label names.
2. **Search for duplicates** (`gh api 'search/issues?q=repo:<o>/<r>+<keywords>'`). A match: add
   your evidence as a comment instead of a new issue.
3. **Write it** ([references/issue-shape.md](references/issue-shape.md)): one problem per issue;
   title says the behaviour, not the fix; minimal reproduction with versions; expected vs
   actual; impact on your project in one line; a proposed direction if you have one.
4. **Mark the origin.** Add the label `from: <project>` (lower-case project name, e.g.
   `from: arffornia`). If it does not exist and you may create labels, create it once
   (colour `#c5def5`, description "Requested from the <project> project"); otherwise put
   `Origin: <project> (<link to the source issue, report or PR>)` as the first line of the body.
   This keeps a trace of which consumer asked for what.
5. **Link both ways.** Note the new issue URL in your project's source (tracking issue, report
   or STATE.md), and link your source from the new issue when it is public.
6. **Batch** several issues from one report: create them in priority order, then post one
   summary comment or list (with full URLs) where your project tracks them.

## Rules
- Security problems in someone else's project: never a public issue with details. Use their
  security policy (SECURITY.md, private advisory) and tell the owner.
- No private details of your project (hostnames, secrets, unreleased plans) in a public repo.
- Same owner for both repos: still use the label, so the target's backlog shows its consumers.
