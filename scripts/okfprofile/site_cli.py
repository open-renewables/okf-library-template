"""Command-line entry points for the site tasks (SDD C-04, C-07, W-08; AD-20).

``build_site.py`` builds with one builder. ``check_site.py`` compares a build with the bundle, writes the release
manifest, runs the offline link check and answers whether a tag run deploys. Exit codes follow ``okfprofile.cli``:
0 success, 1 findings, 2 cannot run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from okfprofile.site import (
    BUILDERS,
    DEFAULT_OUT,
    PageComparison,
    SiteError,
    build,
    compare_pages,
    docs_dir,
    should_deploy,
    write_manifest,
)

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
LYCHEE_ARGS = ("--offline", "--include-fragments", "--no-progress")


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_USAGE


def build_site_main(argv: Sequence[str] | None = None) -> int:
    """``build_site.py``: build the static site with MkDocs or Zensical, from the bundle in place."""
    parser = argparse.ArgumentParser(prog="build_site.py", description="Build the static site.")
    parser.add_argument("builder", choices=BUILDERS, help="mkdocs (blocking, strict) or zensical (non-blocking)")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--out", help="output folder (default: site, or site-zensical)")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        out = build(root, args.builder, Path(args.out) if args.out else None)
    except SiteError as exc:
        return _fail(str(exc))
    print(f"built {out.relative_to(root) if out.is_relative_to(root) else out}", file=sys.stderr)
    return EXIT_OK


def _linkcheck(site: Path) -> int | None:
    binary = shutil.which("lychee")
    if binary is None:
        print("notice: lychee is not installed; link check skipped (CI runs it)", file=sys.stderr)
        return None
    done = subprocess.run(  # noqa: S603 - fixed arguments
        [binary, *LYCHEE_ARGS, "--root-dir", str(site), str(site)], check=False
    )
    return done.returncode


def _lacks(folder: Path, result: PageComparison, other: Path) -> list[str]:
    """Pages that another build lacks and this one has."""
    return [p for p in compare_pages(folder, other).missing if p not in result.missing]


def check_site_main(argv: Sequence[str] | None = None) -> int:
    """``check_site.py``: check a built site against the bundle."""
    parser = argparse.ArgumentParser(prog="check_site.py", description="Check a built site.")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--site", help="built site folder (default: site)")
    parser.add_argument("--against", help="another built site whose page list must equal this one's")
    parser.add_argument("--manifest", metavar="TAG", help="write release.json naming this tag into the site")
    parser.add_argument("--commit", default="", help="commit the tag points to (with --manifest)")
    parser.add_argument("--linkcheck", action="store_true", help="run lychee offline over the site if it is installed")
    parser.add_argument("--deploy-ref", metavar="REF", help="print true or false: does a run on this tag deploy?")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.deploy_ref is not None:
        print("true" if should_deploy(root, args.deploy_ref) else "false")
        return EXIT_OK
    site = Path(args.site).resolve() if args.site else (root / DEFAULT_OUT["mkdocs"]).resolve()
    try:
        folder = docs_dir(root)
        if not site.is_dir():
            return _fail(f"{site} is not a built site; run build_site.py first")
        result = compare_pages(folder, site)
        lacks = _lacks(folder, result, Path(args.against).resolve()) if args.against else []
        if args.manifest:
            write_manifest(site, args.manifest, args.commit)
    except SiteError as exc:
        return _fail(str(exc))
    for page in result.missing:
        print(f"{site.name}: missing page {page}", file=sys.stderr)
    for page in result.extra:
        print(f"{site.name}: page {page} has no concept", file=sys.stderr)
    for page in lacks:
        print(f"{Path(args.against).name}: missing page {page} that {site.name} has", file=sys.stderr)
    failed = not result.ok or bool(lacks) or bool(args.linkcheck and _linkcheck(site))
    print(f"{len(result.missing)} missing and {len(result.extra)} extra page(s) in {site.name}", file=sys.stderr)
    if args.json:
        report = {"ok": not failed, "missing": list(result.missing), "extra": list(result.extra)}
        print(json.dumps(report, indent=2))
    return EXIT_FINDINGS if failed else EXIT_OK
