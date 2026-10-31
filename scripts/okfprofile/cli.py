"""Command-line entry points behind the thin scripts in ``scripts/`` (SDD C-04).

Every command exits 0 on success, 1 when it finds errors, and 2 when it cannot run (bad arguments, an invalid
profile or registry, git unavailable). Human-readable output goes to standard error; ``--json`` writes a
machine-readable form to standard output.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from okfprofile.bundle import display_path, load_bundle
from okfprofile.changes import APPROVED_MOVE_LABEL, ChangeContext
from okfprofile.checks import BaseState, check_indexes
from okfprofile.config import Profile, ProfileError, load_profile
from okfprofile.document import Concept, load_concept
from okfprofile.gitutil import TOOLING_EXPORT, GitError, changed_paths, export_paths, merge_base, uncommitted_paths
from okfprofile.indexes import folders_of, unexpected_indexes, write_indexes
from okfprofile.registry import (
    Registry,
    RegistryError,
    apply_moves,
    load_registry,
    load_registry_file,
    save_registry,
    uid_of_concept,
)
from okfprofile.report import Report
from okfprofile.scaffold import create_concept, renumber_concept
from okfprofile.validate import validate_bundle

EXIT_OK = 0
EXIT_ERRORS = 1
EXIT_USAGE = 2
RECOVERABLE = (ProfileError, RegistryError, GitError, OSError, ValueError, json.JSONDecodeError)
REGISTRY = "profile/uid-registry.yaml"


def _root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")


def _emit(report: Report, as_json: bool, annotations: bool = False, summary: str | None = None) -> int:
    if report.findings:
        print(report.human(), file=sys.stderr)
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)", file=sys.stderr)
    if as_json:
        print(report.to_json())
    if annotations:
        print("\n".join(report.annotations()))
    if summary:
        Path(summary).write_text(report.summary(), encoding="utf-8", newline="\n")
    return EXIT_OK if report.ok else EXIT_ERRORS


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_USAGE


def _validate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="validate_profile.py", description="Validate the knowledge bundle.")
    _root_argument(parser)
    parser.add_argument("files", nargs="*", help="report only findings in these files")
    parser.add_argument("--changed", action="store_true", help="report only findings in files changed since HEAD")
    parser.add_argument("--base", metavar="REF", help="compare with this branch or commit (the merge base is used)")
    parser.add_argument(
        "--base-dir", metavar="DIR", help="compare with a folder holding the base's bundle and registry"
    )
    parser.add_argument("--tooling-from", metavar="REF", help="run the tooling and profile of REF on this working tree")
    parser.add_argument("--change", metavar="FILE", help="JSON file describing the change proposal")
    parser.add_argument("--label", action="append", default=[], help="a label on the change proposal (repeatable)")
    parser.add_argument(
        "--fix-registry", action="store_true", help="record moved concepts (needs --label approved-move)"
    )
    parser.add_argument("--json", action="store_true", help="write the findings as JSON to standard output")
    parser.add_argument(
        "--annotations", action="store_true", help="write GitHub workflow annotations to standard output"
    )
    parser.add_argument("--summary", metavar="FILE", help="write a Markdown summary to FILE")
    return parser


def _base_from_dir(profile: Profile, directory: Path) -> BaseState:
    bundle = profile.bundle_root.relative_to(profile.root)
    registry_file = directory / REGISTRY
    registry = load_registry_file(registry_file, profile.root) if registry_file.is_file() else Registry()
    return BaseState(load_bundle(directory / bundle, directory), registry)


def _export_base(profile: Profile, ref: str, directory: Path) -> list[str]:
    commit = merge_base(profile.root, ref)
    bundle = profile.bundle_root.relative_to(profile.root).as_posix()
    export_paths(profile.root, commit, [bundle, REGISTRY], directory)
    return changed_paths(profile.root, commit)


def _context(
    args: argparse.Namespace, profile: Profile, stack: contextlib.ExitStack
) -> tuple[BaseState | None, ChangeContext | None]:
    base: BaseState | None = None
    paths: list[str] = []
    if args.base_dir:
        base = _base_from_dir(profile, Path(args.base_dir))
    elif args.base:
        directory = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        paths = _export_base(profile, args.base, directory)
        base = _base_from_dir(profile, directory)
    change: ChangeContext | None = None
    if args.change:
        change = ChangeContext.from_file(Path(args.change))
    elif args.base or args.label:
        change = ChangeContext(paths=paths)
    if change is not None:
        change.labels |= set(args.label)
        if not change.paths:
            change.paths = paths
    return base, change


def _only_changed(args: argparse.Namespace, root: Path, report: Report) -> Report:
    if not (args.changed or args.files):
        return report
    wanted = {Path(f).as_posix() for f in args.files}
    if args.changed:
        wanted |= set(uncommitted_paths(root))
    kept = [f for f in report.findings if f.file in wanted or f.file == "(change)"]
    return Report(kept)


def _fix_registry(args: argparse.Namespace, profile: Profile) -> int:
    if APPROVED_MOVE_LABEL not in args.label:
        return _fail(f"--fix-registry records moves, which need --label {APPROVED_MOVE_LABEL}")
    concepts = load_bundle(profile.bundle_root, profile.root)
    uids = {c.concept_id: u for c in concepts if (u := uid_of_concept(c))}
    before = load_registry(profile.root)
    after = apply_moves(before, uids)
    save_registry(profile.root, after)
    moved = sorted(uid for uid in after.entries if after.entries[uid] != before.entries.get(uid))
    print(f"{len(moved)} registry entr{'y' if len(moved) == 1 else 'ies'} updated", file=sys.stderr)
    return EXIT_OK


def _stage_tooling(args: argparse.Namespace, profile: Profile, scratch: Path) -> tuple[Path, Path]:
    """Lay out the base's tooling with this working tree's content, and the base's content to compare with."""
    tooling, base_dir = scratch / "tooling", scratch / "base"
    tooling.mkdir()
    base_dir.mkdir()
    if not export_paths(profile.root, args.tooling_from, list(TOOLING_EXPORT), tooling):
        msg = f"{args.tooling_from} has no tooling to run"
        raise ValueError(msg)
    bundle = profile.bundle_root.relative_to(profile.root).as_posix()
    if (profile.root / bundle).is_dir():
        shutil.copytree(profile.root / bundle, tooling / bundle)
    if (profile.root / REGISTRY).is_file():
        shutil.copy2(profile.root / REGISTRY, tooling / REGISTRY)
    return tooling, base_dir


