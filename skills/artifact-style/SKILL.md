---
name: artifact-style
description: "Visual style for HTML pages and artifacts in Brian's Agent Kit v2 look: industrial production-line theme (Chakra Petch display, Archivo body, JetBrains Mono data), orange/teal/slate on cool greys, light and dark. Use when building any HTML page, artifact, review page, report or dashboard for Brian or his projects, or when asked for the Agent Kit v2 style. Gives tokens, type pairing and ready components: hero stats, belt and stations, part cards, dark pipeline band, merge list, decision cards, gaps."
metadata:
  version: "1.0.0"
  author: "Brian Perret"
---

# Artifact style (Agent Kit v2)

A page reads like a production line: top to bottom, each section a station. Calm cool-grey
surfaces, one warm accent (orange) for what moves, teal for people and "done", slate for CI.
The canonical stylesheet is [assets/style.css](assets/style.css); the markup of every component is
in [references/components.md](references/components.md).

## Use it
1. Start the page with the frame from `references/components.md` (title, viewport-fit meta,
   Google Fonts link, `<style>/* @artifact-style */</style>`, `<div class="wrap">`).
2. Pick the sections the content needs, in this order when present: hero, stations, parts, dark
   band, merge list, decisions, gaps, footer. Skip what the content does not have.
3. Inline the CSS: `python3 scripts/inline.py page.html` (relative to this skill's folder), or paste
   `assets/style.css` into the `<style>` by hand. Delete rules for components you did not use when
   the page must stay small.
4. Check light and dark (OS setting and `data-theme`), and a 400 px wide viewport.

## Tokens
- Colour roles: `--bg` page, `--panel` cards, `--sunk` inset areas, `--line` borders, `--ink`
  text, `--muted` secondary text, `--orange`/`--orange-ink` accent and links, `--teal` human and
  ok, `--slate` CI, `--red` blocked, `--belt*` the dark band (same in both themes).
- Every token is defined on bare `:root` (light), redefined under `prefers-color-scheme: dark`
  guarded by `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`.
  Never put a literal colour in a component rule.
- Type: `--f-display` Chakra Petch 600/700 for h1, stat numbers, eyebrows, merge numbers only;
  `--f-body` Archivo (variable width: h2 at `font-stretch:112%`, weight 750); `--f-mono`
  JetBrains Mono for hooks, tags, PR refs, labels. Scale: 72/30/19/17/16/14.5/13 px.
- Layout: `.wrap` max 1080 px, sections spaced by the wrapper's gap (56 px); grids of 2-4 columns
  collapse to 1 under 860 px; side gutter `max(16px, env(safe-area-inset-*))` on `body`.

## Rules that keep the look
- One dark band per page at most; it is the page's single bold moment.
- Numbers (merge list, decision numbers) only where order or reference matters.
- Stations only for a real sequence, with the legend for node colours.
- Eyebrow = a short uppercase label with the orange square; one per section head.
- Cards (`.part`, `.dec`, `.station`) share radius 10 px and 1 px `--line` border; no shadows.
- Motion: only the belt animation, disabled under `prefers-reduced-motion`.
- Copy: plain, active, specific. Every PR or page mentioned is a full link with a one-line summary.

## Gotchas
- Artifacts allow stylesheets only from Google Fonts: keep the CSS inline.
- `:has()` styles the checked choice; older browsers just lose the highlight.
- The belt's dashed line hides under 860 px; stations then stack in two columns, then one.
