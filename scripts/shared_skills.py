#!/usr/bin/env python3
"""Pull shared Hermes skills safely and publish local learning as draft PRs.

Requires Python 3.10+, git, and (for publish) gh + gitleaks. Never writes to main.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_REL = Path("local/shared-skill-sync.json")
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
NODE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
SECRET_FILE_NAMES = {".env", "credentials", "credentials.json", "secrets.json"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "local"}
EXCLUDED_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pyc"}


class WorkflowError(RuntimeError):
    pass


def run(args: list[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    try:
        result = subprocess.run(
            args, cwd=cwd, check=True, text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
    except FileNotFoundError as exc:
        raise WorkflowError(f"Required command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise WorkflowError(f"Command failed ({exc.returncode}): {' '.join(args)}\n{detail}") from exc
    return result.stdout.strip() if capture else ""


def git(repo: Path, *args: str, capture: bool = False) -> str:
    return run(["git", *args], cwd=repo, capture=capture)


def ensure_repo(repo: Path) -> Path:
    repo = repo.expanduser().resolve()
    root = Path(git(repo, "rev-parse", "--show-toplevel", capture=True))
    origin = git(root, "remote", "get-url", "origin", capture=True)
    if "feihuang-hermes" not in origin:
        raise WorkflowError(f"Unexpected origin remote: {origin}")
    return root


def require_clean_main(repo: Path) -> None:
    branch = git(repo, "branch", "--show-current", capture=True)
    dirty = git(repo, "status", "--porcelain", capture=True)
    if branch != "main":
        raise WorkflowError(f"Use a dedicated clone on main; current branch is {branch!r}.")
    if dirty:
        raise WorkflowError("Repository clone has uncommitted changes. Commit or stash them before syncing.")


def update_checkout(repo: Path) -> str:
    require_clean_main(repo)
    git(repo, "fetch", "--prune", "origin", "main")
    git(repo, "pull", "--ff-only", "origin", "main")
    return git(repo, "rev-parse", "origin/main", capture=True)


def regular_files(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            raise WorkflowError(f"Symlink found in skill tree; review it manually: {path}")
        if not path.is_file():
            continue
        if path.name in SECRET_FILE_NAMES or path.name.startswith(".env"):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[rel.as_posix()] = digest
    return result


def copy_skill(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise WorkflowError(f"Skill source is not a regular directory: {source}")
    if not (source / "SKILL.md").is_file():
        raise WorkflowError(f"Missing SKILL.md: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=destination.parent))
    stage.rmdir()
    backup = destination.with_name(f".{destination.name}.backup")
    try:
        stage.mkdir()
        for path in sorted(source.rglob("*")):
            rel = path.relative_to(source)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            if path.is_symlink():
                raise WorkflowError(f"Symlink found in skill tree; review it manually: {path}")
            if path.is_dir():
                continue
            if path.name in SECRET_FILE_NAMES or path.name.startswith(".env"):
                continue
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        if backup.exists():
            shutil.rmtree(backup)
        if destination.exists():
            destination.replace(backup)
        try:
            stage.replace(destination)
        except OSError:
            if backup.exists() and not destination.exists():
                backup.replace(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def skill_name_from_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return None
    name = re.search(r"(?m)^name:\s*['\"]?([a-z0-9][a-z0-9._-]{0,63})['\"]?\s*$", match.group(1))
    return name.group(1) if name else None


def shared_skills(repo: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for skill_md in sorted((repo / "skills").rglob("SKILL.md")):
        name = skill_name_from_file(skill_md)
        if not name:
            continue
        if name in result:
            raise WorkflowError(f"Duplicate shared skill name in repository: {name}")
        result[name] = skill_md.parent
    return result


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "skills": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read sync manifest {path}: {exc}") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("skills"), dict):
        raise WorkflowError(f"Unsupported sync manifest format: {path}")
    return data


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def sync(repo: Path, hermes_home: Path) -> int:
    repo = ensure_repo(repo)
    hermes_home = hermes_home.expanduser().resolve()
    repo_commit = update_checkout(repo)
    installed_root = hermes_home / "skills"
    manifest_path = repo / MANIFEST_REL
    manifest = load_manifest(manifest_path)
    old_entries = manifest["skills"]
    new_entries = dict(old_entries)
    conflicts: list[str] = []
    kept_local: list[str] = []
    installed: list[str] = []
    updated: list[str] = []

    for name, source in shared_skills(repo).items():
        target = installed_root / name
        source_files = regular_files(source)
        current_files = regular_files(target)
        old = old_entries.get(name)
        old_files = old.get("base_files", {}) if isinstance(old, dict) else None

        if not target.exists() and old is None:
            copy_skill(source, target)
            installed.append(name)
            new_entries[name] = {"source_path": source.relative_to(repo).as_posix(), "base_files": source_files}
            continue

        if current_files == source_files:
            new_entries[name] = {"source_path": source.relative_to(repo).as_posix(), "base_files": source_files}
            continue

        if old_files is None:
            conflicts.append(f"{name}: already installed without a baseline; compare manually")
        elif current_files == old_files:
            copy_skill(source, target)
            updated.append(name)
            new_entries[name] = {"source_path": source.relative_to(repo).as_posix(), "base_files": source_files}
        elif source_files == old_files:
            kept_local.append(name)
        else:
            conflicts.append(f"{name}: local edits and upstream changes both exist; publish/reconcile before updating")

    manifest["skills"] = new_entries
    manifest["last_checked_main"] = repo_commit
    atomic_write(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"Shared skill sync checked {len(shared_skills(repo))} skill(s) at {repo_commit[:12]}.")
    if installed:
        print("Installed: " + ", ".join(installed))
    if updated:
        print("Updated: " + ", ".join(updated))
    if kept_local:
        print("Kept local edits: " + ", ".join(kept_local))
    if conflicts:
        print("Conflicts; left installed skills untouched:")
        for item in conflicts:
            print(f"  - {item}")
        return 2
    return 0


def publish(repo: Path, hermes_home: Path, name: str, node_slug: str) -> None:
    if not SKILL_NAME_RE.fullmatch(name):
        raise WorkflowError("Skill name must use lowercase letters, digits, dot, underscore, or hyphen.")
    if not NODE_SLUG_RE.fullmatch(node_slug):
        raise WorkflowError("Node slug must be a generic public label such as node-a; do not use a hostname or site name.")
    repo = ensure_repo(repo)
    hermes_home = hermes_home.expanduser().resolve()
    require_clean_main(repo)
    git(repo, "fetch", "--prune", "origin", "main")
    candidates = [
        p.parent for p in (hermes_home / "skills").rglob("SKILL.md")
        if skill_name_from_file(p) == name
    ]
    if len(candidates) != 1:
        raise WorkflowError(f"Expected exactly one local skill named {name}; found {len(candidates)}.")
    source = candidates[0]
    run(["gh", "--version"])
    run(["gitleaks", "version"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    branch = f"learn/{node_slug}/{name}-{stamp}"
    worktree = Path(tempfile.mkdtemp(prefix="hermes-skill-pr-"))
    # git worktree requires a path that does not exist.
    worktree.rmdir()
    try:
        git(repo, "worktree", "add", "--detach", str(worktree), "origin/main")
        git(worktree, "checkout", "-b", branch)
        destination = worktree / "skills" / name
        copy_skill(source, destination)
        git(worktree, "add", "--all", "--", f"skills/{name}")
        if not git(worktree, "status", "--porcelain", capture=True):
            raise WorkflowError(f"No changes to publish for {name}.")
        git(worktree, "diff", "--cached", "--check")
        run(["gitleaks", "git", "--staged", "--redact", "--no-banner"], cwd=worktree)
        git(worktree, "commit", "-m", f"skills: propose {name} learning from {node_slug}")
        git(worktree, "push", "--set-upstream", "origin", branch)
        title = f"skills: propose shared learning for {name}"
        body = (
            f"## Candidate\n\n"
            f"Proposed update to `{name}` from contributor `{node_slug}`.\n\n"
            "## Review checklist\n\n"
            "- [ ] Generalized into reusable procedure; no site or machine identifiers\n"
            "- [ ] No credentials, endpoints, tenant details, or live machine state\n"
            "- [ ] Checked for overlap and conflict with current `main`\n"
            "- [ ] Verified the procedure against the relevant node before merge\n\n"
            "This PR was opened as a draft by the shared skill publisher."
        )
        run(["gh", "pr", "create", "--draft", "--base", "main", "--head", branch,
             "--title", title, "--body", body], cwd=worktree)
        print(f"Opened draft PR: {branch}")
    finally:
        # The remote branch and PR remain; only the temporary local checkout is removed.
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=repo,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync", "publish"))
    parser.add_argument("--repo", type=Path, required=True, help="Dedicated clone of feihuang-hermes.")
    parser.add_argument("--hermes-home", type=Path, default=Path(os.environ.get("HERMES_HOME", "~/.hermes")))
    parser.add_argument("--skill", help="Skill name to publish.")
    parser.add_argument("--node-slug", default=os.environ.get("HERMES_NODE_SLUG", "node"),
                        help="Generic public contributor label; never a hostname or site name.")
    args = parser.parse_args()

    try:
        if args.command == "sync":
            return sync(args.repo, args.hermes_home)
        if not args.skill:
            raise WorkflowError("publish requires --skill <name>.")
        publish(args.repo, args.hermes_home, args.skill, args.node_slug)
        return 0
    except WorkflowError as exc:
        print(f"shared_skills: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
