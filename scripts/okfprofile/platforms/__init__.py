"""Platform adapters (SDD AD-19, C-03 ``platforms``).

Core modules never call a platform. An adapter turns a commit on ``main`` into a ``MergedChange``: who wrote it,
who merged it, what was approved on which commit, and which labels it carried. The revision writer works from
that and nothing else. ``github`` reads the pull request through the REST API; ``git-local`` reads commit trailers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Literal, Protocol

BOT_SUFFIX = "[bot]"
LOGIN_FORBIDDEN = re.compile(r"[^A-Za-z0-9._+-]")


class PlatformError(Exception):
    """A platform could not be read, or its answer is unusable."""


def normalise_login(login: str) -> str:
    """Make a platform user name fit the revision-line grammar.

    A trailing ``[bot]`` is dropped and any other character outside ``A-Za-z0-9._+-`` becomes ``-``.

    Args:
        login: User name as the platform gives it.

    Returns:
        A name that starts with a letter or digit; ``unknown`` if nothing usable is left.
    """
    cleaned = LOGIN_FORBIDDEN.sub("-", login.removesuffix(BOT_SUFFIX).strip()).lstrip("._+-")
    return cleaned or "unknown"


@dataclass(frozen=True)
class CommitInfo:
    """A commit on the first-parent history of the main branch.

    Attributes:
        sha: Full commit hash.
        when: Commit time in UTC.
        subject: First line of the message.
        author_name: Author name.
        author_email: Author email.
        committer_email: Committer email.
        trailers: Trailer keys (lower case) to values, from the last paragraph of the message.
        files: Paths changed against the first parent, forward slashes.
    """

    sha: str
    when: datetime
    subject: str
    author_name: str
    author_email: str
    committer_email: str
    trailers: dict[str, str] = field(default_factory=dict)
    files: tuple[str, ...] = ()

    @property
    def short(self) -> str:
        """The seven-character hash used in ``commit <sha7>`` references."""
        return self.sha[:7]

    @property
    def day(self) -> date:
        """The commit date in UTC."""
        return self.when.astimezone(UTC).date()

    @property
    def is_revision_bot(self) -> bool:
        """True if this is a revision-writer commit (``Revision-Bot: true``)."""
        return self.trailers.get("revision-bot", "").lower() == "true"


@dataclass(frozen=True)
class MergeReview:
    """One review given to the change before it merged.

    Attributes:
        login: Reviewer, normalised.
        state: ``APPROVED``, ``CHANGES_REQUESTED``, ``COMMENTED`` or ``DISMISSED``.
        commit_id: The commit the review was given on.
        submitted_at: ISO 8601 time, used only to order reviews.
    """

    login: str
    state: str
    commit_id: str
    submitted_at: str


Kind = Literal["pr", "pr-none", "commit"]


@dataclass(frozen=True)
class MergedChange:
    """A change that reached the main branch, as the revision writer needs it.

    Attributes:
        commit: The commit on the main branch.
        kind: ``pr`` (a pull request), ``pr-none`` (pushed without one) or ``commit`` (``git-local``).
        number: Pull request number for ``pr``.
        author: Author, normalised.
        merged_by: Who merged or pushed it, normalised.
        head_sha: Head of the pull request at merge; for ``commit``, the commit itself.
        reviews: Every review, oldest first.
        labels: Labels on the pull request, or those the trailers stand for in ``git-local``.
    """

    commit: CommitInfo
    kind: Kind
    number: int | None
    author: str
    merged_by: str
    head_sha: str
    reviews: tuple[MergeReview, ...] = ()
    labels: frozenset[str] = frozenset()

    @property
    def reference(self) -> str:
        """The change as written in a revision line: ``PR #12``, ``PR none`` or ``commit abc1234``."""
        if self.kind == "pr":
            return f"PR #{self.number}"
        if self.kind == "pr-none":
            return "PR none"
        return f"commit {self.commit.short}"


class PlatformAdapter(Protocol):
    """Reads the platform's record of a commit."""

    def resolve(self, commit: CommitInfo) -> MergedChange:
        """The merged change a commit on the main branch stands for.

        Args:
            commit: The commit.

        Returns:
            The change, with its reviews and labels.

        Raises:
            PlatformError: If the platform cannot be read.
        """
        ...
