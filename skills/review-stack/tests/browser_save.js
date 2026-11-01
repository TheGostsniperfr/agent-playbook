// Headless regression test: clicking a radio must write to the db, on the stack page and on
// a chantier page. Guards the bug where render() threw (setSelectionRange on a radio) and the
// save() call after it never ran: choices looked clicked but were never stored.
// Also checks "Copy prompt for Claude Code" (localPrompt): the prompt carries the owner's choices,
// skips Done / "Let agents..." decisions, and a refused clipboard shows a selectable textarea.
// Usage: node browser_save.js <stack.html> <chantier.html> [<chantier-with-owner-steps.html>]
const { chromium } = require("playwright");
const path = require("path");

// Stand-in for window.claude.use("db"): records every write in window.__writes.
// Options: failWrites (every write rejects), snapEvery (ms: re-deliver unchanged snapshots, like
// the live db does), writeDelay (ms before a write lands).
function mockDb({ seed, opts = {} }) {
  const store = JSON.parse(JSON.stringify(seed));
  const subs = [];
  window.__writes = [];
  const fire = () => subs.forEach((f) => f());
  if (opts.snapEvery) setInterval(fire, opts.snapEvery);
  const snapDoc = (p) => ({ id: p.split("/").pop(), exists: p in store, data: () => JSON.parse(JSON.stringify(store[p])) });
  const ref = (p) => ({
    set: async (d) => { if (opts.failWrites) { const e = new Error("denied"); e.code = "permission-denied"; throw e; }
      d = JSON.parse(JSON.stringify(d));
      if (opts.writeDelay) await new Promise((r) => setTimeout(r, opts.writeDelay));
      window.__writes.push([p, JSON.parse(JSON.stringify(d))]); store[p] = JSON.parse(JSON.stringify(d)); setTimeout(fire, 20); },
    onSnapshot: (cb) => { const f = () => cb(snapDoc(p)); subs.push(f); setTimeout(f, 0); return () => {}; },
  });
  const db = {
    doc: ref,
    collection: (c) => ({
      doc: (id) => ref(c + "/" + id),
      onSnapshot: (cb) => {
        const f = () => { const docs = Object.keys(store).filter((k) => k.startsWith(c + "/") && k.split("/").length === 2).map(snapDoc); cb({ docs, size: docs.length, empty: !docs.length }); };
        subs.push(f); setTimeout(f, 0); return () => {};
      },
    }),
  };
  window.claude = { use: async (n) => (n === "db" ? db : n === "user" ? { id: async () => "u-test" } : null) };
}

const STACK_SEED = {
  "chantiers/alpha": { order: 1, title: "Alpha", summary: "First card", status: "ready", decisions: [
    { id: "d1", q: "Pick one", why: "Because it matters.", options: ["Yes", "No"], default: "Yes" },
    { id: "d2", q: "Pick another", why: "Also matters.", options: ["A", "B", "C"], default: "B" }] },
  "chantiers/beta": { order: 2, title: "Beta", summary: "Second card", status: "ready", decisions: [
    { id: "d1", q: "Keep it?", why: "A real question.", options: ["Keep", "Drop"], default: "Keep" }] },
  "chantiers/gamma": { order: 3, title: "Gamma", summary: "Owner steps", status: "ready",
    links: [{ label: "Runbook", url: "https://example.com/runbook" }],
    localPrompt: { intro: "Do my part of Gamma.", language: "French",
      steps: { k1: "HOW-K1 run make rotate", k2: "HOW-K2 never shown", k3: "HOW-K3 never shown", k4: "HOW-K4 run make apply" },
      extra: ["EXTRA-1 check the dashboard"] },
    decisions: [
      { id: "k1", q: "Rotate the token?", why: "It leaked in a log.", options: ["Done", "Rotate now", "Later"], default: "Rotate now" },
      { id: "k2", q: "Update the DNS?", why: "The host moved.", options: ["Done", "Do it"], default: "Do it" },
      { id: "k3", q: "Who renames the repo?", why: "Old name is confusing.", options: ["Let agents do it", "I do it"], default: "Let agents do it" },
      { id: "k4", q: "Apply the Vault change?", why: "New policy.", options: ["Yes", "No"], default: "Yes" }] },
  "answers/beta": { verdict: "", notes: "", decisions: {}, at: "2026-10-30T10:00:00Z" },
};

const failures = [];
const check = (ok, msg) => { if (!ok) failures.push(msg); };
// A click that cannot land within 3 s (element kept moving or being rebuilt) is a failure, not a crash.
async function tap(p, sel, what) {
  try { await p.click(sel, { timeout: 3000 }); return true; }
  catch (e) { check(false, `${what}: click could not land (element kept moving or being rebuilt)`); return false; }
}

