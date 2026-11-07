"""Commits on the main branch, read with git (used by both adapters and the revision writer)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from okfprofile.gitutil import GitError, git
from okfprofile.platforms import CommitInfo

TRAILER = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9-]*):[ \t]*(?P<value>.*)$")
FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"
BOT_TRAILER = "Revision-Bot: true"


def parse_trailers(message: str) -> dict[str, str]:
    """Trailers from the last paragraph of a commit message.

    Args:
        message: The full message.

    Returns:
        Lower-case key to value; empty if the last paragraph is not made only of trailers. A repeated key keeps
        its last value.
    """
    paragraphs = [p for p in re.split(r"\n\s*\n", message.strip()) if p.strip()]
    if len(paragraphs) < 2:
        return {}
    trailers = {}
    for line in paragraphs[-1].splitlines():
        match = TRAILER.match(line)
        if match is None:
            return {}
        trailers[match["key"].lower()] = match["value"].strip()
    return trailers


def _commit(root: Path, sha: str) -> CommitInfo:
    fields = git(root, "show", "-s", "--format=%H%x1f%cI%x1f%s%x1f%an%x1f%ae%x1f%ce%x1f%B", sha).split(FIELD_SEP, 6)
    full, stamp, subject, name, email, committer, message = fields
    names = git(
        root, "diff-tree", "-r", "--no-renames", "--name-only", "--no-commit-id", "-m", "--first-parent", "--root", sha
    )
    return CommitInfo(
        full.strip(),
        datetime.fromisoformat(stamp).astimezone(UTC),
        subject,
        name,
        email,
        committer,
        parse_trailers(message),
        tuple(sorted({p for p in names.splitlines() if p})),
    )


def last_revision_bot_commit(root: Path, ref: str = "HEAD") -> str | None:
    """The most recent commit on the first-parent history of ``ref`` that carries ``Revision-Bot: true``."""
    out = git(root, "log", "--first-parent", "--format=%H%x1f%B%x1e", ref)
    for record in out.split(RECORD_SEP):
        if not record.strip():
            continue
        sha, _, message = record.strip().partition(FIELD_SEP)
        if parse_trailers(message).get("revision-bot", "").lower() == "true":
            return sha
    return None


def commits_after(root: Path, base: str | None, ref: str = "HEAD") -> list[CommitInfo]:
    """Commits on the first-parent history of ``ref`` after ``base``, oldest first.

    Args:
        root: Repository root.
        base: Commit or tag to start after; None means the whole history.
        ref: Tip of the history.

    Returns:
        The commits, revision-writer commits included.

    Raises:
        GitError: If git fails or ``base`` is not an ancestor-free name git knows.
    """
    spec = f"{base}..{ref}" if base else ref
    shas = git(root, "rev-list", "--first-parent", "--reverse", spec).split()
    try:
        return [_commit(root, sha) for sha in shas]
    except ValueError as exc:
        msg = f"cannot read commits: {exc}"
        raise GitError(msg) from exc
