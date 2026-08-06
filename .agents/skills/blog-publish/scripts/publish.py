#!/usr/bin/env python3
"""
Publish the blog: detect working-tree / remote state, then build, commit and push.

Workflow:
  1. Check `git status --porcelain` (working tree dirty?) and how many commits are
     ahead of / behind the upstream branch.
  2. If the working tree is clean AND there are unpushed commits -> just push.
  3. Otherwise -> run `npm run build` first (abort on any error), stage all
     changes, commit with the provided message, then push.

Usage:
  python .agents/skills/blog-publish/scripts/publish.py --check
  python .agents/skills/blog-publish/scripts/publish.py --message "feat: ..."
  python .agents/skills/blog-publish/scripts/publish.py --message "..." --dry-run

Options:
  --check       Print the repo state and the planned action; do not modify anything.
  --message M   Commit message for the uncommitted changes (required when dirty).
  --dry-run     Print the exact commands that would run, without executing them.
  --skip-build  Skip the build step (not recommended).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def repo_state() -> dict:
    status = git("status", "--porcelain")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    upstream_res = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    ahead = behind = None
    upstream = ""
    if upstream_res.returncode == 0:
        upstream = upstream_res.stdout.strip()
        ahead = git("rev-list", "--count", "@{upstream}..HEAD").stdout.strip()
        behind = git("rev-list", "--count", "HEAD..@{upstream}").stdout.strip()
    return {
        "branch": branch.stdout.strip() or "(detached)",
        "upstream": upstream,
        "dirty": bool(status.stdout.strip()),
        "dirty_files": [l[3:] for l in status.stdout.splitlines() if l.strip()],
        "ahead": int(ahead) if ahead else 0,
        "behind": int(behind) if behind else 0,
    }


def print_state(state: dict) -> None:
    print(f"branch:   {state['branch']}")
    print(f"upstream: {state['upstream'] or '(none)'}")
    print(f"dirty:    {'yes' if state['dirty'] else 'no'}")
    print(f"ahead:    {state['ahead']} unpushed commit(s)")
    print(f"behind:   {state['behind']} unpulled commit(s)")
    if state["dirty_files"]:
        print("changed files:")
        for f in state["dirty_files"][:20]:
            print(f"  {f}")


def planned_commands(state: dict, message: str | None, skip_build: bool) -> list[str]:
    cmds: list[str] = []
    if state["dirty"]:
        if not skip_build:
            cmds.append("npm run build")
        cmds.append("git add -A")
        if message:
            cmds.append(f"git commit -m {message!r}")
        cmds.append("git push" if state["upstream"] else f"git push -u origin {state['branch']}")
    elif state["ahead"] > 0:
        cmds.append("git push" if state["upstream"] else f"git push -u origin {state['branch']}")
    else:
        cmds.append("(nothing to do: working tree clean and no unpushed commits)")
    return cmds


def run_build() -> bool:
    npm = shutil.which("npm")
    if not npm:
        print("[error] npm not found", file=sys.stderr)
        return False
    print("Running: npm run build")
    proc = subprocess.run([npm, "run", "build"], cwd=REPO_ROOT)
    if proc.returncode != 0:
        print("[error] build failed; fix the errors before publishing.", file=sys.stderr)
        return False
    print("Build succeeded.")
    return True


def main() -> int:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Publish the blog (build -> commit -> push)")
    parser.add_argument("--check", action="store_true", help="print state and planned action only")
    parser.add_argument("--message", default=None, help="commit message for uncommitted changes")
    parser.add_argument("--dry-run", action="store_true", help="print commands without running them")
    parser.add_argument("--skip-build", action="store_true", help="skip npm run build")
    args = parser.parse_args()

    state = repo_state()
    print_state(state)
    print()
    if args.check:
        print("Planned action:")
        for cmd in planned_commands(state, args.message, args.skip_build):
            print(f"  {cmd}")
        return 0

    if state["dirty"]:
        if not args.message:
            print(
                "[error] working tree is dirty; provide a commit message with --message.",
                file=sys.stderr,
            )
            return 1
        cmds = [
            ["git", "add", "-A"],
            ["git", "commit", "-m", args.message],
        ]
    elif state["ahead"] > 0:
        cmds = []
    else:
        print("Working tree is clean and everything is already pushed. Nothing to do.")
        return 0

    push_cmd = ["git", "push"] if state["upstream"] else ["git", "push", "-u", "origin", state["branch"]]

    if args.dry_run:
        if state["dirty"] and not args.skip_build:
            print("Would run: npm run build")
        for cmd in cmds:
            print("Would run:", " ".join(cmd))
        print("Would run:", " ".join(push_cmd))
        return 0

    if state["dirty"] and not args.skip_build and not run_build():
        return 1

    for cmd in cmds:
        proc = git(*cmd[1:])
        if proc.returncode != 0:
            print(f"[error] command failed: {' '.join(cmd)}", file=sys.stderr)
            print(proc.stderr.strip(), file=sys.stderr)
            return 1
        print("Ran:", " ".join(cmd))

    if state["behind"] > 0:
        print(f"[warn] local branch is {state['behind']} commit(s) behind upstream; push may be rejected.")
    proc = subprocess.run(push_cmd, cwd=REPO_ROOT)
    if proc.returncode != 0:
        print("[error] push failed (e.g. non-fast-forward). Resolve and retry.", file=sys.stderr)
        return 1
    print("Pushed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
