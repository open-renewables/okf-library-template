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


def git_bytes(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    """Run ``git -C root <args>`` and return its standard output as bytes.

    Args:
        root: Repository root.
        *args: Arguments to git.
        stdin: Bytes to send to git's standard input.

    Returns:
        Standard output, undecoded.

    Raises:
        GitError: If git cannot be run or exits non-zero.
    """
    try:
        done = subprocess.run(  # noqa: S603 - arguments are fixed git subcommands and refs given by the user
            ["git", "-C", str(root), *args],  # noqa: S607 - git is found on PATH by design
            capture_output=True,
            check=False,
            input=stdin,
        )
    except OSError as exc:
        msg = f"cannot run git: {exc}"
        raise GitError(msg) from exc
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", errors="replace").strip()
        msg = f"git {' '.join(args)} failed: {detail}"
        raise GitError(msg)
    return done.stdout


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
    return git_bytes(root, *args).decode("utf-8", errors="replace")


def tree_entries(root: Path, ref: str) -> list[tuple[str, str, str]]:
    """Every file in the tree of ``ref`` as ``(mode, blob id, path)``, in git's order.

    Args:
        root: Repository root.
        ref: Commit, tag or branch.

    Returns:
        Entries with forward-slash paths; submodules and symbolic links are left out.
    """
    out = git_bytes(root, "ls-tree", "-r", "-z", "--full-tree", f"{ref}^{{commit}}").decode("utf-8")
    entries = []
    for record in filter(None, out.split("\0")):
        meta, _, path = record.partition("\t")
        mode, kind, blob = meta.split()
        if kind == "blob" and mode in {"100644", "100755"}:
            entries.append((mode, blob, path))
    return entries


def read_blobs(root: Path, blob_ids: list[str]) -> dict[str, bytes]:
    """The content of blobs, read with one ``git cat-file --batch`` process.

    Args:
        root: Repository root.
        blob_ids: Object IDs.

    Returns:
        Object ID to bytes.

    Raises:
        GitError: If git fails or an object is missing.
    """
    unique = list(dict.fromkeys(blob_ids))
    out = git_bytes(root, "cat-file", "--batch", stdin=("\n".join(unique) + "\n").encode("ascii") if unique else b"")
    blobs: dict[str, bytes] = {}
    position = 0
    for wanted in unique:
        end = out.index(b"\n", position)
        header = out[position:end].decode("ascii").split()
        if len(header) != 3 or header[1] != "blob":
            msg = f"git cat-file: cannot read object {wanted}"
            raise GitError(msg)
        size = int(header[2])
        blobs[wanted] = out[end + 1 : end + 1 + size]
        position = end + 1 + size + 1
    return blobs


def commit_info(root: Path, ref: str) -> tuple[str, int]:
    """The full hash and committer timestamp (seconds since the epoch) of the commit ``ref`` points to."""
    sha, stamp = git(root, "show", "-s", "--format=%H %ct", f"{ref}^{{commit}}").split()
    return sha, int(stamp)


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
