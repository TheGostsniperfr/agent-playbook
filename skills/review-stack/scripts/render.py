#!/usr/bin/env python3
"""Render a chantier review page from chantier JSON.

Usage:
  render.py chantier.json -o page.html     validate, then write the page
  render.py chantier.json --check          validate only
  render.py --stack -o stack.html          write the review-stack index page (db-driven, no data)
  render.py --lint-card card.json          lint a stack card (chantiers/<id> document) before writing it

Validates against assets/chantier.schema.json (a built-in subset of JSON Schema: type, required,
properties, additionalProperties, items, min/maxItems, min/maxLength, pattern, enum, const, $ref)
plus semantic rules (unique ids, default is one of the options). Python 3.8+ standard library only.
"""
import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
SCHEMA = os.path.join(ASSETS, "chantier.schema.json")
TEMPLATE = os.path.join(ASSETS, "template.html")
STACK = os.path.join(ASSETS, "stack.html")
STYLE = os.path.join(ASSETS, "style.css")
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}


def _resolve(schema, root):
    while "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError("only local $ref supported: %s" % ref)
        node = root
        for part in ref[2:].split("/"):
            node = node[part]
        schema = node
    return schema


def validate(value, schema, root=None, path="$"):
    root = root or schema
    schema = _resolve(schema, root)
    errs = []
    t = schema.get("type")
    if t and not isinstance(value, TYPES[t]) or (t == "integer" and isinstance(value, bool)):
        return ["%s: expected %s" % (path, t)]
    if "const" in schema and value != schema["const"]:
        errs.append("%s: must be %r" % (path, schema["const"]))
    if "enum" in schema and value not in schema["enum"]:
        errs.append("%s: must be one of %s" % (path, ", ".join(map(str, schema["enum"]))))
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errs.append("%s: too short" % path)
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append("%s: longer than %d chars" % (path, schema["maxLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append("%s: %r does not match %s" % (path, value, schema["pattern"]))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append("%s: needs at least %d item(s)" % (path, schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append("%s: at most %d item(s)" % (path, schema["maxItems"]))
        if "items" in schema:
            for i, v in enumerate(value):
                errs += validate(v, schema["items"], root, "%s[%d]" % (path, i))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                errs.append("%s: missing %s" % (path, k))
        for k, v in value.items():
            if k in props:
                errs += validate(v, props[k], root, "%s.%s" % (path, k))
            elif schema.get("additionalProperties") is False:
                errs.append("%s: unknown field %s" % (path, k))
    return errs


# Terms the owner should never meet without a plain-words explanation next to them. Extend in an
# overlay (append to references/plain-words.md and pass --glossary) rather than editing here.
JARGON = (
    "force-with-lease", "force push", "rebase", "squash", "fast-forward", "cherry-pick", "octopus",
    "oidc", "provenance", "csp", "cors", "sast", "dast", "mutation", "flaky", "quorum", "pass^k",
    "networkpolicy", "network polic", "configmap", "init container", "lockfile", "semver",
    "trusted publish", "sandbox", "stop hook", "drift", "overlay", "ablation", "wip limit",
)
EXPLAINED = re.compile(r"(\bmeans\b|\bi\.e\.|\bthat is\b|\bin plain words\b|\(|: | = | -- | \u2014 |, which\b|\bso that\b)", re.I)


def jargon(text, context):
    """Terms used in text that the context does not explain right after (within 160 chars)."""
    out = []
    low_t, low_c = text.lower(), context.lower()
    for term in JARGON:
        if term not in low_t:
            continue
        i = low_c.find(term)
        if i < 0 or not EXPLAINED.search(context[i + len(term): i + len(term) + 160]):
            out.append(term)
    return out


# Steps of a localPrompt run on the owner's machine: refuse the obviously unsafe ones.
UNSAFE = (
    (re.compile(r"\bpush\b[^\n]*(\s-f\b|--force)"), "force-push"),
    (re.compile(r"--no-verify\b"), "skipping hooks (--no-verify)"),
    (re.compile(r"-auto-approve\b"), "applying without showing the plan (-auto-approve)"),
    (re.compile(r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME)(\s|$)"), "deleting a home or root folder"),
)
SKIP_CHOICE = re.compile(r"^(done|let agents)", re.I)


def lint_local_prompt(lp, decision_ids, where, schema=None):
    """localPrompt: well formed, keyed by real decisions, concrete and safe by default."""
    if schema is None:
        with open(SCHEMA, encoding="utf-8") as f:
            schema = json.load(f)
    errs = validate(lp, schema["$defs"]["localPrompt"], schema, where)
    if errs:
        return errs
    steps = lp.get("steps") or {}
    if not steps and not lp.get("extra"):
        errs.append("%s: give at least one step or extra line" % where)
    for k, v in steps.items():
        if k not in decision_ids:
            errs.append("%s.steps.%s: not a decision id (%s)" % (where, k, ", ".join(sorted(decision_ids)) or "none"))
        if not isinstance(v, str) or len(v.strip()) < 10:
            errs.append("%s.steps.%s: say how, as a concrete command or click path" % (where, k))
    for i, text in enumerate(list(steps.values()) + list(lp.get("extra") or [])):
        for rx, what in UNSAFE:
            if isinstance(text, str) and rx.search(text):
                errs.append("%s: step %d is not safe by default (%s); make the owner choose it explicitly" % (where, i + 1, what))
    return errs


def semantic(data):
    errs = []
    ids = [d["id"] for d in data.get("decisions", [])]
    if len(ids) != len(set(ids)):
        errs.append("$.decisions: ids must be unique")
    for i, d in enumerate(data.get("decisions", [])):
        oids = [o["id"] for o in d.get("options", [])]
        if len(oids) != len(set(oids)):
            errs.append("$.decisions[%d]: option ids must be unique" % i)
        if "other" in oids:
            errs.append("$.decisions[%d]: 'other' is reserved (the page adds it)" % i)
        if d.get("default") not in oids:
            errs.append("$.decisions[%d]: default %r is not one of its options" % (i, d.get("default")))
        text = " ".join([d.get("title", ""), d.get("context", ""), d.get("why", "")] + [o.get("label", "") + " " + o.get("detail", "") for o in d.get("options", [])])
        for term in jargon(text, d.get("context", "")):
            errs.append("$.decisions[%d]: explain %r in plain words in the context (what it is, why it matters), e.g. '%s means ...'" % (i, term, term))
    owner = [m["title"] for m in data.get("merge", []) if m.get("status") == "you"] + [
        o["label"] for d in data.get("decisions", []) for o in d.get("options", []) if SKIP_CHOICE.match(o.get("label", ""))]
    if data.get("localPrompt"):
        errs += lint_local_prompt(data["localPrompt"], set(ids), "$.localPrompt")
    elif owner:
        errs.append("$.localPrompt: required, the page has owner actions (%s); ship the steps so the owner never retypes them" % owner[0])
    acc = data.get("accent")
    if acc and not data.get("title", "").endswith(acc):
        errs.append("$.accent: must be the end of the title")
    return errs


def lint_card(card):
    """A stack card (db chantiers/<id>): every inline decision must be readable cold."""
    errs = []
    for k in ("title", "summary", "status"):
        if not card.get(k):
            errs.append("card: missing %s" % k)
    if card.get("status") not in (None, "building", "ready", "done"):
        errs.append("card: status must be building, ready or done")
    for l in card.get("links") or []:
        if not str(l.get("url", "")).startswith("https://"):
            errs.append("card.links: %r is not a full https URL" % l.get("url"))
    for i, d in enumerate(card.get("decisions") or []):
        where = "card.decisions[%d]" % i
        for k in ("id", "q", "why", "options", "default"):
            if not d.get(k):
                errs.append("%s: missing %s%s" % (where, k, " (one plain line: what this is and why we ask)" if k == "why" else ""))
        if d.get("why") and len(d["why"]) < 40:
            errs.append("%s: why is too short to be read cold (40 chars minimum)" % where)
        if d.get("default") and d.get("default") not in (d.get("options") or []):
            errs.append("%s: default %r is not one of its options" % (where, d.get("default")))
        if "Other" in (d.get("options") or []):
            errs.append("%s: do not add 'Other', the page adds it" % where)
        text = " ".join([d.get("q", ""), d.get("why", "")] + list(d.get("options") or []))
        for term in jargon(text, d.get("why", "")):
            errs.append("%s: explain %r in plain words in why" % (where, term))
    decs = card.get("decisions") or []
    owner = [o for d in decs for o in (d.get("options") or []) if SKIP_CHOICE.match(str(o))]
    if card.get("localPrompt"):
        errs += lint_local_prompt(card["localPrompt"], {d.get("id") for d in decs}, "card.localPrompt")
    elif owner:
        errs.append("card: localPrompt required, the card has owner actions; ship the steps so the owner never retypes them")
    return errs


def check(data):
    with open(SCHEMA, encoding="utf-8") as f:
        schema = json.load(f)
    errs = validate(data, schema)
    return errs or semantic(data)


E = html.escape


def _links(links, cls=""):
    return " · ".join('<a%s href="%s">%s</a>' % (' class="%s"' % cls if cls else "", E(l["url"]), E(l["label"])) for l in links or [])


def body_html(d):
    out = []
    title = E(d["title"])
    if d.get("accent"):
        head = E(d["title"][: -len(d["accent"])])
        title = "%s<span>%s</span>" % (head, E(d["accent"]))
    stats = ""
    if d.get("stats"):
        stats = '<div class="stats" aria-label="At a glance">%s</div>' % "".join(
            '<div class="stat"><b>%s</b><small>%s</small></div>' % (E(s["value"]), E(s["label"])) for s in d["stats"])
    out.append('<header class="hero"><div><div class="eyebrow">%s</div><h1>%s</h1><p>%s</p></div>%s</header>' % (
        E(d.get("eyebrow") or "Chantier · review"), title, E(d["summary"]), stats))

    if d.get("parts"):
        cards = []
        for p in d["parts"]:
            cards.append('<article class="part"><header><h3>%s</h3><span class="pr">%s</span></header><ul>%s</ul>%s</article>' % (
                E(p["title"]), _links(p.get("links")), "".join("<li>%s</li>" % E(b) for b in p["bullets"]),
                '<div class="proof">%s</div>' % E(p["proof"]) if p.get("proof") else ""))
        out.append('<section><div class="section-head"><div class="eyebrow">What\'s in it</div><h2>%s</h2></div><div class="parts">%s</div></section>' % (
            "%d part%s" % (len(d["parts"]), "" if len(d["parts"]) == 1 else "s"), "".join(cards)))

    labels = {"ready": ("ok", "ready"), "draft": ("draft", "draft"), "blocked": ("blocked", "blocked"), "you": ("", "you"), "after": ("", "after")}
    items = []
    for i, m in enumerate(d["merge"], 1):
        cls, lab = labels[m["status"]]
        name = '<a href="%s">%s</a>' % (E(m["url"]), E(m["title"])) if m.get("url") else E(m["title"])
        items.append('<li><span class="n">%d</span><span class="what">%s<small>%s</small></span><span class="tag%s">%s</span></li>' % (
            i, name, E(m["summary"]), " " + cls if cls else "", E(m.get("status_label") or lab)))
    n = len(d["merge"])
    out.append('<section><div class="section-head"><div class="eyebrow">Merge order</div><h2>%s</h2><p>The orchestrator merges in this order once you approve.</p></div><ol class="merge">%s</ol></section>' % (
        "%d step%s, in order" % (n, "" if n == 1 else "s"), "".join(items)))

    decs = []
    for i, dec in enumerate(d["decisions"], 1):
        did = E(dec["id"])
        opts = []
        for o in dec["options"]:
            oid = E(o["id"])
            opts.append('<label class="choice"><input type="radio" name="d-%s" value="%s" id="d-%s-%s"%s><span>%s%s%s</span></label>' % (
                did, oid, did, oid, " checked" if o["id"] == dec["default"] else "", E(o["label"]),
                '<span class="def">default</span>' if o["id"] == dec["default"] else "",
                "<small>%s</small>" % E(o["detail"]) if o.get("detail") else ""))
        opts.append('<label class="choice"><input type="radio" name="d-%s" value="other" id="d-%s-other"><span>Other<small>Say what you want in the field below.</small></span></label>' % (did, did))
        why = '<div class="rec"><b>Why the default</b>%s</div>' % E(dec["why"]) if dec.get("why") else ""
        decs.append('<div class="dec" data-decision="%s" id="dec-%s"><h3>%d · %s</h3><p>%s%s</p><fieldset><legend>%s</legend>%s</fieldset>'
                    '<label class="field" for="d-%s-text">Other, or a note<textarea id="d-%s-text" data-text="%s" placeholder="Type or dictate"></textarea></label>%s<div class="saved" aria-live="polite"></div></div>' % (
                        did, did, i, E(dec["title"]), E(dec["context"]),
                        " " + _links(dec.get("links")) if dec.get("links") else "", E(dec["title"]), "".join(opts),
                        did, did, did, why))
    if decs:
        out.append('<section><div class="section-head"><div class="eyebrow">Your calls</div><h2>%d decision%s, each with a default</h2>'
                   '<p>Change only what you disagree with: the default is preselected and silence keeps it. Answers save as you go.</p></div>'
                   '<p class="hint"><b>Voice</b>To speak instead of typing, tap a field and use your keyboard\'s mic (iPhone, Android), Dictation on macOS (press Fn twice), or Win+H on Windows; on Linux use a dictation app. The page itself cannot use the microphone.</p>'
                   '<div class="decisions">%s</div></section>' % (len(decs), "" if len(decs) == 1 else "s", "".join(decs)))

    def gaps(items, cls):
        return "".join('<div class="gap%s"><b>%s</b><span>%s</span></div>' % (cls, E(g["title"]), E(g["detail"])) for g in items)
    out.append('<section><div class="section-head"><div class="eyebrow">Proof</div><h2>Verified, and not yet</h2></div>'
               '<div class="gaps">%s%s</div></section>' % (gaps(d["verified"], " ok"), gaps(d["not_verified"], "")))

    if d.get("localPrompt"):
        out.append('<section id="local"><div class="section-head"><div class="eyebrow">Do it locally</div><h2>Your part, as a prompt</h2>'
                   '<p>Some steps only you can do. Your local Claude Code can do them for you: the prompt carries your choices and notes, '
                   'and skips what you marked Done or left to the agents.</p></div><div class="cc">'
                   '<button class="btn primary" type="button" id="cc-copy" data-copy="chantier">Copy prompt for Claude Code</button>'
                   '<span class="saved" id="cc-status" aria-live="polite"></span>'
                   '<textarea id="cc-text" class="copybox" readonly hidden aria-label="Prompt for Claude Code"></textarea></div></section>')
    out.append('<section class="pipe" id="verdict"><div><div class="eyebrow">Verdict</div><h2>Approve the chantier</h2>'
               '<p>Approving records your answers above (defaults included) for the orchestrator, which then merges in order. '
               'Nothing merges before that.</p></div><div class="flow verdict">'
               '<div><b>Choose</b><span class="vbtns"><button class="btn primary" type="button" id="v-approve" data-status="approved">Approve</button> '
               '<button class="btn" type="button" id="v-changes" data-status="changes">Needs changes</button> '
               '<button class="btn" type="button" id="v-hold" data-status="hold">Hold</button></span></div>'
               '<div><b>Note</b><label class="field vnote" for="v-note"><span>Anything for the orchestrator (optional)</span><textarea id="v-note" placeholder="Type or dictate"></textarea></label></div>'
               '<div><b>Status</b><span><span class="saved" id="v-status" aria-live="polite">Not decided yet.</span></span></div>'
               '<div><b>No sign-in?</b><span><button class="btn" type="button" id="copy">Copy my answers</button> <span class="saved" id="copy-status"></span>'
               '<textarea id="copy-text" class="copybox" readonly hidden></textarea></span></div></div></section>')
    out.append("<footer>%s</footer>" % E(d.get("footer") or "Chantier %s, %s." % (d["id"], d["date"])))
    return "\n".join(out)


def page(d):
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    with open(STYLE, encoding="utf-8") as f:
        css = f.read().strip()
    data = json.dumps(d, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    return (tpl.replace("@@TITLE@@", E(d["title"]))
               .replace("/* @artifact-style */", css)
               .replace("@@BODY@@", body_html(d))
               .replace("@@DATA@@", data))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("chantier", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--stack", action="store_true", help="write the stack index page instead")
    ap.add_argument("--lint-card", metavar="CARD_JSON", help="lint a stack card document and exit")
    a = ap.parse_args(argv)
    if a.lint_card:
        with open(a.lint_card, encoding="utf-8") as f:
            errs = lint_card(json.load(f))
        for e in errs:
            print("error: " + e, file=sys.stderr)
        if not errs:
            print("ok: card %s" % a.lint_card)
        return 1 if errs else 0
    if a.stack:
        with open(STACK, encoding="utf-8") as f:
            tpl = f.read()
        with open(STYLE, encoding="utf-8") as f:
            out = tpl.replace("/* @artifact-style */", f.read().strip())
        with open(a.out or "stack.html", "w", encoding="utf-8") as f:
            f.write(out)
        print("wrote %s" % (a.out or "stack.html"))
        return 0
    if not a.chantier:
        ap.error("chantier.json is required")
    with open(a.chantier, encoding="utf-8") as f:
        data = json.load(f)
    errs = check(data)
    if errs:
        for e in errs:
            print("error: " + e, file=sys.stderr)
        return 1
    if a.check:
        print("ok: %s (%d merge steps, %d decisions)" % (data["id"], len(data["merge"]), len(data["decisions"])))
        return 0
    out = a.out or (data["id"] + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(data))
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
