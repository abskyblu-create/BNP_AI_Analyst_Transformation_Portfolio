"""Install a checksum-pinned scanner and optionally enable clone-local Git hooks."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile


VERSION = "8.30.1"
ROOT = Path(__file__).resolve().parents[1]
# SHA-256 digests from the official v8.30.1 GitHub release assets.
ASSETS = {
    ("Windows", "x64"): ("windows_x64.zip", "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e"),
    ("Linux", "x64"): ("linux_x64.tar.gz", "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"),
    ("Linux", "arm64"): ("linux_arm64.tar.gz", "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080"),
    ("Darwin", "x64"): ("darwin_x64.tar.gz", "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709"),
    ("Darwin", "arm64"): ("darwin_arm64.tar.gz", "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5"),
}


def install_scanner() -> Path:
    machine = platform.machine().lower()
    architecture = "arm64" if machine in {"arm64", "aarch64"} else "x64" if machine in {"amd64", "x86_64"} else machine
    asset = ASSETS.get((platform.system(), architecture))
    if asset is None:
        raise RuntimeError("Unsupported scanner platform; install the pinned Gitleaks release manually.")
    suffix, expected = asset
    url = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/gitleaks_{VERSION}_{suffix}"
    request = urllib.request.Request(url, headers={"User-Agent": "portfolio-safeguards-installer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = response.read(50_000_001)
    if len(archive) > 50_000_000 or hashlib.sha256(archive).hexdigest() != expected:
        raise RuntimeError("Scanner archive checksum or size validation failed; nothing installed.")
    binary_name = "gitleaks.exe" if os.name == "nt" else "gitleaks"
    if suffix.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as container:
            binary = container.read(binary_name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as container:
            member = container.getmember(binary_name)
            if not member.isfile():
                raise RuntimeError("Scanner archive contains an invalid binary entry.")
            stream = container.extractfile(member)
            if stream is None:
                raise RuntimeError("Scanner binary could not be read.")
            binary = stream.read()
    destination = ROOT / ".tools" / binary_name
    destination.parent.mkdir(exist_ok=True)
    temporary = destination.with_suffix(".download")
    temporary.write_bytes(binary)
    temporary.chmod(0o755)
    temporary.replace(destination)
    print(f"Installed checksum-verified Gitleaks {VERSION} in ignored .tools/.")
    return destination


def git_error_reason(result: subprocess.CompletedProcess) -> str:
    """Translate Git failures without exposing raw configuration or stderr."""
    message = result.stderr.decode("utf-8", errors="replace").lower()
    if "permission denied" in message or "access is denied" in message or "read-only" in message:
        return "Git cannot write the repository's local configuration (.git/config). Run setup from a normal PowerShell terminal with write access to this project; the editing session may restrict this path."
    if "file exists" in message and ("lock" in message or "config" in message):
        return "Git reports an existing configuration lock. Finish any active Git operation, then inspect the lock before retrying; setup does not remove lock files."
    if "dubious ownership" in message or "unsafe repository" in message:
        return "Git refuses this repository because of its ownership. Verify the folder owner and Git's trust configuration before enabling hooks."
    if "can only be used inside" in message or "not a git repository" in message:
        return "This Git process does not recognise the project as a repository. Run --diagnose from your normal terminal; a source ZIP without .git cannot use Git hooks."
    return f"Git hook setup failed (exit {result.returncode}). Run --diagnose; raw error output is suppressed."


def run_git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], cwd=ROOT, capture_output=True)


def diagnose() -> None:
    print(f"Project folder: {ROOT}")
    print(f"Git available: {bool(shutil.which('git'))}")
    print(f"Python available: {Path(sys.executable).is_file()}")
    if not shutil.which("git"):
        return
    probe = run_git("rev-parse", "--is-inside-work-tree")
    recognised = probe.returncode == 0 and probe.stdout.strip() == b"true"
    print(f"Git recognises repository: {recognised}")
    if not recognised:
        print(git_error_reason(probe))
        return
    directory = run_git("rev-parse", "--absolute-git-dir")
    if directory.returncode:
        print(git_error_reason(directory))
        return
    metadata = Path(directory.stdout.decode("utf-8").strip())
    config = metadata / "config"
    print(f"Local config exists: {config.is_file()}")
    print(f"Config lock exists: {(metadata / 'config.lock').exists()}")
    print(f"Hooks directory present: {(ROOT / '.githooks').is_dir()}")
    print("Diagnosis is read-only. A readable config file does not prove this terminal can write it.")


def enable_hooks() -> None:
    # These are clone-local settings; they never change global Git configuration.
    probe = run_git("rev-parse", "--is-inside-work-tree")
    if probe.returncode or probe.stdout.strip() != b"true":
        raise RuntimeError(git_error_reason(probe))
    for name in ("pre-commit", "pre-push"):
        (ROOT / ".githooks" / name).chmod(0o755)
    for args in (
        ["config", "--local", "hooks.publicationPython", Path(sys.executable).as_posix()],
        ["config", "--local", "core.hooksPath", ".githooks"],
    ):
        result = run_git(*args)
        if result.returncode:
            raise RuntimeError(git_error_reason(result))
    print("Enabled pre-commit and pre-push hooks for this clone using the current interpreter.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable-hooks", action="store_true")
    parser.add_argument("--hooks-only", action="store_true", help="Enable hooks without downloading the scanner again")
    parser.add_argument("--diagnose", action="store_true", help="Read-only repository and setup diagnostics; prints no credentials")
    args = parser.parse_args()
    try:
        if args.diagnose:
            diagnose()
            return 0
        if not args.hooks_only:
            install_scanner()
        if args.enable_hooks or args.hooks_only:
            enable_hooks()
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except Exception:
        # Network/configuration errors may embed credentials or proxy addresses.
        print("ERROR: safeguard setup failed. Check connectivity, platform, checksums and local permissions; no raw error data is displayed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
