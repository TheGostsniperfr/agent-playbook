#!/usr/bin/env python3
"""Lint a project STATE.md (handoff/resume skills). Python 3.8+ standard library only.

  state_lint.py STATE.md            structure, links, size, secret patterns
  state_lint.py STATE.md --live     also ask GitHub (gh api) for the state of every PR/issue link
                                    and report lines whose wording disagrees with it
Exit 1 on errors. Warnings do not fail.
"""
import json
import re
import subprocess
import sys

REQUIRED_FM = ("project", "updated")
REQUIRED_SECTIONS = ("Start here", "Rules in force", "Active chantiers", "Decisions taken", "Key links")
MAX_LINES = 400
SECRET = [
    (re.compile(r"\b(ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"\bnpm_[A-Za-z0-9]{30,}"), "npm token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS key"),
    (re.compile(r"\bsk-[A-Za-z0-9-_]{20,}"), "API key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)\b(password|passwd|secret|client_secret|api_key)\s*[:=]\s*[^\s`<]{6,}"), "credential assignment"),
    (re.compile(r"\b(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}(\.\d{1,3})?\b"), "private IP address"),
]
GH = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/(pull|issues)/(\d+)")


def lint(text):
    errs, warns = [], []
    lines = text.splitlines()
    if not text.startswith("---\n"):
        errs.append("missing front matter (--- project/updated/... ---)")
        fm = {}
    else:
        end = text.find("\n---", 4)
        fm = dict(l.split(":", 1) for l in text[4:end].splitlines() if ":" in l)
        fm = {k.strip(): v.strip() for k, v in fm.items()}
        for k in REQUIRED_FM:
            if not fm.get(k):
                errs.append("front matter: missing %s" % k)
        if fm.get("updated") and not re.match(r"^\d{4}-\d{2}-\d{2}", fm["updated"]):
            errs.append("front matter: updated must be YYYY-MM-DD")
    heads = [l[3:].strip() for l in lines if l.startswith("## ")]
    for s in REQUIRED_SECTIONS:
        if not any(h.lower().startswith(s.lower()) for h in heads):
            errs.append("missing section: ## %s" % s)
    if len(lines) > MAX_LINES:
        warns.append("%d lines: distil, move detail into linked files (target < 300)" % len(lines))
    for i, l in enumerate(lines, 1):
        for rx, what in SECRET:
            if rx.search(l):
                errs.append("line %d: looks like a %s; never put it in the state file" % (i, what))
        for m in re.finditer(r"\]\((http://[^)]+)\)|(?<![\w/])(http://\S+)", l):
            errs.append("line %d: use https links (%s)" % (i, m.group(1) or m.group(2)))
        if re.search(r"(?<![\w/:])#\d+\b", l) and "github.com" not in l and not l.lstrip().startswith("|"):
            warns.append("line %d: a bare #number; give the full URL" % i)
    return errs, warns


def live(text):
    """[(line, url, state, wording)] where the line's wording disagrees with GitHub."""
    out = []
    cache = {}
    for i, l in enumerate(text.splitlines(), 1):
        for o, r, kind, n in GH.findall(l):
            key = (o, r, n)
            if key not in cache:
                try:
                    p = subprocess.run(["gh", "api", "repos/%s/%s/%s/%s" % (o, r, "pulls" if kind == "pull" else "issues", n)],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                    d = json.loads(p.stdout.decode() or "{}")
                    st = "merged" if d.get("merged") else d.get("state", "unknown")
                except (OSError, ValueError, subprocess.SubprocessError):
                    st = "unknown"
                cache[key] = st
            st = cache[key]
            low = l.lower()
            says_open = re.search(r"\b(open|ready|draft|waiting|to merge|in review)\b", low)
            says_done = re.search(r"\b(merged|closed|done)\b", low)
            if st in ("merged", "closed") and says_open and not says_done:
                out.append((i, "https://github.com/%s/%s/%s/%s" % (o, r, kind, n), st, "line says open"))
            elif st == "open" and says_done and not says_open:
                out.append((i, "https://github.com/%s/%s/%s/%s" % (o, r, kind, n), st, "line says done"))
    return out, cache


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    with open(argv[0], encoding="utf-8") as f:
        text = f.read()
    errs, warns = lint(text)
    for e in errs:
        print("error: " + e)
    for w in warns:
        print("warn:  " + w)
    if "--live" in argv:
        diffs, seen = live(text)
        print("live: %d GitHub link(s) checked" % len(seen))
        for i, url, st, why in diffs:
            print("stale: line %d %s is %s (%s)" % (i, url, st, why))
    if not errs:
        print("ok: %s" % argv[0])
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
