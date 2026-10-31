"""Tests for review-stack's render.py. Run: python3 -m unittest discover -s skills/review-stack/tests"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import render  # noqa: E402

with open(os.path.join(SKILL, "assets", "example.chantier.json"), encoding="utf-8") as f:
    EXAMPLE = json.load(f)


class Validate(unittest.TestCase):
    def test_example_is_valid(self):
        self.assertEqual(render.check(EXAMPLE), [])

    def test_default_must_be_an_option(self):
        d = copy.deepcopy(EXAMPLE)
        d["decisions"][0]["default"] = "nope"
        self.assertTrue(any("default" in e for e in render.check(d)))

    def test_other_is_reserved(self):
        d = copy.deepcopy(EXAMPLE)
        d["decisions"][0]["options"].append({"id": "other", "label": "x"})
        self.assertTrue(any("reserved" in e for e in render.check(d)))

    def test_unknown_field_and_http_url(self):
        d = copy.deepcopy(EXAMPLE)
        d["oops"] = 1
        d["merge"][0]["url"] = "http://example.com"
        errs = render.check(d)
        self.assertTrue(any("unknown field oops" in e for e in errs))
        self.assertTrue(any("merge[0].url" in e for e in errs))

    def test_missing_required(self):
        d = copy.deepcopy(EXAMPLE)
        del d["not_verified"]
        self.assertTrue(any("missing not_verified" in e for e in render.check(d)))


class Page(unittest.TestCase):
    def test_page_escapes_and_embeds(self):
        d = copy.deepcopy(EXAMPLE)
        d["summary"] = "a <b> & </script> c"
        html = render.page(d)
        self.assertIn("a &lt;b&gt; &amp; &lt;/script&gt; c", html)
        data = re.search(r'<script type="application/json" id="chantier-data">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(data)["summary"], d["summary"])
        self.assertNotIn("@@", html)
        self.assertNotIn("/* @artifact-style */", html)
        self.assertIn('value="on" id="d-sandbox-on" checked', html)
        self.assertIn("Win+H", html)

    def test_style_copy_matches_artifact_style(self):
        mine = os.path.join(SKILL, "assets", "style.css")
        base = os.path.join(SKILL, "..", "artifact-style", "assets", "style.css")
        if not os.path.isfile(base):
            self.skipTest("artifact-style not next to review-stack (rendered alone)")
        with open(mine) as a, open(base) as b:
            self.assertEqual(a.read(), b.read(), "copy skills/artifact-style/assets/style.css into review-stack/assets/")


@unittest.skipUnless(shutil.which("chromium") or shutil.which("chromium-browser"), "chromium not installed")
class Browser(unittest.TestCase):
    def test_answers_and_verdict_reach_db(self):
        tmp = tempfile.mkdtemp()
        try:
            page = os.path.join(tmp, "t.html")
            with open(os.path.join(HERE, "mock_claude.html")) as m, open(os.path.join(HERE, "drive.html")) as dr:
                with open(page, "w") as f:
                    f.write(m.read() + render.page(EXAMPLE) + dr.read())
            exe = shutil.which("chromium") or shutil.which("chromium-browser")
            out = subprocess.run([exe, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=5000",
                                  "--dump-dom", "file://" + page], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=90).stdout.decode()
            m = re.search(r'<pre id="RESULT">(.*?)</pre>', out, re.S)
            self.assertTrue(m, "page did not finish the scripted review")
            res = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))
            st = res["store"]
            self.assertEqual(st["answers/sandbox"]["choice"], "opt-in")
            self.assertEqual(st["answers/sandbox"]["by"], "u-brian")
            self.assertEqual(st["verdict/current"]["status"], "approved")
            self.assertEqual(st["verdict/current"]["answers"]["force-with-lease"]["choice"], "block")
            self.assertEqual(res["fwltext"], "prior answer")  # existing answers load back into the form
        finally:
            shutil.rmtree(tmp)



class Context(unittest.TestCase):
    """Every decision must be readable cold (Brian could not answer a bare 'force-with-lease')."""

    def test_why_is_required(self):
        d = copy.deepcopy(EXAMPLE)
        del d["decisions"][0]["why"]
        self.assertTrue(any("missing why" in e for e in render.check(d)))

    def test_unexplained_jargon_fails(self):
        d = copy.deepcopy(EXAMPLE)
        dec = [x for x in d["decisions"] if x["id"] == "force-with-lease"][0]
        dec["context"] = "Plain --force and anything aimed at main stay blocked; we propose force-with-lease on feature branches only."
        errs = render.check(d)
        self.assertTrue(any("explain 'force-with-lease'" in e for e in errs), errs)

    def test_lint_card(self):
        bad = {"title": "T", "summary": "s", "status": "ready", "links": [{"label": "x", "url": "http://x"}],
               "decisions": [{"id": "force", "q": "Force-with-lease on feature branches?", "options": ["Yes", "No", "Other"], "default": "Yes"}]}
        errs = render.lint_card(bad)
        self.assertTrue(any("missing why" in e for e in errs))
        self.assertTrue(any("Other" in e for e in errs))
        self.assertTrue(any("https" in e for e in errs))
        good = dict(bad, links=[{"label": "x", "url": "https://x"}], decisions=[{
            "id": "force", "q": "Force-with-lease on feature branches?", "options": ["Yes", "No"], "default": "Yes",
            "why": "Force-with-lease means: overwrite my own PR branch only if nobody else pushed since I looked."}])
        self.assertEqual(render.lint_card(good), [])


class Stack(unittest.TestCase):
    def test_stack_moves_to_the_next_card(self):
        with open(os.path.join(SKILL, "assets", "stack.html"), encoding="utf-8") as f:
            s = f.read()
        self.assertIn('id="card-${esc(it.id)}"', s)
        self.assertIn("scrollIntoView", s)
        self.assertIn("prefers-reduced-motion", s)
        self.assertIn("@keyframes unfold", s)
        self.assertIn("safeUrl", s)

if __name__ == "__main__":
    unittest.main()
