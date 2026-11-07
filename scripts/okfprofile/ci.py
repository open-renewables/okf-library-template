"""What a validation run in CI needs to know about the event that started it (SDD W-04, FR1.5, FR2.5, FR2.6).

The workflow passes the event payload; this module turns it into the ``ChangeContext`` the checks read: the labels
(``approved-move``, ``profile-migration``), the author, the head commit, the latest review of each reviewer with the
commit it was given on, and whether commit trailers or the description show that an AI tool helped. Nothing here
calls a platform: the caller fetches the reviews.
"""

from __future__ import annotations

import re
from typing import Any

from okfprofile.changes import ChangeContext, Review
from okfprofile.platforms.commits import parse_trailers

ZERO_SHA = "0" * 40
DECISIONS = {"APPROVED": True, "CHANGES_REQUESTED": False, "DISMISSED": False}
AGENT_MARKER = re.compile(
    r"(Co-Authored-By:[^\n]*\b(Claude|Copilot|ChatGPT|GPT|Gemini|Cursor|Codex)\b"
    r"|Agent-Drafted:\s*yes"
    r"|Generated with \[?(Claude Code|Copilot|Codex)\b)",
    re.IGNORECASE,
)
PULL_REQUEST_EVENTS = frozenset({"pull_request", "pull_request_review", "pull_request_review_comment"})


def latest_reviews(raw: list[dict[str, Any]]) -> list[Review]:
    """The latest decision of each reviewer, as the publishing pre-check reads it.

    Args:
        raw: Reviews as the REST API returns them, oldest first.

    Returns:
        One ``Review`` per reviewer. A later comment does not undo an approval; a later change request or a
        dismissal does.
    """
    latest: dict[str, Review] = {}
    for review in sorted(raw, key=lambda r: str(r.get("submitted_at") or "")):
        approved = DECISIONS.get(str(review.get("state", "")).upper())
        login = (review.get("user") or {}).get("login", "")
        if approved is not None and login:
            latest[login] = Review(login, approved, str(review.get("commit_id", "")))
    return list(latest.values())


def agent_markers_in(*texts: str) -> bool:
    """True if any text shows that an AI tool helped: a co-author trailer, ``Agent-Drafted: yes`` or a tool credit."""
    return any(AGENT_MARKER.search(text or "") for text in texts)


def change_from_pull_request(
    event: dict[str, Any], raw_reviews: list[dict[str, Any]], commit_messages: list[str]
) -> ChangeContext:
    """The change context of a pull request event.

    Args:
        event: The ``pull_request`` or ``pull_request_review`` event payload.
        raw_reviews: The pull request's reviews, oldest first.
        commit_messages: Messages of the commits the pull request adds.

    Returns:
        The context. ``paths`` stays empty: the validator reads them from git against the base.
    """
    pull = event["pull_request"]
    return ChangeContext(
        labels={str(label["name"]) for label in pull.get("labels", [])},
        author=str((pull.get("user") or {}).get("login", "")),
        head_sha=str((pull.get("head") or {}).get("sha", "")),
        reviews=latest_reviews(raw_reviews),
        agent_markers=agent_markers_in(str(pull.get("body") or ""), *commit_messages),
        reviews_known=True,
    )


def change_from_push(event: dict[str, Any]) -> ChangeContext:
    """The change context of a push to the main branch: the head commit, and whether it is a revision-writer commit."""
    head = event.get("head_commit") or {}
    message = str(head.get("message", ""))
    return ChangeContext(
        author=str((event.get("pusher") or {}).get("name", "")),
        head_sha=str(event.get("after", "")),
        revision_bot=parse_trailers(message).get("revision-bot", "").lower() == "true",
    )


def pull_request_number(event: dict[str, Any]) -> int:
    """The number of the pull request an event belongs to."""
    return int(event["pull_request"]["number"])


def base_ref(event: dict[str, Any]) -> str:
    """The branch a pull request merges into, as a remote-tracking ref (``origin/main``)."""
    return f"origin/{event['pull_request']['base']['ref']}"


def before_sha(event: dict[str, Any]) -> str | None:
    """The commit a push moved the branch from, or None for a new branch."""
    before = str(event.get("before", ""))
    return None if not before or before == ZERO_SHA else before
