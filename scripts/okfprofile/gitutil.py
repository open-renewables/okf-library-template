"""The few git operations the command line needs (SDD W-04): changed paths, a base commit's files, tooling export.

This is not a platform adapter: it reads the local repository only and never calls a hosting platform.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import Path

TOOLING_EXPORT = ("scripts", "profile", "pyproject.toml", "uv.lock", ".python-version")


class GitError(Exception):
    """A git command failed or git is not available."""


def git(root: Path, *args: str) -> str:
    """Run ``git -C root <args>`` and return its standard output.

    Args:
        root: Repository root.
        *args: Arguments to git.

    Returns:
        Standard output, decoded as UTF-8.

    Raises:
        GitError: If git cannot be run or exits non-zero.
    """
    try:
        done = subprocess.run(  # noqa: S603 - arguments are fixed git subcommands and refs given by the user
            ["git", "-C", str(root), *args],  # noqa: S607 - git is found on PATH by design
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        msg = f"cannot run git: {exc}"
        raise GitError(msg) from exc
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", errors="replace").strip()
        msg = f"git {' '.join(args)} failed: {detail}"
        raise GitError(msg)
    return done.stdout.decode("utf-8", errors="replace")


def merge_base(root: Path, ref: str) -> str:
    """The commit where ``HEAD`` left ``ref``."""
    return git(root, "merge-base", ref, "HEAD").strip()


def changed_paths(root: Path, base_commit: str) -> list[str]:
    """Files that differ from ``base_commit`` in the working tree, plus untracked files, sorted, forward slashes."""
    tracked = git(root, "diff", "--name-only", "--no-renames", base_commit).splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({p for p in [*tracked, *untracked] if p})


def uncommitted_paths(root: Path) -> list[str]:
    """Files changed since ``HEAD`` (staged, unstaged and untracked), sorted."""
    return changed_paths(root, "HEAD")


def exists_at(root: Path, commit: str, path: str) -> bool:
    """True if ``path`` exists in the tree of ``commit``."""
    try:
        git(root, "cat-file", "-e", f"{commit}:{path}")
    except GitError:
        return False
    return True


def export_paths(root: Path, commit: str, paths: list[str], dest: Path) -> list[str]:
    """Extract files and folders of a commit into ``dest``.

    Args:
        root: Repository root.
        commit: Commit or ref to read.
        paths: Paths to extract; those missing from the commit are skipped.
        dest: Existing folder to extract into.

    Returns:
        The paths that were extracted.
    """
    present = [p for p in paths if exists_at(root, commit, p)]
    if not present:
        return []
    try:
        done = subprocess.run(  # noqa: S603 - fixed git subcommand
            ["git", "-C", str(root), "archive", "--format=tar", commit, "--", *present],  # noqa: S607 - git on PATH
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        msg = f"git archive failed: {exc}"
        raise GitError(msg) from exc
    with tarfile.open(fileobj=io.BytesIO(done.stdout), mode="r:") as archive:
        archive.extractall(dest, filter="data")
    return present