async function stack(browser, file) {
  const p = await browser.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.addInitScript(mockDb, { seed: STACK_SEED });
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector("[data-toggle]");
  for (const id of ["alpha", "beta"]) {
    if (!(await p.$(`input[type=radio][data-c="${id}"]`))) await p.click(`[data-toggle="${id}"]`);
    const decs = await p.$$eval(`input[type=radio][data-c="${id}"]`, (els) => [...new Set(els.map((e) => e.dataset.d))]);
    check(decs.length > 0, `stack ${id}: no radios rendered`);
    for (const d of decs) {
      const target = await p.$eval(`input[type=radio][data-c="${id}"][data-d="${d}"]:not(:checked)`, (e) => e.value);
      await p.click(`input[type=radio][data-c="${id}"][data-d="${d}"][value="${target}"]`);
      await p.waitForTimeout(900); // the stack debounces saves by 500 ms
      const writes = await p.evaluate(() => window.__writes);
      const last = writes.filter((w) => w[0] === "answers/" + id).pop();
      check(last && last[1].decisions && last[1].decisions[d] && last[1].decisions[d].choice === target,
        `stack ${id}.${d}: clicking "${target}" wrote nothing (writes: ${JSON.stringify(writes.map((w) => w[0]))})`);
      const shown = await p.$eval(`input[type=radio][data-c="${id}"][data-d="${d}"]:checked`, (e) => e.value).catch(() => null);
      check(shown === target, `stack ${id}.${d}: "${target}" not checked after save (shows ${shown})`);
      const status = await p.$eval(`#saved-${id}`, (e) => e.textContent).catch(() => "");
      check(/^Saved/.test(status), `stack ${id}.${d}: status says "${status}", expected "Saved"`);
    }
  }
  check(!errors.length, "stack: page errors: " + errors.join(" | "));
  await p.close();
}

// A failed write must be visible: "Not saved" on the card and in the page alert.
async function stackFailure(browser, file) {
  const p = await browser.newPage();
  await p.addInitScript(mockDb, { seed: STACK_SEED, opts: { failWrites: true } });
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector('input[type=radio][data-c="alpha"]');
  await p.click('input[type=radio][data-c="alpha"][data-d="d1"][value="No"]');
  await p.waitForTimeout(900);
  const status = await p.$eval("#saved-alpha", (e) => e.textContent).catch(() => "");
  check(/^Not saved/.test(status), `stack failure: card status says "${status}", expected "Not saved..."`);
  const alert = await p.$eval("#alert", (e) => (e.hidden ? "" : e.textContent)).catch(() => "");
  check(/Not saved/.test(alert), `stack failure: page alert not shown (got "${alert}")`);
  await p.close();
}

// Local edits win until saved. The live db re-delivers snapshots all the time, and WebKit does
// not focus a radio on click, so an "is the user editing?" focus check is not enough: a snapshot
// arriving before the debounced save used to put the OLD answer back, and the save wrote it.
async function stackRace(browser, file) {
  const p = await browser.newPage();
  await p.addInitScript(mockDb, { seed: STACK_SEED, opts: { snapEvery: 60, writeDelay: 150 } });
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector('input[type=radio][data-c="alpha"]');
  const picks = { d1: "No", d2: "C" };
  for (const [d, v] of Object.entries(picks)) {
    await tap(p, `label:has(> input[data-c="alpha"][data-d="${d}"][value="${v}"])`, `stack race alpha.${d}`);
    await p.evaluate(() => document.activeElement && document.activeElement.blur()); // behave like WebKit
    await p.waitForTimeout(80);
  }
  await p.waitForTimeout(1500);
  const writes = await p.evaluate(() => window.__writes.filter((w) => w[0] === "answers/alpha"));
  const last = writes.length ? writes[writes.length - 1][1] : {};
  for (const [d, v] of Object.entries(picks)) {
    const got = last.decisions && last.decisions[d] && last.decisions[d].choice;
    check(got === v, `stack race alpha.${d}: last write stored "${got}", expected "${v}"`);
    const shown = await p.$eval(`input[data-c="alpha"][data-d="${d}"]:checked`, (e) => e.value).catch(() => null);
    check(shown === v, `stack race alpha.${d}: shows "${shown}" after snapshots, expected "${v}"`);
  }
  await p.close();
}

