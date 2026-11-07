"""Command-line entry point for ``setup_repo.py`` (SDD C-04, W-01 step 4, W-11).

Exit codes follow ``okfprofile.cli``: 0 success (``--dry-run`` lists changes and still exits 0), 1 when ``--check``
or a plan finds a problem, 2 when the command cannot run.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from okfprofile.config import ProfileError, load_profile
from okfprofile.ghsetup import (
    RULESET_NAME,
    GhCli,
    GhError,
    GitHubApi,
    Plan,
    apply_plan,
    build_plan,
    check_app,
    promote_profile,
)
from okfprofile.gitutil import GitError, git
from okfprofile.revision_cli import repository_from_remote

EXIT_OK = 0
EXIT_PROBLEM = 1
EXIT_USAGE = 2


class UsageError(Exception):
    """The command cannot run as asked."""


@dataclass
class Outcome:
    """What a run found and did."""

    repo: str
    plan: Plan
    problems: list[str] = field(default_factory=list)
    profile_changed: bool = False


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup_repo.py", description="Configure the GitHub repository (platform github)."
    )
    parser.add_argument("--root", default=".", help="the library's working tree (default: the current folder)")
    parser.add_argument("--repo", help="owner/name (default: the origin remote); every request names it")
    parser.add_argument("--app-slug", help="slug of the revision GitHub App: put it on the ruleset bypass list")
    parser.add_argument("--dry-run", action="store_true", help="list the changes a run would make; change nothing")
    parser.add_argument("--check", action="store_true", help="check the App set-up and report drift; change nothing")
    parser.add_argument(
        "--promote", action="store_true", help="also set up a public library (W-11): CodeQL, Pages, App token"
    )
    parser.add_argument(
        "--ruleset-name", default=RULESET_NAME, help="the ruleset to create or converge (default: main-protect)"
    )
    parser.add_argument("--no-required-check", action="store_true", help="leave the validate check out of the ruleset")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    return parser


def _run(args: argparse.Namespace, client: GitHubApi) -> Outcome:
    """Plan, then apply (unless ``--dry-run`` or ``--check``).

    Raises:
        UsageError: If the library is not on ``github`` or the repository cannot be told.
    """
    root = Path(args.root).resolve()
    profile = load_profile(root)
    if profile.platform != "github":
        msg = "this library's platform is not github; there is nothing to set up"
        raise UsageError(msg)
    repo = args.repo or repository_from_remote(git(root, "remote", "get-url", "origin"))
    if not repo:
        msg = "cannot tell the repository: pass --repo owner/name"
        raise UsageError(msg)
    plan = build_plan(
        client,
        repo,
        root,
        args.app_slug,
        False if args.no_required_check else None,
        promote=args.promote,
        ruleset_name=args.ruleset_name,
    )
    outcome = Outcome(repo, plan, list(plan.problems))
    if args.check:
        outcome.problems += [f"drift: {op.area}: {op.detail}" for op in plan.operations]
        if args.app_slug:
            outcome.problems += check_app(client, repo, args.app_slug, args.ruleset_name)
    elif not args.dry_run and not plan.problems:
        apply_plan(client, plan)
        outcome.profile_changed = args.promote and promote_profile(root)
    return outcome


def _report(outcome: Outcome, args: argparse.Namespace) -> None:
    verb = "would" if args.dry_run or args.check else "did"
    for op in outcome.plan.operations:
        print(f"{verb}: {op.area}: {op.detail}", file=sys.stderr)
    for note in outcome.plan.notes:
        print(f"note: {note}", file=sys.stderr)
    for problem in outcome.problems:
        print(f"problem: {problem}", file=sys.stderr)
    if outcome.profile_changed:
        print(
            "changed profile/profile.yaml: rules.revision_token is github-app; commit it in a pull request",
            file=sys.stderr,
        )
    if not outcome.plan.operations and not outcome.problems:
        print("nothing to change", file=sys.stderr)
    if args.json:
        data = {
            "repository": outcome.repo,
            "operations": [{"area": o.area, "detail": o.detail} for o in outcome.plan.operations],
            "notes": outcome.plan.notes,
            "problems": outcome.problems,
            "profile_changed": outcome.profile_changed,
        }
        print(json.dumps(data, indent=2))


def setup_repo_main(argv: Sequence[str] | None = None, api: GitHubApi | None = None) -> int:
    """``setup_repo.py``: configure the GitHub repository of a ``github`` library; safe to rerun."""
    args = _parser().parse_args(argv)
    try:
        outcome = _run(args, api or GhCli())
    except (ProfileError, GhError, GitError, OSError, UsageError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    _report(outcome, args)
    return EXIT_PROBLEM if outcome.problems else EXIT_OK
