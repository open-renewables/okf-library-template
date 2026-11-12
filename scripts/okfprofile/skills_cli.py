"""Command-line entry points for ``check_skills.py`` and ``link_skills.py`` (SDD C-04, C-08; ADR-002).

Exit codes follow ``okfprofile.cli``: 0 success, 1 findings or a refused folder, 2 cannot run.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from okfprofile.config import ProfileError, load_profile
from okfprofile.skills import ADAPTERS, SKILLS_DIR, check_skills, link_skills

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def check_skills_main(argv: Sequence[str] | None = None) -> int:
    """``check_skills.py``: check the agent skills against the Agent Skills format and the profile."""
    parser = argparse.ArgumentParser(prog="check_skills.py", description="Check agent skills.")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    try:
        profile = load_profile(Path(args.root).resolve())
    except (ProfileError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    findings, count = check_skills(profile)
    for finding in findings:
        print(finding.human(), file=sys.stderr)
    print(f"{len(findings)} finding(s) in {count} skill(s) under {SKILLS_DIR.as_posix()}", file=sys.stderr)
    if args.json:
        report = {
            "ok": not findings,
            "skills": count,
            "findings": [{"file": f.file, "message": f.message} for f in findings],
        }
        print(json.dumps(report, indent=2))
    return EXIT_FINDINGS if findings else EXIT_OK


def link_skills_main(argv: Sequence[str] | None = None) -> int:
    """``link_skills.py``: make the skills visible to one provider, in the user's own checkout."""
    parser = argparse.ArgumentParser(
        prog="link_skills.py",
        description="Copy .agents/skills/<name> into a provider's skills folder (optional adapter, not committed).",
    )
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--target", choices=sorted(ADAPTERS), default="claude", help="provider adapter")
    parser.add_argument("--link", action="store_true", help="make a directory link instead of a copy")
    parser.add_argument("--dry-run", action="store_true", help="report without changing anything")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not (root / SKILLS_DIR).is_dir():
        print(f"error: no {SKILLS_DIR.as_posix()} folder under {root}", file=sys.stderr)
        return EXIT_USAGE
    results = link_skills(root, args.target, link=args.link, dry_run=args.dry_run)
    for result in results:
        print(f"{result.action}: {result.target}", file=sys.stderr)
    if args.json:
        print(json.dumps([{"skill": r.skill, "action": r.action, "target": r.target} for r in results], indent=2))
    return EXIT_FINDINGS if any(r.action == "refused" for r in results) else EXIT_OK
