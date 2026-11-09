"""Command-line entry points for CI: ``ci_validate.py`` and ``report_issue.py`` (SDD C-05, W-04).

Exit codes follow ``okfprofile.cli``: 0 success, 1 when validation finds errors, 2 when the command cannot run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from okfprofile.ci import (
    PULL_REQUEST_EVENTS,
    base_ref,
    before_sha,
    change_from_pull_request,
    change_from_push,
    pull_request_number,
)
from okfprofile.cli import validate_main
from okfprofile.ghsetup import GhCli, GhError, GitHubApi
from okfprofile.gitutil import GitError, git
from okfprofile.issues import close_issues, upsert_issue
from okfprofile.platforms import PlatformError
from okfprofile.platforms.github import HttpTransport, Transport, paginate

EXIT_OK = 0
EXIT_USAGE = 2
RECOVERABLE = (GitError, PlatformError, GhError, OSError, ValueError, KeyError, json.JSONDecodeError)


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_USAGE


def commit_messages(root: Path, base: str) -> list[str]:
    """Messages of the commits ``HEAD`` adds to ``base``, oldest first."""
    out = git(root, "log", "--reverse", "--format=%B%x00", f"{base}..HEAD")
    return [m.strip() for m in out.split(chr(0)) if m.strip()]


def validate_event(
    root: Path,
    event_name: str,
    event: dict[str, Any],
    transport: Transport | None,
    repo: str,
    passthrough: Sequence[str] = (),
) -> int:
    """Validate the working tree as the event that started this run calls for.

    A pull request is judged with the base branch's tooling and profile (AD-18), with its labels, reviews and agent
    markers. A push to the main branch is validated whole and compared with the commit before it, with the change
    rules off (the merge already passed them); it catches duplicate ``uid`` values and hand-edited history.
    Anything else (a manual run) is a plain validation.

    Args:
        root: The checked-out repository.
        event_name: ``GITHUB_EVENT_NAME``.
        event: The event payload.
        transport: Where pull request reviews come from (``None`` for events that need none).
        repo: ``owner/name``.
        passthrough: Flags for ``validate_profile.py`` (``--json``, ``--annotations``, ``--summary FILE``).

    Returns:
        The exit code of the validation.
    """
    flags = list(passthrough)
    with tempfile.TemporaryDirectory() as scratch:
        change_file = Path(scratch) / "change.json"
        if event_name in PULL_REQUEST_EVENTS:
            if transport is None:
                msg = "reviews cannot be read without a token"
                raise PlatformError(msg)
            base = base_ref(event)
            reviews = paginate(transport, f"repos/{repo}/pulls/{pull_request_number(event)}/reviews?per_page=100")
            change = change_from_pull_request(event, reviews, commit_messages(root, base))
            change_file.write_text(json.dumps(change.to_dict()), encoding="utf-8")
            arguments = ["--tooling-from", base, "--base", base, "--change", str(change_file)]
        elif event_name == "push" and before_sha(event):
            change_file.write_text(json.dumps(change_from_push(event).to_dict()), encoding="utf-8")
            arguments = ["--base", str(before_sha(event)), "--change", str(change_file), "--merged"]
        else:
            arguments = []
        return validate_main(["--root", str(root), *arguments, *flags])


def ci_validate_main(argv: Sequence[str] | None = None) -> int:
    """``ci_validate.py``: validate for the event that started this workflow run."""
    parser = argparse.ArgumentParser(prog="ci_validate.py", description="Validate as the CI event calls for.")
    parser.add_argument("--root", default=".", help="the checked-out repository (default: the current folder)")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args(argv)
    if not args.event_name or not args.event_path:
        return _fail("no event: GITHUB_EVENT_NAME and GITHUB_EVENT_PATH are set by the workflow runner")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    flags = ["--annotations"]
    summary = os.environ.get("OKF_SUMMARY_FILE") or os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        flags += ["--summary", summary]
    try:
        event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        return validate_event(
            Path(args.root).resolve(), args.event_name, event, HttpTransport(token) if token else None, args.repo, flags
        )
    except RECOVERABLE as exc:
        return _fail(str(exc))


def report_issue_main(argv: Sequence[str] | None = None, api: GitHubApi | None = None) -> int:
    """``report_issue.py``: keep one open issue per label up to date, or close it."""
    parser = argparse.ArgumentParser(prog="report_issue.py", description="Open, update or close a tracking issue.")
    parser.add_argument("--label", required=True, help="the label that marks the tracking issue")
    parser.add_argument("--title", help="issue title (needed unless --close)")
    parser.add_argument("--body-file", help="file holding the issue body (needed unless --close)")
    parser.add_argument("--close", action="store_true", help="close any open issue with the label")
    parser.add_argument("--comment", default="Resolved.", help="comment left when closing")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""), help="owner/name")
    args = parser.parse_args(argv)
    if not args.repo:
        return _fail("pass --repo owner/name (the workflow sets GITHUB_REPOSITORY)")
    client = api or GhCli()
    try:
        if args.close:
            closed = close_issues(client, args.repo, args.label, args.comment)
            print(f"closed {closed} issue(s)", file=sys.stderr)
            return EXIT_OK
        if not args.title or not args.body_file:
            return _fail("--title and --body-file are needed unless --close")
        action, number = upsert_issue(
            client, args.repo, args.label, args.title, Path(args.body_file).read_text(encoding="utf-8")
        )
        print(f"{action} issue #{number}", file=sys.stderr)
    except RECOVERABLE as exc:
        return _fail(str(exc))
    return EXIT_OK
