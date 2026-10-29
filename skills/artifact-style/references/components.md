# Components (markup)

Every class below is styled in `assets/style.css`. Copy only the blocks the page uses. Content here is
illustrative; write the real content of the page.

## Page frame
```html
<title>Agent Kit v2</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..800&family=Chakra+Petch:wght@600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>/* @artifact-style */</style>
<div class="wrap"> ...sections... </div>
```
`.wrap` is a flex column with a 56 px gap: sections never set their own margins.

## Hero with stats
Use stats only when the numbers are the point (what ships, what passed). 3 or 6 tiles fill the grid.
```html
<header class="hero">
  <div>
    <div class="eyebrow">Org · project · review</div>
    <h1>Agent Kit <span>v2</span></h1>
    <p>One or two sentences: what this is and why it matters to the reader.</p>
  </div>
  <div class="stats" aria-label="What ships">
    <div class="stat"><b>7</b><small>hooks shipped by the plugin</small></div>
  </div>
</header>
```

## Section head
```html
<div class="section-head">
  <div class="eyebrow">Merge order</div>
  <h2>Seven merges to switch it on</h2>
  <p>One line of instruction or context.</p>
</div>
```

## Belt and stations (a real sequence only)
A station per step of a process the reader follows in order. Node colour encodes who acts:
default orange = automatic, `.human` teal = a person, `.ci` slate = CI. Always add the legend.
```html
<div class="belt">
  <div class="station"><span class="node"></span><h3>Guard</h3><span class="hook">PreToolUse</span><p>What happens.</p></div>
  <div class="station human"><span class="node"></span><h3>You publish</h3><span class="hook">/publish</span><p>...</p></div>
</div>
<div class="legend"><span><i style="border-color:var(--orange)"></i>automatic</span><span><i style="border-color:var(--teal)"></i>human only</span><span><i style="border-color:var(--slate)"></i>in CI</span></div>
```

## Part cards
One card per deliverable (a PR, a module). The `.proof` line says how it was verified.
```html
<div class="parts">
  <article class="part">
    <header><h3>Core harness</h3><a class="pr" href="https://github.com/org/repo/pull/2">repo #2</a></header>
    <ul><li>What it contains.</li></ul>
    <div class="proof">Proof: 82 offline cases pass.</div>
  </article>
</div>
```

## Dark band (one per page)
The single bold moment: a pipeline, a flow, or the key mechanism.
```html
<section class="pipe">
  <div><div class="eyebrow">AI code review</div><h2>Only findings two agents agree on reach you</h2><p>Context.</p></div>
  <div class="flow">
    <div><b>Route</b><span>What this step does.</span></div>
  </div>
</section>
```

## Merge list
Numbered because order matters. Tags: `ok` (ready), `draft`, `blocked`, or plain (`you`, `after v2`).
```html
<ol class="merge">
  <li><span class="n">1</span><span class="what"><a href="https://github.com/org/repo/pull/2">repo #2 · core harness</a><small>One-line summary.</small></span><span class="tag ok">ready</span></li>
</ol>
```

## Decision cards
Read-only form: context plus the recommended default.
```html
<div class="decisions">
  <div class="dec"><h3>1 · Sandbox on by default</h3><p>Options and trade-off.</p><div class="rec"><b>Default</b>Keep it on.</div></div>
</div>
```
Answerable form (used by the `review-stack` skill): radio options, the default marked, an "Other"
free-text field, a save status line.
```html
<div class="dec" id="dec-sandbox">
  <h3>1 · Sandbox on by default</h3><p>Context.</p>
  <fieldset><legend>Sandbox on by default</legend>
    <label class="choice"><input type="radio" name="d-sandbox" value="on" id="d-sandbox-on"><span>Keep it on<span class="def">default</span><small>Why.</small></span></label>
    <label class="choice"><input type="radio" name="d-sandbox" value="other" id="d-sandbox-other"><span>Other</span></label>
  </fieldset>
  <label class="field" for="d-sandbox-text">Other, or a note<textarea id="d-sandbox-text" placeholder="Type or dictate"></textarea></label>
  <div class="saved" aria-live="polite"></div>
</div>
```

## Gaps
`.gap.ok` (teal) for verified, plain for not verified. Three per row.
```html
<div class="gaps">
  <div class="gap ok"><b>Offline hooks</b><span>82 cases, 0 failing.</span></div>
  <div class="gap"><b>macOS</b><span>Nothing ran on a Mac.</span></div>
</div>
```

## Footer
Sources, date, who built it. `<footer>` inside `.wrap`.
