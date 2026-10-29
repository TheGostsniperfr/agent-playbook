#!/usr/bin/env python3
"""Inline assets/style.css into a page: replaces the marker /* @artifact-style */.

Usage: inline.py page.html [-o out.html]   (default: rewrite page.html in place)
Python 3 standard library only.
"""
import argparse
import os
import sys

MARKER = "/* @artifact-style */"
CSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "style.css")


def inline(html, css):
    if MARKER not in html:
        raise SystemExit("inline.py: marker %s not found" % MARKER)
    return html.replace(MARKER, css.strip())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    with open(a.page, encoding="utf-8") as f:
        html = f.read()
    with open(CSS, encoding="utf-8") as f:
        css = f.read()
    out = inline(html, css)
    with open(a.out or a.page, "w", encoding="utf-8") as f:
        f.write(out)
    print("inlined artifact-style into %s" % (a.out or a.page))
    return 0


if __name__ == "__main__":
    sys.exit(main())
