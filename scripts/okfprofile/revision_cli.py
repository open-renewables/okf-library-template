"""Command-line entry point for ``write_revision.py`` (SDD C-04, W-05).

Exit codes follow ``okfprofile.cli``: 0 success, 1 when ``--check-since`` finds a missing revision line, 2 when
the command cannot run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from okfprofile.bundle import load_bundle
from okfprofile.codeowners import load_codeowners
from okfprofile.config import Profile, ProfileError, load_profile
from okfprofile.gitutil import GitError, git
from okfprofile.platforms import PlatformAdapter, PlatformError
from okfprofile.platforms.git_local import GitLocalAdapter
from okfprofile.platforms.github import GitHubAdapter, HttpTransport
from okfprofile.report import Report
from okfprofile.revision_writer import RevisionError, catch_up, check_since, commit_revision
from okfprofile.stale import DurationError, find_stale

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
REMOTE = re.compile(r"github\.com[:/](?P<repo>[^/\s]+/[^/\s]+?)(?:\.git)?/?$")
RECOVERABLE = (ProfileError, GitError, PlatformError, RevisionError, DurationError, OSError, ValueError)


def repository_from_remote(url: str) -> str | None:
    """``owner/name`` from a GitHub remote URL (https or ssh), or None."""
    match = REMOTE.search(url.strip())
    return match["repo"] if match else None


def make_adapter(profile: Profile, repo: str | None = None) -> PlatformAdapter:
    """The adapter for the profile's platform.

    Args:
        profile: The loaded profile.
        repo: ``owner/name`` for ``github``; default is ``GITHUB_REPOSITORY``, then the ``origin`` remote.

    Returns:
        The adapter.

    Raises:
        PlatformError: If the platform is unknown, or ``github`` has no token or repository.
    """
    if profile.platform == "git-local":
        return GitLocalAdapter(profile)
    if profile.platform != "github":
        msg = f"unknown platform '{profile.platform}'"
        raise PlatformError(msg)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        msg = "platform github needs GITHUB_TOKEN (or GH_TOKEN) in the environment"
        raise PlatformError(msg)
    name = repo or os.environ.get("GITHUB_REPOSITORY")
    if not name:
        try:
            name = repository_from_remote(git(profile.root, "remote", "get-url", "origin"))
        except GitError:
            name = None
    if not name:
        msg = "cannot tell the repository: set GITHUB_REPOSITORY or pass --repo owner/name"
        raise PlatformError(msg)
    return GitHubAdapter(name, HttpTransport(token))


def write_revision_main(argv: Sequence[str] | None = None) -> int:
    """``write_revision.py``: record merged changes in revision histories, or check that they are recorded."""
    parser = argparse.ArgumentParser(prog="write_revision.py", description="Write or check revision history.")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--ref", default="HEAD", help="tip of the history to read (default: HEAD)")
    parser.add_argument(
        "--since", metavar="REF", help="record changes after this commit instead of after the last bot commit"
    )
    parser.add_argument(
        "--check-since", metavar="TAG", help="report merged changes after TAG that have no revision line"
    )
    parser.add_argument("--repo", help="owner/name for platform github")
    parser.add_argument("--commit", action="store_true", help="commit the result with the Revision-Bot trailer")
    parser.add_argument("--dry-run", action="store_true", help="show what would be written; change nothing")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # revision lines hold a middle dot; a Windows console would garble it
    root = Path(args.root).resolve()
    try:
        profile = load_profile(root)
        adapter = make_adapter(profile, args.repo)
        if args.check_since:
            report = Report(check_since(profile, adapter, args.check_since, args.ref))
            for finding in report.findings:
                print(finding.human() if hasattr(finding, "human") else finding, file=sys.stderr)
            print(f"{len(report.errors)} missing revision line(s)", file=sys.stderr)
            if args.json:
                print(report.to_json())
            return EXIT_OK if report.ok else EXIT_FINDINGS
        result = catch_up(profile, adapter, load_codeowners(root), args.ref, args.since, args.dry_run)
        committed = commit_revision(root, result.files) if args.commit and not args.dry_run else False
    except RECOVERABLE as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    for path, line in result.lines:
        print(f"{path}: {line}", file=sys.stderr)
    print(
        f"{result.changes} change(s) read, {len(result.lines)} line(s) {'would be ' if args.dry_run else ''}added, "
        f"{result.already_present} already recorded{'; committed' if committed else ''}",
        file=sys.stderr,
    )
    if args.json:
        print(
            json.dumps(
                {
                    "changes": result.changes,
                    "lines": [{"file": f, "line": text} for f, text in result.lines],
                    "files": result.files,
                    "already_present": result.already_present,
                    "committed": committed,
                },
                indent=2,
            )
        )
    return EXIT_OK


def stale_main(argv: Sequence[str] | None = None) -> int:
    """``stale_report.py``: list concepts past their review date (and, optionally, changes with no revision line).

    The report is information, not a gate: the exit code is 0 whatever it finds, and 2 when it cannot run.
    """
    parser = argparse.ArgumentParser(prog="stale_report.py", description="Report concepts due for review.")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument(
        "--now", metavar="DATETIME", help="judge by this ISO 8601 instant, with an offset (default: now)"
    )
    parser.add_argument("--check-since", metavar="TAG", help="also list merged changes after TAG with no revision line")
    parser.add_argument("--repo", help="owner/name for platform github")
    parser.add_argument("--markdown", metavar="FILE", help="write the issue body to FILE")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        now = datetime.fromisoformat(args.now) if args.now else None
        if now is not None and now.tzinfo is None:
            msg = "--now needs an offset, for example 2026-11-03T00:00:00Z"
            raise ValueError(msg)
        profile = load_profile(root)
        report = find_stale(profile, load_bundle(profile.bundle_root, root), now)
        if args.check_since:
            report.gaps = check_since(profile, make_adapter(profile, args.repo), args.check_since)
    except RECOVERABLE as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    if report.human():
        print(report.human(), file=sys.stderr)
    gap_count = len(report.gaps or [])
    print(
        f"{len(report.stale)} stale, {len(report.unrevised)} with no revision, {gap_count} change(s) without a line",
        file=sys.stderr,
    )
    if args.markdown:
        Path(args.markdown).write_text(report.to_markdown(), encoding="utf-8", newline="\n")
    if args.json:
        print(report.to_json())
    return EXIT_OK
