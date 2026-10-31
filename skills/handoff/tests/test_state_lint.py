"""Tests for handoff/scripts/state_lint.py. Run: python3 -m unittest discover -s skills/handoff/tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import state_lint  # noqa: E402

GOOD = """---
project: demo
updated: 2026-10-31
---
# Demo state

## Start here
- Merge https://github.com/o/r/pull/1 (ready).

## Rules in force
1. Free only.

## Active chantiers
| C | Status |

## Decisions taken
| 2026-10-31 | x | y |

## Key links
- https://example.com
"""


class Lint(unittest.TestCase):
    def test_good(self):
        self.assertEqual(state_lint.lint(GOOD)[0], [])

    def test_missing_section_and_front_matter(self):
        errs, _ = state_lint.lint("# x\n## Start here\n")
        self.assertTrue(any("front matter" in e for e in errs))
        self.assertTrue(any("Key links" in e for e in errs))

    def test_secrets_and_http(self):
        bad = GOOD + "\ntoken ghp_abcdefghijklmnopqrstuvwxyz0123\nhttp://x.y/z\nserver 192.168.1.20\n"
        errs, _ = state_lint.lint(bad)
        self.assertTrue(any("GitHub token" in e for e in errs))
        self.assertTrue(any("https" in e for e in errs))
        self.assertTrue(any("private IP" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
