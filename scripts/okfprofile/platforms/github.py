"""The ``github`` adapter: pull requests, reviews and labels through the REST API (SDD AD-19, W-05).

No third-party client is used: requests go through ``urllib`` behind a small ``Transport`` so tests can replay
recorded responses. Finding the pull request that produced a commit follows the order recorded in V-05: the list
of closed pull requests by ``merge_commit_sha``, then the ``(#n)`` in the squash subject, then
``commits/{sha}/pulls``, which lagged up to 8 s behind the push in the recorded runs and so is retried.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from okfprofile.platforms import (
    CommitInfo,
    MergedChange,
    MergeReview,
    PlatformError,
    normalise_login,
)

API = "https://api.github.com"
SUBJECT_NUMBER = re.compile(r"\(#(?P<number>[0-9]+)\)\s*$")
NEXT_LINK = re.compile(r'<([^>]+)>;\s*rel="next"')
RETRY_STATUS = frozenset({502, 503, 504})
HTTP_NOT_FOUND = 404
HTTP_RETRIES = 3


class NotFoundError(PlatformError):
    """The platform answered 404."""


class Transport(Protocol):
    """Reads one page of a GitHub REST resource."""

    def get(self, path: str) -> tuple[Any, str | None]:
        """Fetch ``path`` (relative to the API root, query included).

        Args:
            path: For example ``repos/o/r/pulls/2``.

        Returns:
            The parsed JSON and the path of the next page, or None.

        Raises:
            NotFoundError: On a 404.
            PlatformError: On any other failure.
        """
        ...


class HttpTransport:
    """``Transport`` over ``urllib`` with a bearer token."""

    def __init__(self, token: str, base: str = API, sleep: Callable[[float], None] = time.sleep) -> None:
        self.token = token
        self.base = base.rstrip("/")
        self.sleep = sleep

    def get(self, path: str) -> tuple[Any, str | None]:
        """Fetch one page, retrying a gateway error up to three times."""
        request = urllib.request.Request(  # noqa: S310 - the base is a fixed https URL
            f"{self.base}/{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "okf-library-template",
            },
        )
        for attempt in range(HTTP_RETRIES):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                    data = json.loads(response.read().decode("utf-8"))
                    link = NEXT_LINK.search(response.headers.get("Link", ""))
            except urllib.error.HTTPError as exc:
                if exc.code == HTTP_NOT_FOUND:
                    msg = f"GitHub: not found: {path}"
                    raise NotFoundError(msg) from exc
                if exc.code in RETRY_STATUS and attempt + 1 < HTTP_RETRIES:
                    self.sleep(2.0 * (attempt + 1))
                    continue
                msg = f"GitHub: HTTP {exc.code} for {path}"
                raise PlatformError(msg) from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                msg = f"GitHub: cannot read {path}: {exc}"
                raise PlatformError(msg) from exc
            return data, (link.group(1).removeprefix(self.base + "/") if link else None)
        msg = f"GitHub: gave up on {path}"
        raise PlatformError(msg)


def paginate(transport: Transport, path: str) -> list[Any]:
    """Every item of a list endpoint, following the ``Link`` header page by page."""
    items: list[Any] = []
    next_path: str | None = path
    while next_path:
        data, next_path = transport.get(next_path)
        items.extend(data)
    return items


def subject_number(subject: str) -> int | None:
    """The pull request number a squash subject ends with (``Title (#12)``), if any."""
    match = SUBJECT_NUMBER.search(subject)
    return int(match["number"]) if match else None


class GitHubAdapter:
    """Resolve a commit on ``main`` to its pull request, reviews and labels.

    Args:
        repo: ``owner/name``.
        transport: Where responses come from.
        sleep: Called between lookup retries.
        attempts: Lookup attempts for a commit whose subject names a pull request.
        delay: Seconds between attempts; the default budget is 30 s (plan step 4).
    """

    def __init__(
        self,
        repo: str,
        transport: Transport,
        sleep: Callable[[float], None] = time.sleep,
        attempts: int = 6,
        delay: float = 6.0,
    ) -> None:
        self.repo = repo
        self.transport = transport
        self.sleep = sleep
        self.attempts = attempts
        self.delay = delay

    def _path(self, tail: str) -> str:
        return f"repos/{self.repo}/{tail}"

    def _pages(self, tail: str) -> list[Any]:
        return paginate(self.transport, self._path(tail))

    def _pull(self, number: int) -> dict[str, Any] | None:
        try:
            data, _ = self.transport.get(self._path(f"pulls/{number}"))
        except NotFoundError:
            return None
        return data if isinstance(data, dict) else None

    def _find_number(self, commit: CommitInfo) -> int | None:
        """One pass of the three lookups; the first that names a pull request merged as ``commit`` wins."""
        try:
            listing, _ = self.transport.get(self._path("pulls?state=closed&sort=updated&direction=desc&per_page=100"))
        except NotFoundError:
            listing = []
        for pull in listing:
            if pull.get("merge_commit_sha") == commit.sha:
                return int(pull["number"])
        number = subject_number(commit.subject)
        if number is not None:
            pull = self._pull(number)
            if pull and pull.get("merge_commit_sha") == commit.sha:
                return number
        try:
            data, _ = self.transport.get(self._path(f"commits/{commit.sha}/pulls"))
        except NotFoundError:
            return None
        for pull in data:
            if pull.get("merge_commit_sha") == commit.sha:
                return int(pull["number"])
        return None

    def find_pull_number(self, commit: CommitInfo) -> int | None:
        """The number of the pull request merged as ``commit``, or None for a push without one.

        A commit whose subject ends ``(#n)`` is certainly a squash merge, so the lookup is retried while the
        platform catches up; any other commit is tried once.
        """
        tries = self.attempts if subject_number(commit.subject) is not None else 1
        for attempt in range(tries):
            number = self._find_number(commit)
            if number is not None:
                return number
            if attempt + 1 < tries:
                self.sleep(self.delay)
        return None

    def _reviews(self, number: int) -> tuple[MergeReview, ...]:
        reviews = [
            MergeReview(
                normalise_login((raw.get("user") or {}).get("login", "")),
                str(raw.get("state", "")).upper(),
                str(raw.get("commit_id", "")),
                str(raw.get("submitted_at") or ""),
            )
            for raw in self._pages(f"pulls/{number}/reviews?per_page=100")
        ]
        return tuple(sorted(reviews, key=lambda r: r.submitted_at))

    def _pusher(self, commit: CommitInfo) -> str:
        try:
            data, _ = self.transport.get(self._path(f"commits/{commit.sha}"))
        except NotFoundError:
            data = {}
        for key in ("author", "committer"):
            login = (data.get(key) or {}).get("login")
            if login:
                return normalise_login(login)
        return normalise_login(commit.author_email.split("@", 1)[0] or commit.author_name)

    def resolve(self, commit: CommitInfo) -> MergedChange:
        """The merged change for ``commit``.

        Raises:
            PlatformError: If a request fails for a reason other than not finding the pull request.
        """
        number = self.find_pull_number(commit)
        if number is None:
            who = self._pusher(commit)
            return MergedChange(commit, "pr-none", None, who, who, commit.sha)
        pull = self._pull(number)
        if pull is None:
            msg = f"GitHub: pull request #{number} disappeared"
            raise PlatformError(msg)
        merged_by = (pull.get("merged_by") or {}).get("login") or (pull.get("user") or {}).get("login", "")
        return MergedChange(
            commit,
            "pr",
            number,
            normalise_login((pull.get("user") or {}).get("login", "")),
            normalise_login(merged_by),
            str((pull.get("head") or {}).get("sha", "")),
            self._reviews(number),
            frozenset(str(label["name"]) for label in pull.get("labels", [])),
        )
