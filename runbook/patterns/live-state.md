# Pattern: live state outside the chat

**Problem.** A long chat knows things no file holds: the owner's small wishes, decisions taken in
passing, links to pages. A new chat starts blank and redoes or contradicts work.

**Pattern.** One state file per project, `STATE.md` in a private ops repo, written by `handoff`
and read by `resume`. The review stack holds the live queue; the chat product's project docs
hold a copy for chats that cannot read the repo. Public repos point to the ops repo in one line.

**Why private.** The state names unfinished security work, people and plans; product repos may
be public. The playbook itself never holds a project's state.

**Format and rules:** [`skills/handoff/references/state-format.md`](../../skills/handoff/references/state-format.md).
**Lint:** `skills/handoff/scripts/state_lint.py STATE.md --live` (structure, https links,
secret patterns, and links whose wording disagrees with GitHub).
