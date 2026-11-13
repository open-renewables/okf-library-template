"""Command-line entry points for ``build_bundle.py`` and ``release.py`` (SDD C-04, W-07).

Exit codes follow ``okfprofile.cli``: 0 success, 1 when a check fails (a missing revision line, a validation
error, an archive that does not match its manifest), 2 when the command cannot run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from okfprofile.archive import ArchiveError, build_archive, rebuild_problems, verify_archive, write_archive
from okfprofile.cli import validate_main
from okfprofile.config import Profile, ProfileError, load_profile
from okfprofile.gitutil import GitError
from okfprofile.platforms import PlatformError
from okfprofile.release import ReleaseError, finish, prepare, run_gate
from okfprofile.revision_cli import make_adapter

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
RECOVERABLE = (ProfileError, GitError, PlatformError, ArchiveError, ReleaseError, OSError, ValueError, KeyError)


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_USAGE


def _manifests(folder: Path) -> list[Path]:
    found = sorted(folder.glob("*.manifest.json"))
    if not found:
        msg = f"no *.manifest.json in {folder}"
        raise ArchiveError(msg)
    return found


def verify_folder(folder: Path) -> list[str]:
    """Check every archive in ``folder`` against its manifest and its ``.sha256`` file (what ``sha256sum -c`` reads)."""
    problems: list[str] = []
    for manifest_path in _manifests(folder):
        name = manifest_path.name.removesuffix(".manifest.json")
        archive = folder / f"{name}.tar.gz"
        problems += verify_archive(archive, json.loads(manifest_path.read_text(encoding="utf-8")))
        checksum = folder / f"{name}.tar.gz.sha256"
        expected = f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
        if not checksum.is_file() or checksum.read_text(encoding="utf-8") != expected:
            problems.append(f"{checksum.name}: missing or not the digest of {archive.name}")
    return problems


def rebuild_folder(profile: Profile, folder: Path) -> list[str]:
    """Rebuild the archive of each manifest in ``folder`` from the manifest's tag and compare the tar digests."""
    problems: list[str] = []
    for manifest_path in _manifests(folder):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        problems += rebuild_problems(profile, manifest, str(manifest["tag"]))
    return problems


def _check_existing(args: argparse.Namespace, profile: Profile) -> list[str] | None:
    """Run the check the options ask for, or return None when the options ask to build an archive."""
    if args.verify_dir:
        return verify_folder(Path(args.verify_dir))
    if args.rebuild_dir:
        return rebuild_folder(profile, Path(args.rebuild_dir))
    if args.verify:
        archive_path = Path(args.verify)
        manifest_path = (
            Path(args.manifest)
            if args.manifest
            else archive_path.with_name(archive_path.name.removesuffix(".tar.gz") + ".manifest.json")
        )
        return verify_archive(archive_path, json.loads(manifest_path.read_text(encoding="utf-8")))
    if args.rebuild_check:
        manifest = json.loads(Path(args.rebuild_check).read_text(encoding="utf-8"))
        return rebuild_problems(profile, manifest, args.ref)
    return None


def build_bundle_main(argv: Sequence[str] | None = None) -> int:
    """``build_bundle.py``: build, verify or rebuild-check the release archive."""
    parser = argparse.ArgumentParser(prog="build_bundle.py", description="Build or check the release archive.")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--tag", help="release tag, for example v0.2.0 (needed to build)")
    parser.add_argument("--ref", default="HEAD", help="commit, tag or branch to build from (default: HEAD)")
    parser.add_argument("--out", default="dist", help="folder for the archive, checksum and manifest (default: dist)")
    parser.add_argument("--verify", metavar="ARCHIVE", help="check an existing .tar.gz against its manifest")
    parser.add_argument("--manifest", metavar="FILE", help="manifest to check against (default: beside the archive)")
    parser.add_argument("--rebuild-check", metavar="MANIFEST", help="rebuild from --ref and compare the tar digest")
    parser.add_argument(
        "--verify-dir", metavar="DIR", help="check every archive in DIR against its manifest and checksum"
    )
    parser.add_argument(
        "--rebuild-dir", metavar="DIR", help="rebuild each manifest's tag from this checkout and compare"
    )
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        profile = load_profile(root)
        checked = _check_existing(args, profile)
        if checked is not None:
            problems = checked
        else:
            if not args.tag:
                return _fail("--tag is required to build an archive")
            archive = build_archive(profile, args.tag, args.ref)
            files = write_archive(archive, Path(args.out))
            for file in files:
                print(f"wrote {file}", file=sys.stderr)
            print(f"tar sha256 {archive.tar_sha256}", file=sys.stderr)
            if args.json:
                print(json.dumps({"files": [str(f) for f in files], "manifest": archive.manifest}, indent=2))
            return EXIT_OK
    except (*RECOVERABLE, json.JSONDecodeError) as exc:
        return _fail(str(exc))
    for problem in problems:
        print(problem, file=sys.stderr)
    print("archive matches" if not problems else f"{len(problems)} problem(s)", file=sys.stderr)
    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}))
    return EXIT_OK if not problems else EXIT_FAILED


def release_main(argv: Sequence[str] | None = None) -> int:
    """``release.py``: the revision-line gate, validation, the archive and (``git-local``) the annotated tag."""
    parser = argparse.ArgumentParser(prog="release.py", description="Cut a release.")
    parser.add_argument("tag", help="release tag, for example v0.2.0")
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")
    parser.add_argument("--out", default="dist", help="folder for the archive files (default: dist)")
    parser.add_argument("--repo", help="owner/name for platform github")
    parser.add_argument(
        "--dry-run", action="store_true", help="run every check and build the archive, but create no tag"
    )
    parser.add_argument("--sign", action="store_true", help="sign the tag (git tag -s)")
    parser.add_argument(
        "--from-tag",
        action="store_true",
        help="the tag already exists and is checked out (the release workflow): gate against the tag before it",
    )
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        profile = load_profile(root)
        prepare(profile, args.tag, from_tag=args.from_tag)
        result = run_gate(profile, make_adapter(profile, args.repo), args.tag)
        for finding in result.gaps:
            print(f"{finding.file}:{finding.line}: {finding.code}: {finding.message}", file=sys.stderr)
        if result.gaps:
            print(
                f"{len(result.gaps)} merged change(s) have no revision line: run `uv run poe revision` first",
                file=sys.stderr,
            )
            return EXIT_FAILED
        if validate_main(["--root", str(root)]) != 0:
            print("validation failed; no archive built, no tag created", file=sys.stderr)
            return EXIT_FAILED
        if profile.platform == "github":
            message = (
                "checks passed"
                if args.from_tag
                else f"checks passed; push the tag {args.tag} to run the release workflow"
            )
            print(message, file=sys.stderr)
        else:
            finish(profile, result, Path(args.out), create_tag=not (args.dry_run or args.from_tag), sign=args.sign)
            for file in result.files:
                print(f"wrote {file}", file=sys.stderr)
            print(f"{'would tag' if args.dry_run else 'tagged'} {args.tag}", file=sys.stderr)
    except RECOVERABLE as exc:
        return _fail(str(exc))
    if args.json:
        archive = result.archive.manifest["archive"] if result.archive else None
        print(
            json.dumps(
                {"tag": args.tag, "previous": result.previous, "tagged": result.tagged, "archive": archive}, indent=2
            )
        )
    return EXIT_OK
