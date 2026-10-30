"""Safeguard regression tests using isolated repositories and synthetic data only."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

import publication_guard as guard


PROJECT = Path(__file__).resolve().parents[1]


class PublicationGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scanner = guard.find_scanner(PROJECT)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="portfolio-guard-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Synthetic safeguard test")
        self.git("config", "user.email", "test@example.invalid")
        (self.root / ".gitleaks.toml").write_bytes((PROJECT / ".gitleaks.toml").read_bytes())
        (self.root / "README.md").write_text("Public synthetic example.\n", encoding="utf-8")
        self.policy = {"schema_version": 1, "max_file_bytes": 3_000_000,
                       "files": ["README.md", ".publication-policy.json", ".gitleaks.toml"], "reviewed_assets": {}}
        self.save_policy()
        self.git("add", "--", "README.md", ".publication-policy.json", ".gitleaks.toml")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0, "Synthetic Git fixture failed; output suppressed.")
        return result.stdout

    def save_policy(self):
        (self.root / ".publication-policy.json").write_text(json.dumps(self.policy), encoding="utf-8")

    def check(self, scope):
        output = io.StringIO()
        with patch.object(guard, "find_scanner", return_value=self.scanner), redirect_stdout(output), redirect_stderr(output):
            code = guard.main([scope, "--root", str(self.root)])
        return code, output.getvalue()

    def synthetic_credential(self):
        return "ghp_" + uuid.uuid4().hex + uuid.uuid4().hex[:4]

    def test_public_staged_files_pass(self):
        self.assertEqual(self.check("staged")[0], 0)

    def test_required_safeguards_must_be_staged_not_only_present(self):
        name = "required_safeguard.py"
        self.policy["files"].append(name)
        self.policy["required_files"] = [name]
        self.save_policy()
        self.git("add", "--", ".publication-policy.json")
        (self.root / name).write_text("# Synthetic required safeguard\n", encoding="utf-8")
        code, output = self.check("staged")
        self.assertEqual(code, 1)
        self.assertIn("REQUIRED SAFEGUARD MISSING", output)
        self.git("add", "--", name)
        self.assertEqual(self.check("staged")[0], 0)

    def test_staged_content_is_checked_even_if_worktree_is_clean(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "'\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        (self.root / "README.md").write_text("Clean working copy.\n", encoding="utf-8")
        code, output = self.check("staged")
        self.assertEqual(code, 1)
        self.assertIn("SECRET CANDIDATE", output)
        self.assertNotIn(candidate, output)
        self.assertIn("README.md", output)

    def test_unstaged_secret_does_not_change_staged_snapshot(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "'\n", encoding="utf-8")
        self.assertEqual(self.check("staged")[0], 0)
        code, output = self.check("worktree")
        self.assertEqual(code, 1)
        self.assertNotIn(candidate, output)

    def test_forced_private_file_is_rejected_and_preserved(self):
        private = self.root / "private-note.txt"
        private.write_text("Synthetic private document, no actual private content.\n", encoding="utf-8")
        self.git("add", "--", "private-note.txt")
        code, output = self.check("staged")
        self.assertEqual(code, 1)
        self.assertIn("INVENTORY REJECTED", output)
        self.assertTrue(private.exists())

    def test_private_path_types_are_never_public(self):
        for path in [".env", ".env.production", ".aws/credentials", "private/file.py", "exports/result.json",
                     "report.pdf", "input.xlsx", "dataset.csv", "backup.zip", "client.key", "../outside.py", "a\\b.py"]:
            with self.subTest(path=path):
                self.assertTrue(guard.private_path(path))

    def test_symlink_or_submodule_mode_is_rejected(self):
        blob = self.git("rev-parse", ":README.md").decode().strip()
        for mode in ["120000", "160000"]:
            output = io.StringIO()
            with redirect_stdout(output):
                ok, content = guard.audit_entries(self.root, self.policy, [("README.md", mode, blob)])
            self.assertFalse(ok)
            self.assertEqual(content, [])

    def test_changed_reviewed_asset_requires_review(self):
        name = "overview.png"
        data = b"\x89PNG\r\n\x1a\n" + b"synthetic image fixture"
        (self.root / name).write_bytes(data)
        self.policy["files"].append(name)
        self.policy["reviewed_assets"][name] = hashlib.sha256(data).hexdigest()
        self.save_policy()
        self.git("add", "--", name, ".publication-policy.json")
        self.assertEqual(self.check("staged")[0], 0)
        (self.root / name).write_bytes(data + b"changed")
        self.git("add", "--", name)
        self.assertEqual(self.check("staged")[0], 1)

    def test_missing_scanner_is_an_error(self):
        with patch.object(guard.shutil, "which", return_value=None):
            with self.assertRaises(guard.GuardError):
                guard.find_scanner(self.root)

    def test_broken_scanner_does_not_print_raw_output(self):
        marker = "synthetic-private-error-content"
        result = subprocess.CompletedProcess([], 2, marker.encode(), marker.encode())
        with patch.object(guard.subprocess, "run", return_value=result):
            with self.assertRaises(guard.GuardError) as error:
                guard.run_scanner(self.root, self.scanner, self.root)
        self.assertNotIn(marker, str(error.exception))

    def test_missing_report_does_not_pass(self):
        result = subprocess.CompletedProcess([], 0, b"", b"")
        with patch.object(guard.subprocess, "run", return_value=result):
            with self.assertRaises(guard.GuardError):
                guard.run_scanner(self.root, self.scanner, self.root)

    def test_inline_suppression_cannot_hide_secret(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "' # gitleaks:allow\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        code, output = self.check("staged")
        self.assertEqual(code, 1)
        self.assertNotIn(candidate, output)

    def test_history_finds_deleted_secret(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "'\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        self.git("commit", "--quiet", "-m", "Synthetic unsafe fixture")
        (self.root / "README.md").write_text("Public synthetic example.\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        self.git("commit", "--quiet", "-m", "Synthetic correction fixture")
        code, output = self.check("history")
        self.assertEqual(code, 1)
        self.assertIn("SECRET CANDIDATE", output)
        self.assertNotIn(candidate, output)

    def test_actual_ignore_rules_reject_private_paths(self):
        (self.root / ".gitignore").write_bytes((PROJECT / ".gitignore").read_bytes())
        paths = [".env", "input.xlsx", "reference_review/private.pdf", "exports/data.json", ".tools/gitleaks.exe",
                 "docs/screenshots/unreviewed.png", "institutional_streamlit_portfolio/app_pages/unreviewed.py"]
        result = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"], cwd=self.root,
                                input=("\n".join(paths) + "\n").encode(), capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(set(result.stdout.decode().splitlines()), set(paths))

    def test_docker_directory_exceptions_do_not_admit_unreviewed_descendants(self):
        rules = [line.strip() for line in (PROJECT / ".dockerignore").read_text().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        for index, rule in enumerate(rules):
            if rule.startswith("!") and rule.endswith("/"):
                self.assertEqual(rules[index + 1], rule[1:] + "**",
                                 "Opening a Docker directory must immediately re-exclude its descendants.")
        inventory = json.loads((PROJECT / ".publication-policy.json").read_text())["files"]
        runtime = {rule[1:] for rule in rules if rule.startswith("!") and not rule.endswith("/")}
        self.assertTrue(runtime <= set(inventory))
        self.assertNotIn("institutional_streamlit_portfolio/app_pages/*.py", runtime)

    def run_real_hook(self, name):
        (self.root / "scripts").mkdir(exist_ok=True)
        (self.root / "scripts" / "publication_guard.py").write_bytes((PROJECT / "scripts" / "publication_guard.py").read_bytes())
        self.git("config", "--local", "hooks.publicationPython", Path(sys.executable).as_posix())
        environment = os.environ.copy()
        environment["PATH"] = str(self.scanner.parent) + os.pathsep + environment.get("PATH", "")
        result = subprocess.run(["git", "-c", f"core.hooksPath={(PROJECT / '.githooks').as_posix()}",
                                 "hook", "run", name], cwd=self.root, capture_output=True, env=environment)
        return result.returncode, result.stdout + result.stderr

    def test_real_pre_commit_hook_blocks_staged_secret(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "'\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        code, output = self.run_real_hook("pre-commit")
        self.assertNotEqual(code, 0)
        self.assertIn(b"SECRET CANDIDATE", output)
        self.assertNotIn(candidate.encode(), output)

    def test_real_pre_push_hook_checks_committed_secret(self):
        candidate = self.synthetic_credential()
        (self.root / "README.md").write_text("credential = '" + candidate + "'\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        self.git("commit", "--quiet", "-m", "Synthetic hook fixture")
        code, output = self.run_real_hook("pre-push")
        self.assertNotEqual(code, 0)
        self.assertIn(b"SECRET CANDIDATE", output)
        self.assertNotIn(candidate.encode(), output)


if __name__ == "__main__":
    unittest.main()