def _run_with_tooling(args: argparse.Namespace, root: Path) -> int:
    """Run the tooling and profile of another ref on this working tree (SDD AD-18)."""
    profile = load_profile(root)
    with tempfile.TemporaryDirectory() as name:
        scratch = Path(name)
        tooling, base_dir = _stage_tooling(args, profile, scratch)
        paths = _export_base(profile, args.base, base_dir) if args.base else []
        change = ChangeContext.from_file(Path(args.change)) if args.change else ChangeContext()
        change.labels |= set(args.label)
        change.paths = change.paths or paths
        change_file = scratch / "change.json"
        change_file.write_text(json.dumps(change.to_dict()), encoding="utf-8")
        command = [sys.executable, str(tooling / "scripts" / "validate_profile.py"), "--root", str(tooling)]
        command += ["--change", str(change_file)]
        command += ["--base-dir", str(base_dir)] if args.base else []
        command += [flag for flag, on in (("--json", args.json), ("--annotations", args.annotations)) if on]
        command += ["--summary", args.summary] if args.summary else []
        return subprocess.run(command, cwd=tooling, check=False).returncode  # noqa: S603 - runs the base's own script


def validate_main(argv: list[str] | None = None) -> int:
    """``validate_profile.py``: run the validation checks and report the findings."""
    args = _validate_parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.tooling_from:
            return _run_with_tooling(args, root)
        profile = load_profile(root)
        if args.fix_registry:
            return _fix_registry(args, profile)
        with contextlib.ExitStack() as stack:
            base, change = _context(args, profile, stack)
            report = validate_bundle(profile, base, change)
    except RECOVERABLE as exc:
        return _fail(str(exc))
    return _emit(_only_changed(args, root, report), args.json, args.annotations, args.summary)


def build_indexes_main(argv: list[str] | None = None) -> int:
    """``build_indexes.py``: write the generated indexes, or check that they are fresh with ``--check``."""
    parser = argparse.ArgumentParser(prog="build_indexes.py", description="Generate index.md files.")
    _root_argument(parser)
    parser.add_argument("concepts", nargs="*", help="regenerate only the folders that hold these concept IDs")
    parser.add_argument("--check", action="store_true", help="report differences without writing")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        profile = load_profile(root)
        concepts = load_bundle(profile.bundle_root, root)
        if args.check:
            return _emit(Report(check_indexes(profile, concepts)), args.json)
        folders = _folders_for(concepts, args.concepts)
        written = write_indexes(profile, concepts, folders)
        if folders is None:
            for extra in unexpected_indexes(profile, concepts):
                (profile.bundle_root / extra).unlink()
    except RECOVERABLE as exc:
        return _fail(str(exc))
    shown = [display_path(p, root) for p in written]
    print("\n".join(shown), file=sys.stderr)
    if args.json:
        print(json.dumps({"written": shown}))
    return EXIT_OK


def _folders_for(concepts: list[Concept], ids: list[str]) -> set[str] | None:
    if not ids:
        return None
    chosen = [c for c in concepts if c.concept_id in set(ids)]
    unknown = set(ids) - {c.concept_id for c in chosen}
    if unknown:
        msg = f"no such concept: {', '.join(sorted(unknown))}"
        raise ValueError(msg)
    return folders_of(chosen)


def new_concept_main(argv: list[str] | None = None) -> int:
    """``new_concept.py``: create a concept with the next ``uid`` and register it."""
    parser = argparse.ArgumentParser(prog="new_concept.py", description="Create a concept.")
    _root_argument(parser)
    parser.add_argument("type", help="declared concept type, such as Item")
    parser.add_argument("path", help="concept ID: path under the bundle root without .md")
    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        profile = load_profile(root)
        file = create_concept(profile, args.type, args.path, args.title, args.description)
    except RECOVERABLE as exc:
        return _fail(str(exc))
    uid = uid_of_concept(load_concept(file)) or ""
    print(f"created {display_path(file, root)} ({uid})", file=sys.stderr)
    if args.json:
        print(json.dumps({"path": display_path(file, root), "uid": uid}))
    return EXIT_OK


def renumber_main(argv: list[str] | None = None) -> int:
    """``renumber.py``: give a concept whose ``uid`` clashes with another the next free number."""
    parser = argparse.ArgumentParser(prog="renumber.py", description="Renumber a concept with a clashing uid.")
    _root_argument(parser)
    parser.add_argument("concept", help="concept ID to renumber")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    try:
        old, new = renumber_concept(load_profile(Path(args.root).resolve()), args.concept)
    except RECOVERABLE as exc:
        return _fail(str(exc))
    print(f"{args.concept}: {old} -> {new}", file=sys.stderr)
    if args.json:
        print(json.dumps({"concept": args.concept, "old": old, "new": new}))
    return EXIT_OK
