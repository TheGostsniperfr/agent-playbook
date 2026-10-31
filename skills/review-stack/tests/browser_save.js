// Headless regression test: clicking a radio must write to the db, on the stack page and on
// a chantier page. Guards the bug where render() threw (setSelectionRange on a radio) and the
// save() call after it never ran: choices looked clicked but were never stored.
// Usage: node browser_save.js <stack.html> <chantier.html>   (needs the playwright package)
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

(async () => {
  const [stackFile, chantierFile] = process.argv.slice(2);
  const browser = await chromium.launch();
  try {
    await stack(browser, stackFile);
    await stackFailure(browser, stackFile);
    await stackRace(browser, stackFile);
    await stackNoReplay(browser, stackFile);
    await chantierRace(browser, chantierFile);
    await chantier(browser, chantierFile);
  } finally {
    await browser.close();
  }
  if (failures.length) { console.error(failures.join("\n")); process.exit(1); }
  console.log("ok: every radio click was saved, local edits won, no re-render replay");
})().catch((e) => { console.error(String(e && e.message || e).split("\n")[0]); process.exit(2); });
