"""Headless check that every radio click is saved (stack page and chantier page).

Runs tests/browser_save.js with Node and Playwright; skipped when either is missing.
Run: python3 -m unittest discover -s skills/review-stack/tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import render  # noqa: E402


def _node_env():
    node = shutil.which("node")
    if not node:
        return None, None
    env = dict(os.environ)
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True).stdout.strip()
        env["NODE_PATH"] = os.pathsep.join(p for p in (env.get("NODE_PATH"), root) if p)
    except (OSError, subprocess.CalledProcessError):
        pass
    probe = subprocess.run([node, "-e", "require('playwright')"], env=env, capture_output=True)
    return (node, env) if probe.returncode == 0 else (None, None)


class RadioClicksAreSaved(unittest.TestCase):
    def test_every_radio_click_writes(self):
        node, env = _node_env()
        if not node:
            self.skipTest("node with the playwright package not available")
        with tempfile.TemporaryDirectory() as tmp:
            stack, chantier = os.path.join(tmp, "stack.html"), os.path.join(tmp, "chantier.html")
            render.main(["--stack", "-o", stack])
            render.main([os.path.join(SKILL, "assets", "example.chantier.json"), "-o", chantier])
            r = subprocess.run([node, os.path.join(HERE, "browser_save.js"), stack, chantier],
                               env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
