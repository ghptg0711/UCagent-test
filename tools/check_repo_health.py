"""Check Git integrity, submission cleanliness, and nested repositories."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "third_party_sources.json"


def git(*args: str, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _ignored_paths() -> set[str]:
    """Return paths that git ignores (so nested scans can skip them)."""
    result = git("ls-files", "--others", "--ignored", "--exclude-standard",
                "--directory", "--no-empty-directory", check=False)
    return {line.rstrip("/\\") for line in result.stdout.splitlines() if line.strip()}


def nested_repositories() -> set[str]:
    """Discover nested repositories while skipping git-ignored paths.

    os.walk is used (instead of pathlib rglob) because broken symlinks
    inside .venv raise OSError mid-traversal on Windows; onerror lets us
    skip those entries instead of aborting the whole scan.
    """
    repositories: set[str] = set()
    ignored = _ignored_paths()

    def _is_ignored(rel: str) -> bool:
        return rel in ignored or any(rel.startswith(ign + "/") for ign in ignored)

    for current, dirs, _files in os.walk(ROOT, onerror=lambda _e: None):
        rel_dir = os.path.relpath(current, ROOT).replace(os.sep, "/")
        if rel_dir == ".":
            rel_dir = ""
        # Prune ignored directories (e.g. .venv, build) in-place.
        dirs[:] = [
            d for d in dirs
            if not _is_ignored(f"{rel_dir}/{d}".lstrip("/"))
        ]
        if ".git" in dirs or os.path.exists(os.path.join(current, ".git")):
            if rel_dir:
                repositories.add(rel_dir)
    return repositories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="report, but do not fail on, uncommitted top-level changes",
    )
    args = parser.parse_args()

    failures: list[str] = []

    integrity = git("fsck", "--full", "--strict", check=False)
    if integrity.returncode:
        failures.append(f"Git object integrity failed:\n{integrity.stdout.strip()}")
    else:
        print("[ok] Git object database is intact")

    index = git("ls-files", "--stage").stdout.splitlines()
    gitlinks = [line for line in index if line.startswith("160000 ")]
    if gitlinks and not (ROOT / ".gitmodules").is_file():
        failures.append("gitlink entries exist, but .gitmodules is missing")
    else:
        print(f"[ok] Gitlinks are consistent ({len(gitlinks)} found)")

    manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = {entry["path"]: entry for entry in manifest_data["repositories"]}
    discovered = nested_repositories()
    unexpected = discovered - expected.keys()
    if unexpected:
        failures.append("Unregistered nested repositories: " + ", ".join(sorted(unexpected)))

    for path, entry in expected.items():
        repo = ROOT / path
        if path not in discovered:
            if not entry.get("optional", False):
                failures.append(f"Required nested repository is missing: {path}")
            else:
                print(f"[skip] Optional nested repository is absent: {path}")
            continue

        head = git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        if head != entry["commit"]:
            failures.append(f"{path}: expected {entry['commit']}, found {head}")
        status = git("status", "--porcelain", "--untracked-files=all", cwd=repo).stdout.strip()
        if status:
            failures.append(f"{path}: nested repository has uncommitted files:\n{status}")
        nested_integrity = git("fsck", "--full", "--strict", cwd=repo, check=False)
        if nested_integrity.returncode:
            failures.append(f"{path}: Git object integrity failed:\n{nested_integrity.stdout.strip()}")
        print(f"[ok] {path} is pinned at {head}")

    dirty = git("status", "--porcelain", "--untracked-files=all").stdout.strip()
    if dirty:
        message = "Top-level repository has uncommitted files:\n" + dirty
        if args.allow_dirty:
            print("[warn] " + message)
        else:
            failures.append(message)
    else:
        print("[ok] Top-level repository is clean")

    whitespace = git("diff", "--check", check=False)
    if whitespace.returncode:
        failures.append("Whitespace errors found:\n" + whitespace.stdout.strip())
    else:
        print("[ok] No whitespace errors found")

    if failures:
        print("\nRepository health check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Repository health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
