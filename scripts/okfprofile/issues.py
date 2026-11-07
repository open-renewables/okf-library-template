"""One tracking issue per label (SDD FR2.4, W-06): a failing ``main`` and the weekly review report.

A run finds the open issue that carries the label and updates it, or opens one, so repeated failures or reports
never pile up. Pull requests are not counted: the issues endpoint lists them too.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from okfprofile.ghsetup import GitHubApi


def open_issues(api: GitHubApi, repo: str, label: str) -> list[dict[str, Any]]:
    """The open issues (not pull requests) that carry ``label``, oldest first."""
    items = api.paginate(f"repos/{repo}/issues?labels={quote(label, safe='')}&state=open&per_page=100")
    return sorted((i for i in items if "pull_request" not in i), key=lambda i: int(i["number"]))


def upsert_issue(api: GitHubApi, repo: str, label: str, title: str, body: str) -> tuple[str, int]:
    """Update the open issue with ``label``, or create one.

    Args:
        api: GitHub.
        repo: ``owner/name``.
        label: The label that marks the tracking issue; it must exist (``setup_repo.py`` creates it).
        title: New title.
        body: New body.

    Returns:
        ``("updated", number)`` or ``("created", number)``. The oldest open issue is the tracking issue.
    """
    existing = open_issues(api, repo, label)
    if existing:
        number = int(existing[0]["number"])
        if existing[0].get("title") != title or existing[0].get("body") != body:
            api.request("PATCH", f"repos/{repo}/issues/{number}", {"title": title, "body": body})
        return "updated", number
    made = api.request("POST", f"repos/{repo}/issues", {"title": title, "body": body, "labels": [label]})
    return "created", int(made["number"])


def close_issues(api: GitHubApi, repo: str, label: str, comment: str) -> int:
    """Close every open issue with ``label`` after a comment; returns how many were closed."""
    existing = open_issues(api, repo, label)
    for issue in existing:
        number = int(issue["number"])
        api.request("POST", f"repos/{repo}/issues/{number}/comments", {"body": comment})
        api.request("PATCH", f"repos/{repo}/issues/{number}", {"state": "closed", "state_reason": "completed"})
    return len(existing)
