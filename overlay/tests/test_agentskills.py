"""Tests for overlay/agentskills. Run: python3 -m unittest discover -s overlay/tests -v"""
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.dirname(HERE)
REPO = os.path.dirname(OVERLAY)
TOOL = os.path.join(OVERLAY, "agentskills")
SAMPLE = os.path.join(OVERLAY, "examples", "sample-project")
ORG = os.path.join(OVERLAY, "examples", "org-layer")

_loader = importlib.machinery.SourceFileLoader("agentskills", TOOL)
_spec = importlib.util.spec_from_loader("agentskills", _loader)
A = importlib.util.module_from_spec(_spec)
_loader.exec_module(A)


def run(*args, cwd=None, env=None):
    """Run the CLI in-process; return (exit code, stdout+stderr)."""
    out = io.StringIO()
    old_env = dict(os.environ)
    old_cwd = os.getcwd()
    try:
        if env:
            os.environ.update(env)
        if cwd:
            os.chdir(cwd)
        with redirect_stdout(out), redirect_stderr(out):
            rc = A.main(list(args))
    finally:
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)
    return rc, out.getvalue()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


class Yaml(unittest.TestCase):
    def test_subset(self):
        doc = A.yaml_load(
            "a: 1\n"
            "b: \"quoted # not a comment\"\n"
            "c: plain text # comment\n"
            "d: [x, 'y z', \"w\"]\n"
            "e: {k: v, n: 2}\n"
            "f:\n  - one\n  - name: two\n    v: ^1.0\n"
            "g: |\n  line 1\n\n  line 2\n"
            "h: >-\n  folded\n  text\n"
            "i:\n  nested: true\n  ver: 1.0\n"
            "j: it's fine\n"
            "k: wrapped plain\n  continues here\n"
        )
        self.assertEqual(doc["a"], 1)
        self.assertEqual(doc["b"], "quoted # not a comment")
        self.assertEqual(doc["c"], "plain text")
        self.assertEqual(doc["d"], ["x", "y z", "w"])
        self.assertEqual(doc["e"], {"k": "v", "n": 2})
        self.assertEqual(doc["f"], ["one", {"name": "two", "v": "^1.0"}])
        self.assertEqual(doc["g"], "line 1\n\nline 2\n")
        self.assertEqual(doc["h"], "folded text")
        self.assertEqual(doc["i"], {"nested": True, "ver": "1.0"})
        self.assertEqual(doc["j"], "it's fine")
        self.assertEqual(doc["k"], "wrapped plain continues here")

    def test_seq_at_key_indent(self):
        self.assertEqual(A.yaml_load("skills:\n- a\n- b\nx: 1\n"), {"skills": ["a", "b"], "x": 1})

    def test_matches_pyyaml_on_base_skills(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        for n in sorted(os.listdir(os.path.join(REPO, "skills"))):
            p = os.path.join(REPO, "skills", n, "SKILL.md")
            if not os.path.isfile(p):
                continue
            t = read(p)
            ref = yaml.safe_load(t[4:t.find("\n---", 4)])
            fm, _ = A.split_frontmatter(t)
            self.assertEqual(fm, ref, n)

    def test_dump_roundtrip(self):
        fm = {"name": "x", "description": "a: b # c \"q\"", "metadata": {"version": "1.0.0"}, "paths": ["a", "b"], "n": True}
        self.assertEqual(A.yaml_load(A.yaml_dump(fm)), fm)


class Semver(unittest.TestCase):
    def test_constraints(self):
        ok = [("1.2.3", "^1.0"), ("1.9.0", "^1.2"), ("0.2.5", "^0.2"), ("1.2.9", "~1.2"), ("1.2.3", "1.2"),
              ("2.0.0", ">=1.5 <3"), ("1.0.0", "*"), ("1.0.0", None)]
        bad = [("2.0.0", "^1.0"), ("0.3.0", "^0.2"), ("1.3.0", "~1.2"), ("1.3.0", "1.2"), ("3.0.0", ">=1.5 <3")]
        for v, c in ok:
            self.assertTrue(A.satisfies(v, c), (v, c))
        for v, c in bad:
            self.assertFalse(A.satisfies(v, c), (v, c))


BODY = "# T\n\nIntro.\n\n## Steps\n\n1. one\n\n```md\n## Not a heading\n```\n\n### Sub\n\nsub text\n\n## Rules\n\n- r1\n"


def skill(body=BODY):
    return A.Skill("t", "/nonexistent", {"name": "t", "description": "d"}, body, {}, "base")


class Patches(unittest.TestCase):
    def test_append_section_goes_after_subsections(self):
        s = skill()
        A.apply_patch(s, {"append_section": {"heading": "Steps", "text": "2. two"}}, ".", "t")
        self.assertIn("sub text\n\n2. two\n\n## Rules", s.body)

    def test_fenced_heading_ignored(self):
        self.assertIsNone(A.find_section(BODY, "Not a heading"))

    def test_replace_and_prepend_and_remove(self):
        s = skill()
        A.apply_patch(s, {"replace_section": {"heading": "## Rules", "text": "- new"}}, ".", "t")
        self.assertTrue(s.body.endswith("## Rules\n\n- new\n"))
        A.apply_patch(s, {"prepend_section": {"heading": "Steps", "text": "0. zero"}}, ".", "t")
        self.assertIn("## Steps\n\n0. zero\n\n1. one", s.body)
        A.apply_patch(s, {"remove_section": "Sub"}, ".", "t")
        self.assertNotIn("sub text", s.body)

    def test_missing_section_fails_loudly(self):
        with self.assertRaises(A.Error):
            A.apply_patch(skill(), {"replace_section": {"heading": "Nope", "text": "x"}}, ".", "t")
        s = skill()
        A.apply_patch(s, {"append_section": {"heading": "New one", "text": "x"}}, ".", "t")
        self.assertTrue(s.body.endswith("## New one\n\nx\n"))

    def test_replace_text_count(self):
        s = skill()
        with self.assertRaises(A.Error):
            A.apply_patch(s, {"replace_text": {"old": "one", "new": "1", "count": 2}}, ".", "t")
        A.apply_patch(s, {"replace_text": {"old": "r1", "new": "rule one"}}, ".", "t")
        self.assertIn("- rule one", s.body)

    def test_prepend_after_h1_and_set(self):
        s = skill()
        A.apply_patch(s, {"prepend": "Read me first."}, ".", "t")
        self.assertTrue(s.body.startswith("# T\n\nRead me first.\n\nIntro."))
        A.apply_patch(s, {"set": {"metadata": {"team": "core"}, "allowed-tools": "Read"}}, ".", "t")
        self.assertEqual(s.fm["metadata"], {"team": "core"})

    def test_add_files_cannot_escape(self):
        with self.assertRaises(A.Error):
            A.apply_patch(skill(), {"add_files": {"../x": "y"}}, ".", "t")

    def test_unknown_patch(self):
        with self.assertRaises(A.Error):
            A.apply_patch(skill(), {"frobnicate": 1}, ".", "t")


class Project(unittest.TestCase):
    """End to end on a copy of overlay/examples (base = this repository's skills/)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proj = os.path.join(self.tmp, "sample-project")
        shutil.copytree(SAMPLE, self.proj, ignore=shutil.ignore_patterns(".claude", ".opencode", "skills", "agentskills.lock"))
        shutil.copytree(ORG, os.path.join(self.tmp, "org-layer"))
        ov = os.path.join(self.proj, ".agents", "overlay.yaml")
        write(ov, read(ov).replace("path: ../../..", "path: " + REPO))
        self.env = {"AGENTSKILLS_CACHE": os.path.join(self.tmp, "cache")}
        self.env.pop("AGENTSKILLS_BASE", None)
        os.environ.pop("AGENTSKILLS_BASE", None)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def p(self, *parts):
        return os.path.join(self.proj, *parts)

    def test_render_all_targets(self):
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        for d in (".claude/skills", ".agents/skills", ".opencode/skills"):
            for n in ("review-stack", "artifact-style", "overlay-apply", "release-train"):
                self.assertTrue(os.path.isfile(self.p(d, n, "SKILL.md")), (d, n))
            self.assertFalse(os.path.exists(self.p(d, "review-stack", "variants")))
            self.assertFalse(os.path.exists(self.p(d, "review-stack", "tests")))
            self.assertFalse(os.path.exists(self.p(d, "review-stack", "CHANGELOG.md")))
            self.assertTrue(os.path.isfile(self.p(d, "review-stack", "references", "arffornia.md")))
            self.assertTrue(os.path.isfile(self.p(d, "review-stack", "references", "project.md")))
            rc, out = run("validate", "--target", "claude" if "claude" in d else "codex", self.p(d))
            self.assertEqual(rc, 0, out)
        claude = read(self.p(".claude/skills/review-stack/SKILL.md"))
        codex = read(self.p(".agents/skills/review-stack/SKILL.md"))
        self.assertIn("capabilities: {\"db\": {}", claude)            # base text
        self.assertIn("cannot publish claude.ai artifacts", codex)    # codex variant
        self.assertIn('variant: "codex"', codex)
        self.assertIn("never squash", claude)                          # org layer
        self.assertIn("tracking issue", codex)                         # project patch
        # Claude-only front matter only in the Claude render
        self.assertIn('context: "fork"', read(self.p(".claude/skills/release-train/SKILL.md")))
        self.assertNotIn("context:", read(self.p(".agents/skills/release-train/SKILL.md")))
        # scripts keep their executable bit
        self.assertTrue(os.access(self.p(".agents/skills/overlay-apply/scripts/agentskills"), os.X_OK))

    def test_deterministic_and_check(self):
        self.assertEqual(run("render", "-C", self.proj, env=self.env)[0], 0)
        lock1 = read(self.p(".agents/agentskills.lock"))
        snap1 = {d: A.read_tree(self.p(d)) for d in (".claude/skills", ".agents/skills", ".opencode/skills")}
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertIn("0 skill folder(s) changed", out)
        self.assertEqual(lock1, read(self.p(".agents/agentskills.lock")))
        self.assertEqual(snap1, {d: A.read_tree(self.p(d)) for d in snap1})
        rc, out = run("check", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        # hand edit is caught offline
        with open(self.p(".agents/skills/review-stack/SKILL.md"), "a") as f:
            f.write("\nhand edit\n")
        rc, out = run("check", "--offline", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("edited by hand: .agents/skills/review-stack", out)
        run("render", "-C", self.proj, env=self.env)
        # overlay change without render = drift
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov).replace("tracking issue", "tracking ticket"))
        rc, out = run("check", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("drift: claude review-stack", out)

    def test_settings_guard(self):
        write(self.p(".claude/settings.json"), '{\n  "permissions": {"allow": ["Bash(make check)"]}\n}\n')
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        data = json.loads(read(self.p(".claude/settings.json")))
        self.assertEqual(data["enabledPlugins"], {"playbook@skills-dir": False})
        self.assertEqual(data["permissions"], {"allow": ["Bash(make check)"]})
        self.assertEqual(run("check", "-C", self.proj, env=self.env)[0], 0)
        write(self.p(".claude/settings.json"), "{}\n")
        rc, out = run("check", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("enabledPlugins", out)
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov) + "userSkills: keep\n")
        self.assertEqual(run("check", "-C", self.proj, env=self.env)[0], 0)  # guard no longer required
        run("render", "-C", self.proj, env=self.env)
        self.assertEqual(read(self.p(".claude/settings.json")), "{}\n")

    def test_unmanaged_folder_is_protected_and_removal(self):
        write(self.p(".claude/skills/artifact-style/SKILL.md"), "---\nname: artifact-style\ndescription: mine\n---\n")
        write(self.p(".claude/skills/own-skill/SKILL.md"), "---\nname: own-skill\ndescription: mine\n---\n")
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("not managed by agentskills", out)
        rc, out = run("render", "--force", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        # drop artifact-style from both layers: its folders go, the user's own skill stays
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov) + "exclude: [artifact-style]\n")
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        self.assertFalse(os.path.exists(self.p(".claude/skills/artifact-style")))
        self.assertTrue(os.path.exists(self.p(".claude/skills/own-skill/SKILL.md")))

    def test_version_pin_and_unknown_skill(self):
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov).replace("version: ~1.1", "version: ^2.0"))
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("pins ^2.0", out)
        write(ov, read(ov).replace("version: ^2.0", "version: ~1.1").replace("- name: artifact-style\n", "- name: no-such-skill\n"))
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 1)
        self.assertIn("no-such-skill", out)

    def test_user_mode_and_dest(self):
        home = os.path.join(self.tmp, "home")
        henv = dict(self.env, HOME=home)
        rc, out = run("render", "--user", "--overlay", "none", "--base", REPO, env=henv)
        self.assertEqual(rc, 0, out)
        # Claude: a personal plugin (namespaced /playbook:review-stack), never a bare personal skill
        plug = os.path.join(home, ".claude/skills/playbook")
        self.assertTrue(os.path.isfile(os.path.join(plug, "skills/review-stack/SKILL.md")))
        self.assertEqual(json.loads(read(os.path.join(plug, ".claude-plugin/plugin.json")))["name"], "playbook")
        self.assertFalse(os.path.exists(os.path.join(home, ".claude/skills/review-stack")))
        # Codex / OpenCode: prefixed names, so a project's own review-stack never collides
        for d in (".agents/skills", ".config/opencode/skills"):
            sk = os.path.join(home, d, "playbook-review-stack", "SKILL.md")
            self.assertTrue(os.path.isfile(sk), d)
            self.assertIn('name: "playbook-review-stack"', read(sk))
        self.assertEqual(run("render", "--user", "--overlay", "none", "--base", REPO, env=henv)[1].count("rendered"), 0)
        rc, out = run("clean", "--user", "--overlay", "none", "--base", REPO, env=henv)
        self.assertFalse(os.path.exists(plug))
        self.assertFalse(os.path.exists(os.path.join(home, ".agents/skills/playbook-review-stack")))
        # opt out of the plugin and prefix: flat names
        rc, out = run("render", "--user", "--overlay", "none", "--base", REPO, "--plugin", "", "--prefix", "", env=henv)
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isfile(os.path.join(home, ".claude/skills/review-stack/SKILL.md")))
        self.assertTrue(os.path.isfile(os.path.join(home, ".agents/skills/review-stack/SKILL.md")))
        dest = os.path.join(self.tmp, "plugin", "skills")
        rc, out = run("render", "-C", self.proj, "--target", "claude", "--dest", dest, env=self.env)
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isfile(os.path.join(dest, "review-stack", "SKILL.md")))

    def test_git_base_is_locked(self):
        if not shutil.which("git"):
            self.skipTest("git missing")
        base = os.path.join(self.tmp, "base-repo")
        shutil.copytree(os.path.join(REPO, "skills"), os.path.join(base, "skills"))
        g = ["git", "-C", base, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.check_call(["git", "init", "-q", "-b", "main", base])
        subprocess.check_call(g + ["add", "-A"])
        subprocess.check_call(g + ["commit", "-qm", "v1"])
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov).replace("path: " + REPO, "git: file://" + base + "\n  ref: main"))
        self.assertEqual(run("render", "-C", self.proj, env=self.env)[0], 0)
        lock = json.loads(read(self.p(".agents/agentskills.lock")))
        c1 = lock["sources"]["base"]["commit"]
        # the base moves on; render keeps the locked commit, update moves it
        sk = os.path.join(base, "skills", "artifact-style", "SKILL.md")
        write(sk, read(sk).replace("# Artifact style (Agent Kit v2)", "# Artifact style (Agent Kit v2, edited)"))
        subprocess.check_call(g + ["commit", "-qam", "v2"])
        run("render", "-C", self.proj, env=self.env)
        self.assertNotIn("edited", read(self.p(".claude/skills/artifact-style/SKILL.md")))
        self.assertEqual(run("check", "-C", self.proj, env=self.env)[0], 0)
        rc, out = run("update", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        self.assertIn("edited", read(self.p(".claude/skills/artifact-style/SKILL.md")))
        self.assertNotEqual(json.loads(read(self.p(".agents/agentskills.lock")))["sources"]["base"]["commit"], c1)

    def test_three_levels_from_git(self):
        """Personal base (git) -> org layer (its own git repo) -> project: all three end up in the render."""
        if not shutil.which("git"):
            self.skipTest("git missing")
        def repo(path):
            g = ["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.check_call(["git", "init", "-q", "-b", "main", path])
            subprocess.check_call(g + ["add", "-A"])
            subprocess.check_call(g + ["commit", "-qm", "v1"])
        base = os.path.join(self.tmp, "base-repo")
        shutil.copytree(os.path.join(REPO, "skills"), os.path.join(base, "skills"))
        repo(base)
        org = os.path.join(self.tmp, "org-layer")
        repo(org)
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov).replace("path: " + REPO, "git: file://" + base + "\n  ref: main")
              .replace("  - path: ../org-layer\n", "  - git: file://" + org + "\n    ref: main\n"))
        rc, out = run("render", "-C", self.proj, env=self.env)
        self.assertEqual(rc, 0, out)
        lock = json.loads(read(self.p(".agents/agentskills.lock")))
        self.assertEqual(sorted(lock["sources"]), ["base", "extends:arffornia"])
        self.assertTrue(lock["sources"]["extends:arffornia"]["commit"])
        sk = read(self.p(".claude/skills/review-stack/SKILL.md"))
        self.assertIn("capabilities", sk)              # level 1: personal base
        self.assertIn("never squash", sk)              # level 2: org layer
        self.assertIn("tracking issue", sk)            # level 3: project
        self.assertEqual(run("check", "-C", self.proj, env=self.env)[0], 0)

    def test_export_and_diff(self):
        a, b = os.path.join(self.tmp, "exp-a"), os.path.join(self.tmp, "exp-b")
        rc, out = run("export", "-C", self.proj, "--out", a, env=self.env)
        self.assertEqual(rc, 0, out)
        for t in ("claude", "codex", "opencode"):
            self.assertTrue(os.path.isfile(os.path.join(a, t, "review-stack", "SKILL.md")))
        self.assertIn("extends:arffornia", read(os.path.join(a, "BUILD.json")))
        # export does not touch the project's own folders
        self.assertFalse(os.path.exists(self.p(".claude/skills")))
        run("export", "-C", self.proj, "--out", b, env=self.env)
        rc, out = run("diff", a, b, "--exit-code")
        self.assertEqual(rc, 0, out)
        self.assertIn("no change", out)
        org = os.path.join(self.tmp, "org-layer", "overlay", "arffornia.yaml")
        write(org, read(org).replace("never squash", "never squash or rebase"))
        run("export", "-C", self.proj, "--out", b, env=self.env)
        rc, out = run("diff", a, b, "--exit-code")
        self.assertEqual(rc, 1)
        self.assertIn("changed  claude/review-stack", out)
        self.assertIn("+- Arffornia: the orchestrator merges", out)
        rc, out = run("diff", a, b, "--markdown")
        self.assertIn("| changed | `codex/review-stack` |", out)
        self.assertIn("```diff", out)
        # refuses to wipe a folder that is not an export
        write(os.path.join(self.tmp, "notexp", "keep.txt"), "x")
        rc, out = run("export", "-C", self.proj, "--out", os.path.join(self.tmp, "notexp"), env=self.env)
        self.assertEqual(rc, 1)

    def test_preview_against_git_ref(self):
        if not shutil.which("git"):
            self.skipTest("git missing")
        g = ["git", "-C", self.tmp, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.check_call(["git", "init", "-q", "-b", "main", self.tmp])
        ov = self.p(".agents", "overlay.yaml")
        write(ov, read(ov).replace("path: ../org-layer", "path: ../org-layer"))
        subprocess.check_call(g + ["add", "-A"])
        subprocess.check_call(g + ["commit", "-qm", "v1"])
        rc, out = run("preview", "-C", self.proj, "--against", "HEAD", env=self.env)
        self.assertEqual(rc, 0, out)
        self.assertIn("no change", out)
        write(ov, read(ov).replace("tracking issue", "tracking ticket"))
        keep = os.path.join(self.tmp, "kept")
        rc, out = run("preview", "-C", self.proj, "--against", "HEAD", "--markdown", "--keep", keep, env=self.env)
        self.assertEqual(rc, 0, out)
        self.assertIn("| changed | `claude/review-stack` |", out)
        self.assertIn("+8. Also post the page link in the chantier's tracking ticket.", out)
        self.assertTrue(os.path.isfile(os.path.join(keep, "BUILD.json")))

    def test_init(self):
        d = os.path.join(self.tmp, "fresh")
        os.makedirs(d)
        rc, out = run("init", "-C", d, "--skills", "review-stack", "--git", "file:///x")
        self.assertEqual(rc, 0, out)
        data = A.yaml_load(read(os.path.join(d, ".agents", "overlay.yaml")))
        self.assertEqual(data["skills"], [{"name": "review-stack"}])
        self.assertEqual(data["base"]["git"], "file:///x")


class Repo(unittest.TestCase):
    def test_base_skills_valid(self):
        rc, out = run("validate", os.path.join(REPO, "skills"))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("warn", out)

    def test_overlay_apply_ships_this_resolver(self):
        self.assertEqual(read(TOOL), read(os.path.join(REPO, "skills", "overlay-apply", "scripts", "agentskills")),
                         "copy overlay/agentskills to skills/overlay-apply/scripts/agentskills")

    def test_shared_copies_are_identical(self):
        for a, b in (("handoff/references/state-format.md", "resume/references/state-format.md"),
                     ("handoff/scripts/state_lint.py", "resume/scripts/state_lint.py")):
            self.assertEqual(read(os.path.join(REPO, "skills", a)), read(os.path.join(REPO, "skills", b)), "copy %s to %s" % (a, b))

    def test_runs_as_script(self):
        out = subprocess.run([sys.executable, TOOL, "--version"], stdout=subprocess.PIPE).stdout.decode()
        self.assertIn("agentskills " + A.VERSION, out)


if __name__ == "__main__":
    unittest.main()