// Render only on real changes, and never replay the open-card animation on a re-render: clicks
// used to land on moving, freshly rebuilt elements ("it reloads the component").
async function stackNoReplay(browser, file) {
  const p = await browser.newPage();
  await p.addInitScript(mockDb, { seed: STACK_SEED, opts: { snapEvery: 60 } });
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector('input[type=radio][data-c="alpha"]');
  await p.waitForTimeout(400); // let the first open animation finish
  await p.evaluate(() => { document.querySelector("#card-alpha .body").__mark = 1; });
  await p.waitForTimeout(600); // ~10 identical snapshots
  const kept = await p.evaluate(() => !!(document.querySelector("#card-alpha .body") || {}).__mark);
  check(kept, "stack: identical snapshots rebuilt the open card (render on every snapshot)");
  const animating = await p.$$eval(".body.opening", (els) => els.length);
  check(animating === 0, `stack: ${animating} card(s) replaying the open animation without being opened`);
  await tap(p, 'input[data-c="alpha"][data-d="d1"][value="No"]', "stack replay");
  await p.waitForTimeout(900);
  const replay = await p.$$eval(".body.opening", (els) => els.length);
  check(replay === 0, "stack: a radio click replayed the open animation");
  await tap(p, '[data-toggle="beta"]', "stack replay open beta");
  const opened = await p.$$eval("#card-beta .body.opening", (els) => els.length);
  check(opened === 1, "stack: opening a card should play its unfold animation once");
  await p.close();
}

// Same rule on a chantier page: a second click while the first save is in flight must win.
async function chantierRace(browser, file) {
  const p = await browser.newPage();
  await p.addInitScript(mockDb, { seed: {}, opts: { snapEvery: 50, writeDelay: 250 } });
  await p.goto("file://" + path.resolve(file));
  await p.waitForTimeout(200);
  const d = await p.$eval("[data-decision]", (e) => e.dataset.decision);
  const values = await p.$$eval(`[data-decision="${d}"] input[type=radio]`, (els) => els.map((e) => e.value));
  const first = values.find((v) => v !== "other") , second = values[values.length - 1];
  for (const v of [first, second]) {
    await p.click(`[data-decision="${d}"] input[type=radio][value="${v}"]`);
    await p.evaluate(() => document.activeElement && document.activeElement.blur());
    await p.waitForTimeout(100);
  }
  await p.waitForTimeout(1500);
  const writes = await p.evaluate((d) => window.__writes.filter((w) => w[0] === "answers/" + d), d);
  const got = writes.length ? writes[writes.length - 1][1].choice : null;
  check(got === second, `chantier race ${d}: last write stored "${got}", expected "${second}"`);
  const shown = await p.$eval(`[data-decision="${d}"] input[type=radio]:checked`, (e) => e.value);
  check(shown === second, `chantier race ${d}: shows "${shown}", expected "${second}"`);
  await p.close();
}

async function chantier(browser, file) {
  const p = await browser.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.addInitScript(mockDb, { seed: {} });
  await p.goto("file://" + path.resolve(file));
  await p.waitForTimeout(200);
  const decs = await p.$$eval("[data-decision]", (els) => els.map((e) => e.dataset.decision));
  check(decs.length > 0, "chantier: no decision cards rendered");
  for (const d of decs) {
    const target = await p.$eval(`[data-decision="${d}"] input[type=radio]:not(:checked)`, (e) => e.value);
    await p.click(`[data-decision="${d}"] input[type=radio][value="${target}"]`);
    await p.waitForTimeout(150);
    const writes = await p.evaluate(() => window.__writes);
    const last = writes.filter((w) => w[0] === "answers/" + d).pop();
    check(last && last[1].choice === target, `chantier ${d}: clicking "${target}" wrote nothing`);
    const status = await p.$eval(`[data-decision="${d}"] .saved`, (e) => e.textContent);
    check(/^Saved/.test(status), `chantier ${d}: status says "${status}", expected "Saved"`);
  }
  check(!errors.length, "chantier: page errors: " + errors.join(" | "));
  await p.close();
}

// Clipboard stand-in: ok -> records the text in window.__clip; refused -> writeText rejects.
function mockClipboard(mode) {
  const writeText = mode === "refused" ? async () => { throw new Error("NotAllowedError"); } : async (t) => { window.__clip = t; };
  Object.defineProperty(navigator, "clipboard", { value: mode === "missing" ? undefined : { writeText }, configurable: true });
}

