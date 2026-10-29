#!/usr/bin/env python3
"""Helpers for profile SVGs: text as paths (fontTools), isometric projection, polygons, boxes.

Import from your generator:  sys.path.insert(0, "<skill>/scripts"); from svgkit import Fonts, iso, box
Self-test (no font needed):  python3 svgkit.py --selftest
Needs `pip install fonttools` only for Fonts/text_path.
"""
import math
import sys


class Fonts(object):
    """Load .ttf files once: Fonts({"bold": "fonts/X-Bold.ttf"}).path("Hi", "bold", 48, 60, 120)."""

    def __init__(self, files):
        from fontTools.ttLib import TTFont  # imported here so the rest works without fonttools
        self.fonts = {k: TTFont(v) for k, v in files.items()}

    def path(self, txt, font, size, x, y, tracking=0.0):
        """SVG path 'd' for txt with its baseline at (x, y), and the advance width in px."""
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        f = self.fonts[font]
        gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
        s, pen, cx = size / upm, SVGPathPen(gs), 0.0
        for ch in txt:
            g = cmap.get(ord(ch))
            if g is None:
                cx += size * 0.3
                continue
            gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + cx, y)))
            cx += gs[g].width * s + tracking
        return pen.getCommands(), cx - tracking


def iso(x, y, z=0, ox=930, oy=246, k=26):
    """Isometric projection of grid units to pixels: x' = (x-y)cos30, y' = (x+y)sin30 - z."""
    return (ox + (x - y) * k * math.cos(math.radians(30)), oy + (x + y) * k * math.sin(math.radians(30)) - z * k)


def poly(points, fill, extra=""):
    return '<polygon points="%s" fill="%s" %s/>' % (" ".join("%.1f,%.1f" % p for p in points), fill, extra)


def box(x, y, z, dx, dy, dz, top, left, right, extra="", **proj):
    """An isometric cuboid as three polygons (left, right, top), drawn back to front."""
    def p(a, b, c):
        return iso(x + a, y + b, z + c, **proj)
    t = poly([p(0, 0, dz), p(dx, 0, dz), p(dx, dy, dz), p(0, dy, dz)], top, extra)
    l = poly([p(0, dy, 0), p(dx, dy, 0), p(dx, dy, dz), p(0, dy, dz)], left, extra)
    r = poly([p(dx, 0, 0), p(dx, dy, 0), p(dx, dy, dz), p(dx, 0, dz)], right, extra)
    return l + r + t


def keyframes(name, stops):
    """Explicit @keyframes (no CSS variables inside keyframes: Safari/Camo ignore them)."""
    body = " ".join("%s{%s}" % (k, v) for k, v in stops)
    return "@keyframes %s{%s}" % (name, body)


REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def _selftest():
    x, y = iso(0, 0)
    assert (round(x), round(y)) == (930, 246)
    x1, _ = iso(1, 0)
    assert round(x1 - 930, 2) == round(26 * math.cos(math.radians(30)), 2)
    svg = box(0, 0, 0, 1, 1, 1, "#aaa", "#888", "#666")
    assert svg.count("<polygon") == 3
    assert keyframes("spin", [("0%", "opacity:0"), ("100%", "opacity:1")]).startswith("@keyframes spin{0%{")
    print("svgkit selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        print(__doc__)
