#!/usr/bin/env python3
"""Find work agents did twice: repeated command sequences across agent sessions.

"Done twice -> skill": this scans session transcripts (Claude Code ~/.claude/projects/**/*.jsonl,
Codex ~/.codex/sessions/**/*.jsonl, or any JSONL whose records carry a "command") and lists the
command sequences that appear in at least --min-sessions different sessions. Each hit is a skill
candidate for the propose-skill step. Deterministic, offline, Python 3.8+ standard library.

  repeat_scan.py [ROOT ...] [--since YYYY-MM-DD] [--min-sessions 2] [--top 15] [--json]
"""
import argparse
import collections
import json
import os
import re
import shlex
import sys

NOISE = {"ls", "cat", "cd", "pwd", "echo", "head", "tail", "wc", "grep", "find", "sed", "true", "sleep",
         "git status", "git diff", "git log", "git branch", "git show", "which", "mkdir", "rm", "cp", "mv", "df",
         "for", "do", "done", "then", "fi", "if", "else", "while", "tr", "sort", "uniq", "xargs", "test", "[",
         "du", "printf", "export", "set", "date", "jq", "awk", "cut", "tee", "git rev-parse", "git ls-files"}
OPT_WITH_ARG = {"-C", "-c", "-R", "--repo", "-f", "--file", "-p"}
SUBCMD = {"git", "gh", "npm", "pnpm", "yarn", "make", "docker", "kubectl", "helm", "composer", "php", "go",
          "cargo", "nix", "python3", "python", "node", "npx", "uv", "pip", "gradle", "./gradlew", "claude",
          "codex", "noodle", "agentskills", "terraform", "mvn", "bash", "sh"}


def commands_of(obj, out):
    """Collect shell commands from any record shape (Claude tool_use, Codex function_call...)."""
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use" and obj.get("name") in ("Bash", "shell", "exec") and isinstance(obj.get("input"), dict):
            c = obj["input"].get("command")
            if isinstance(c, str):
                out.append(c)
            return
        if obj.get("type") in ("function_call", "local_shell_call"):
            a = obj.get("arguments") or obj.get("action") or {}
            if isinstance(a, str):
                try:
                    a = json.loads(a)
                except ValueError:
                    a = {}
            c = a.get("command") if isinstance(a, dict) else None
            if isinstance(c, list):
                c = " ".join(c[2:] if c[:2] in (["bash", "-lc"], ["sh", "-c"]) else c)
            if isinstance(c, str):
                out.append(c)
            return
        for v in obj.values():
            commands_of(v, out)
    elif isinstance(obj, list):
        for v in obj:
            commands_of(v, out)


def norm(cmd):
    """Reduce one command line to its verbs: 'gh api repos/x/y/pulls/3 --jq ..' -> 'gh api'."""
    parts = []
    for seg in re.split(r"\s*(?:&&|\|\||;|\|)\s*", cmd.strip()):
        try:
            toks = shlex.split(seg, comments=True)
        except ValueError:
            toks = seg.split()
        toks = [t for t in toks if "=" not in t.split("/")[0] or t.startswith("-")]  # drop VAR=x prefixes
        if not toks:
            continue
        head = os.path.basename(toks[0]) if toks[0].startswith("/") else toks[0]
        head = head.lstrip("(")
        verb = head
        rest = toks[1:]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in OPT_WITH_ARG else rest[1:]
        if head in SUBCMD and rest:
            nxt = rest[0]
            if head in ("python3", "python", "node", "bash", "sh") and not nxt.startswith("-"):
                nxt = os.path.basename(nxt)
            if not nxt.startswith("-"):
                verb = head + " " + re.sub(r"\d+", "N", nxt)
        if verb in NOISE or head in NOISE:
            continue
        parts.append(verb)
    return " && ".join(parts)


def sessions(roots, since):
    for root in roots:
        root = os.path.expanduser(root)
        for d, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith(".jsonl"):
                    continue
                p = os.path.join(d, fn)
                cmds, first = [], None
                with open(p, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                        except ValueError:
                            continue
                        ts = rec.get("timestamp") if isinstance(rec, dict) else None
                        if ts and not first:
                            first = ts[:10]
                        commands_of(rec, cmds)
                if since and first and first < since:
                    continue
                seq = [n for n in (norm(c) for c in cmds) if n]
                if seq:
                    yield p, first or "?", seq


def scan(roots, since=None, min_sessions=2, nmin=2, nmax=5):
    seen = collections.defaultdict(set)
    example = {}
    for p, day, seq in sessions(roots, since):
        for n in range(nmin, nmax + 1):
            for i in range(len(seq) - n + 1):
                g = tuple(seq[i:i + n])
                if len(set(g)) < 2:
                    continue
                seen[g].add(p)
                example.setdefault(g, (p, day))
    hits = [(g, s) for g, s in seen.items() if len(s) >= min_sessions]
    # keep the longest sequences: drop a gram contained in a longer one seen in as many sessions
    hits.sort(key=lambda x: (-len(x[1]), -len(x[0]), x[0]))
    kept = []
    for g, s in hits:
        if any(len(s) <= len(s2) and _contains(g2, g) for g2, s2 in kept):
            continue
        kept.append((g, s))
    return [{"sequence": list(g), "sessions": len(s), "example": example[g][0], "first_seen": example[g][1]} for g, s in kept]


def _contains(big, small):
    n = len(small)
    return len(big) > n and any(big[i:i + n] == small for i in range(len(big) - n + 1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("roots", nargs="*", default=["~/.claude/projects", "~/.codex/sessions"])
    ap.add_argument("--since")
    ap.add_argument("--min-sessions", type=int, default=2)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = scan(a.roots, a.since, a.min_sessions)[: a.top]
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    if not res:
        print("no repeated sequence across %d+ sessions" % a.min_sessions)
        return 0
    print("| sessions | repeated sequence | first seen |\n|---|---|---|")
    for r in res:
        print("| %d | `%s` | %s |" % (r["sessions"], " -> ".join(r["sequence"]), r["first_seen"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