async function stackCopy(browser, file, mode) {
  const p = await browser.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.addInitScript(mockDb, { seed: STACK_SEED });
  await p.addInitScript(mockClipboard, mode);
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector('[data-toggle="gamma"]');
  check(!(await p.$('[data-copy="alpha"]')) , "stack copy: a card without localPrompt shows the copy button");
  await p.click('[data-toggle="gamma"]');
  await p.click('input[data-c="gamma"][data-d="k1"][value="Other"]');
  await p.fill("#o-gamma-k1", "OTHER-TEXT use the new path");
  await p.click('input[data-c="gamma"][data-d="k2"][value="Done"]');
  await p.click('input[data-c="gamma"][data-d="k4"][value="No"]');
  await p.fill("#notes-gamma", "NOTE-1 keep it short");
  await p.click('button[data-copy="gamma"]');
  await p.waitForTimeout(100);
  const ta = await p.$eval("#cc-gamma", (e) => ({ hidden: e.hidden, value: e.value, focused: document.activeElement === e,
    selected: e.selectionEnd - e.selectionStart }));
  const text = mode === "ok" ? await p.evaluate(() => window.__clip || "") : ta.value;
  const label = await p.$eval('button[data-copy="gamma"]', (e) => e.textContent);
  const tag = `stack copy (${mode})`;
  if (mode === "ok") {
    check(/Copied/.test(label), `${tag}: button says "${label}", expected "Copied..."`);
    check(ta.hidden, `${tag}: textarea shown although the clipboard worked`);
  } else {
    check(!ta.hidden && ta.focused && ta.selected === ta.value.length && ta.value.length > 0,
      `${tag}: fallback textarea not shown, focused and selected (${JSON.stringify({ hidden: ta.hidden, focused: ta.focused, selected: ta.selected })})`);
    check(/Select all/.test(label), `${tag}: button says "${label}", expected "Select all..."`);
  }
  for (const want of ["Do my part of Gamma.", "Rotate the token? (my choice: Other: OTHER-TEXT use the new path)", "HOW-K1",
    "Apply the Vault change? (my choice: No)", "HOW-K4", "EXTRA-1", "https://example.com/runbook", "My notes: NOTE-1",
    "never force-push", "never print", "ask me before", "through Terraform", "in French"])
    check(text.includes(want), `${tag}: prompt lacks "${want}"`);
  for (const not of ["Update the DNS?", "HOW-K2", "Who renames the repo?", "HOW-K3"])
    check(!text.includes(not), `${tag}: prompt includes a Done / "Let agents" item: "${not}"`);
  check(!errors.length, `${tag}: page errors: ` + errors.join(" | "));
  await p.close();
}

async function chantierCopy(browser, file, mode) {
  const p = await browser.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.addInitScript(mockDb, { seed: {} });
  await p.addInitScript(mockClipboard, mode);
  await p.goto("file://" + path.resolve(file));
  await p.waitForSelector("#cc-copy");
  const tag = `chantier copy (${mode})`;
  const read = async () => {
    await p.click("#cc-copy"); await p.waitForTimeout(100);
    return mode === "ok" ? p.evaluate(() => window.__clip || "") : p.$eval("#cc-text", (e) => e.value);
  };
  await p.click("#d-sandbox-done");
  await p.click("#d-force-with-lease-agents");
  let text = await read();
  check(!/Sandbox on by default|force-with-lease on feature/i.test(text), `${tag}: Done / "Let agents" decisions are in the prompt`);
  check(text.includes("Install the Claude GitHub App"), `${tag}: extra owner step missing`);
  await p.click("#d-force-with-lease-block");
  await p.fill("#d-force-with-lease-text", "NOTE-FWL only on my branches");
  await p.fill("#v-note", "VNOTE-1");
  text = await read();
  for (const want of ["(my choice: Block it too; note: NOTE-FWL only on my branches)", "How: Run `grep -n force-with-lease", "My notes: VNOTE-1",
    "https://github.com/Arffornia/agent-kit/pull/2", "never force-push", "ask me before"])
    check(text.includes(want), `${tag}: prompt lacks "${want}"`);
  check(!text.includes("Sandbox on by default"), `${tag}: Done decision came back`);
  const box = await p.$eval("#cc-text", (e) => ({ hidden: e.hidden, focused: document.activeElement === e }));
  const st = await p.$eval("#cc-status", (e) => e.textContent);
  if (mode === "ok") check(box.hidden && /Copied/.test(st), `${tag}: expected "Copied" and a hidden textarea (status "${st}")`);
  else check(!box.hidden && box.focused && /Select all/.test(st), `${tag}: fallback textarea not shown and focused (status "${st}")`);
  check(!errors.length, `${tag}: page errors: ` + errors.join(" | "));
  await p.close();
}

(async () => {
  const [stackFile, chantierFile, ownerFile] = process.argv.slice(2);
  const browser = await chromium.launch();
  try {
    await stack(browser, stackFile);
    await stackFailure(browser, stackFile);
    await stackRace(browser, stackFile);
    await stackNoReplay(browser, stackFile);
    await chantierRace(browser, chantierFile);
    await chantier(browser, chantierFile);
    for (const mode of ["ok", "refused", "missing"]) {
      await stackCopy(browser, stackFile, mode);
      if (ownerFile) await chantierCopy(browser, ownerFile, mode);
    }
  } finally {
    await browser.close();
  }
  if (failures.length) { console.error(failures.join("\n")); process.exit(1); }
  console.log("ok: every radio click was saved, local edits won, no re-render replay, copy prompt right");
})().catch((e) => { console.error(String(e && e.message || e).split("\n")[0]); process.exit(2); });
