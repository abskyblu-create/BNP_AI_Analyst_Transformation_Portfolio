"""Offline publication inventory and Gitleaks checks; never print candidate values."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "8.30.1"
REGULAR_MODES = {"100644", "100755"}
PRIVATE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".zip", ".bak", ".log", ".sqlite", ".db"}


class GuardError(RuntimeError):
    pass


def git(root: Path, *args: str, input_data: bytes | None = None, allow_failure: bool = False) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(["git", *args], cwd=root, input=input_data, capture_output=True, env=environment)
    if result.returncode and not allow_failure:
        raise GuardError("Git could not read the required local content; check repository state and permissions.")
    return result.stdout if result.returncode == 0 else b""


def safe_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if not parts or path.startswith("/") or "\\" in path or ":" in path or any(p in {".", ".."} for p in parts):
        return False
    if PurePosixPath(path).as_posix() != path or any(c in path for c in "\n\r\0"):
        return False
    return True


def private_path(path: str) -> bool:
    parts = [p.lower() for p in PurePosixPath(path).parts]
    return (
        not safe_path(path)
        or any(p in {".git", ".aws", ".ssh", ".venv", ".runtime_venv", "__pycache__", "exports", "backups", "private", "real_data"} for p in parts)
        or any(p == ".env" or p.startswith(".env.") or p == "secrets.toml" for p in parts)
        or PurePosixPath(path).suffix.lower() in PRIVATE_SUFFIXES
    )


def load_policy(root: Path) -> dict:
    try:
        policy = json.loads((root / ".publication-policy.json").read_text(encoding="utf-8"))
        paths = policy["files"]
        assets = policy["reviewed_assets"]
        if policy["schema_version"] != 1 or not isinstance(paths, list) or len(paths) != len(set(paths)):
            raise ValueError
        if not paths or not all(isinstance(p, str) and safe_path(p) and not private_path(p) and not any(c in p for c in "*?[]") for p in paths):
            raise ValueError
        if not isinstance(assets, dict) or any(
            p not in paths or not digest or not all(isinstance(d, str) and re.fullmatch(r"[0-9a-f]{64}", d)
                                                  for d in (digest if isinstance(digest, list) else [digest]))
            for p, digest in assets.items()
        ):
            raise ValueError
        if not 1 <= policy["max_file_bytes"] <= 10_000_000:
            raise ValueError
        required = policy.get("required_files", [])
        if not isinstance(required, list) or not all(isinstance(p, str) and p in paths for p in required):
            raise ValueError
    except (KeyError, ValueError, TypeError, OSError):
        raise GuardError("Publication policy is missing or invalid; refusing to publish.") from None
    return policy


def index_entries(root: Path) -> list[tuple[str, str, str]]:
    entries = []
    for item in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not item:
            continue
        header, path = item.split(b"\t", 1)
        mode, oid, stage = header.decode("ascii").split()
        if stage != "0":
            raise GuardError("The index has unresolved merges; resolve them before publication checks.")
        entries.append((path.decode("utf-8", errors="surrogateescape"), mode, oid))
    return entries


def tree_entries(root: Path, revision: str) -> list[tuple[str, str, str]]:
    entries = []
    for item in git(root, "ls-tree", "-rz", "--full-tree", revision).split(b"\0"):
        if item:
            header, path = item.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            entries.append((path.decode("utf-8", errors="surrogateescape"), mode if kind == "blob" else "160000", oid))
    return entries


def find_scanner(root: Path) -> Path:
    candidate = root / ".tools" / ("gitleaks.exe" if os.name == "nt" else "gitleaks")
    if not candidate.is_file():
        resolved = shutil.which("gitleaks")
        if not resolved:
            raise GuardError("Gitleaks is unavailable. Run scripts/setup_safeguards.py; scanning is mandatory.")
        candidate = Path(resolved)
    try:
        result = subprocess.run([str(candidate), "version"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise GuardError("Gitleaks could not run; publication is blocked.") from None
    if result.returncode or not re.search(rb"(?<![\d.])8\.30\.1(?![\d.])", result.stdout):
        raise GuardError(f"Gitleaks version mismatch; install pinned version {VERSION}.")
    return candidate


def scanner_environment() -> dict:
    # Prevent inherited config/report variables from changing the checked rules.
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GITLEAKS_")}
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return environment


def run_scanner(root: Path, scanner: Path, snapshot: Path, *, history: bool = False) -> bool:
    config = root / ".gitleaks.toml"
    if not config.is_file():
        raise GuardError("Required Gitleaks configuration is missing.")
    with tempfile.TemporaryDirectory(prefix="portfolio-scan-") as temporary:
        folder = Path(temporary)
        report = folder / "report.json"
        ignore = folder / "empty-ignore"
        ignore.mkdir()
        command = [str(scanner), "git" if history else "dir", str(snapshot),
                   "--config", str(config), "--redact=100", "--no-banner", "--no-color",
                   "--log-level=error", "--report-format=json", "--report-path", str(report),
                   "--gitleaks-ignore-path", str(ignore), "--ignore-gitleaks-allow", "--timeout=120"]
        if history:
            command += ["--log-opts=--all --full-history"]
        try:
            result = subprocess.run(command, cwd=folder, capture_output=True, env=scanner_environment(), timeout=135)
        except (OSError, subprocess.TimeoutExpired):
            raise GuardError("Secret scanner failed or timed out; publication is blocked. Raw output is suppressed.") from None
        if result.returncode not in {0, 1}:
            raise GuardError("Secret scanner failed; publication is blocked. Raw output is suppressed.")
        try:
            findings = json.loads(report.read_text(encoding="utf-8"))
            if not isinstance(findings, list) or (result.returncode == 1 and not findings):
                raise ValueError
            for finding in findings:
                filename = str(finding["File"])
                if not history:
                    try:
                        filename = Path(filename).relative_to(snapshot).as_posix()
                    except ValueError:
                        filename = filename.replace(str(snapshot), "").lstrip("/\\")
                # Never emit Match, Secret, source lines, hashes or scanner logs.
                print(f"SECRET CANDIDATE: {json.dumps(filename)}:{int(finding['StartLine'])} | type={finding['RuleID']}")
        except (OSError, ValueError, KeyError, TypeError):
            raise GuardError("Secret scanner produced an invalid report; publication is blocked.") from None
        if result.returncode == 0 and findings:
            raise GuardError("Secret scanner status/report disagree; publication is blocked.")
        return not findings


def audit_entries(root: Path, policy: dict, entries: list[tuple[str, str, str]], *, worktree: bool = False) -> tuple[bool, list[tuple[str, bytes]]]:
    allowed = set(policy["files"])
    valid = True
    contents = []
    for path, mode, oid in entries:
        reason = None
        if path not in allowed or private_path(path):
            reason = "path is outside the reviewed publication inventory"
        if mode not in REGULAR_MODES:
            reason = "symlinks, submodules and non-regular entries are not permitted"
        if reason:
            print(f"INVENTORY REJECTED: {json.dumps(path)} | {reason}")
            valid = False
        if not safe_path(path) or mode not in REGULAR_MODES:
            continue
        if worktree:
            file = root / path
            if file.is_symlink() or not file.is_file() or root.resolve() not in file.resolve().parents:
                print(f"INVENTORY REJECTED: {json.dumps(path)} | unsafe local file")
                valid = False
                continue
            size = file.stat().st_size
        else:
            size = int(git(root, "cat-file", "-s", oid))
        if size > policy["max_file_bytes"]:
            print(f"INVENTORY REJECTED: {json.dumps(path)} | file exceeds the policy size limit")
            valid = False
            continue
        data = file.read_bytes() if worktree else git(root, "cat-file", "blob", oid)
        suffix = PurePosixPath(path).suffix.lower()
        asset = path in policy["reviewed_assets"]
        approved = policy["reviewed_assets"].get(path, [])
        approved = approved if isinstance(approved, list) else [approved]
        if asset and hashlib.sha256(data).hexdigest() not in approved:
            print(f"ASSET REVIEW REQUIRED: {json.dumps(path)} | content differs from reviewed image")
            valid = False
        elif not asset and (b"\0" in data or suffix in {".png", ".webp", ".jpg", ".jpeg", ".gif", ".svg"}):
            print(f"ASSET REVIEW REQUIRED: {json.dumps(path)} | binary or image has no review digest")
            valid = False
        contents.append((path, data))
    return valid, contents


def check_snapshot(root: Path, policy: dict, scanner: Path, scope: str) -> bool:
    if scope == "head":
        if not git(root, "rev-parse", "--verify", "HEAD", allow_failure=True):
            raise GuardError("There is no committed HEAD to check yet. Use the staged check before the first commit.")
        entries = tree_entries(root, "HEAD")
    else:
        entries = index_entries(root)
    if scope == "worktree":
        paths = {p for p, _, _ in entries if (root / p).exists()}
        paths.update(p for p in policy["files"] if (root / p).exists())
        paths.update(p.decode("utf-8", errors="surrogateescape") for p in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p)
        entries = [(path, "120000" if (root / path).is_symlink() else "100644", "") for path in sorted(paths)]
    missing = set(policy.get("required_files", [])) - {path for path, _mode, _oid in entries}
    for path in sorted(missing):
        print(f"REQUIRED SAFEGUARD MISSING: {json.dumps(path)} | include the reviewed safeguard files in the publication")
    inventory_ok, contents = audit_entries(root, policy, entries, worktree=scope == "worktree")
    inventory_ok = inventory_ok and not missing
    if not contents:
        raise GuardError("No content available for the selected scan; refusing to report a successful publication check.")
    with tempfile.TemporaryDirectory(prefix="portfolio-publication-") as temporary:
        snapshot = Path(temporary)
        for name, content in contents:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        secrets_ok = run_scanner(root, scanner, snapshot)
    print(f"Checked {len(entries)} {scope} files against inventory and offline secret rules.")
    return inventory_ok and secrets_ok


def check_history(root: Path, policy: dict, scanner: Path) -> bool:
    commits = git(root, "rev-list", "--all").splitlines()
    if not commits:
        print("No reachable commits: no committed history exists to scan.")
        return True
    ok = check_snapshot(root, policy, scanner, "head")
    seen = set()
    for commit in commits:
        entries = []
        for entry in tree_entries(root, commit.decode("ascii")):
            if entry not in seen:
                entries.append(entry)
                seen.add(entry)
        inventory_ok, _contents = audit_entries(root, policy, entries)
        ok = inventory_ok and ok
    secrets_ok = run_scanner(root, scanner, root, history=True)
    print(f"Checked {len(commits)} reachable commits, including all local refs.")
    return ok and secrets_ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", choices=["staged", "worktree", "head", "history", "ci"])
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        policy = load_policy(root)
        scanner = find_scanner(root)
        if args.scope in {"history", "ci"}:
            if args.scope == "ci" and git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
                raise GuardError("CI requires full Git history; use fetch-depth: 0 or GIT_DEPTH: 0.")
            ok = check_history(root, policy, scanner)
        else:
            ok = check_snapshot(root, policy, scanner, args.scope)
        print("PUBLICATION CHECK PASSED" if ok else "PUBLICATION BLOCKED: review the metadata-only findings above.")
        return 0 if ok else 1
    except (GuardError, OSError, ValueError) as error:
        message = str(error) if isinstance(error, GuardError) else "Cannot read or validate required content; publication is blocked."
        print(f"ERROR: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
