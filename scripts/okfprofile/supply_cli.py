"""Command-line entry points for the supply-chain and scan tasks (SDD C-04, I-16; QA-56, QA-74).

``scan.py``, ``check_licences.py``, ``audit.py`` and ``export_requirements.py`` are thin wrappers over these
functions. Exit codes follow ``okfprofile.cli``: 0 success, 1 findings, 2 cannot run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from okfprofile.gitutil import GitError, git
from okfprofile.licences import CONSTRAINTS, PolicyError, audit_exceptions, check_repository
from okfprofile.scanner import ScanConfigError, load_scan_config, scan_files

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

GITLEAKS_ARGS = ("git", "--pre-commit", "--redact", "--staged", "--verbose")
EXPORTS = {
    "requirements/validate.txt": ("--only-group", "validate"),
    "requirements/dev.txt": ("--all-groups",),
    "requirements/site-mkdocs.txt": ("--only-group", "site-mkdocs"),
    "requirements/site-zensical.txt": ("--only-group", "site-zensical"),
}
EXPORT_BASE = ("--frozen", "--format", "requirements-txt", "--no-emit-project")


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return EXIT_USAGE


def _root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="repository root (default: the current folder)")


def _tracked(root: Path) -> list[str]:
    return [p for p in git(root, "ls-files", "-z").split("\0") if p]


def _changed(root: Path) -> list[str]:
    names = git(root, "diff", "--name-only", "-z", "--diff-filter=ACMR", "HEAD").split("\0")
    untracked = git(root, "ls-files", "-z", "--others", "--exclude-standard").split("\0")
    return sorted({n for n in names + untracked if n})


def run_gitleaks(root: Path) -> int | None:
    """Run the gitleaks CLI on the staged changes if it is installed.

    Args:
        root: Repository root.

    Returns:
        gitleaks' exit code, or None if gitleaks is not installed (a notice is printed).
    """
    binary = shutil.which("gitleaks")
    if binary is None:
        print("notice: gitleaks is not installed; skipped (CI runs it)", file=sys.stderr)
        return None
    done = subprocess.run([binary, *GITLEAKS_ARGS], cwd=root, check=False)  # noqa: S603 - fixed arguments
    return done.returncode


def scan_main(argv: Sequence[str] | None = None) -> int:
    """``scan.py``: scan files for confidentiality markers and secret-shaped strings."""
    parser = argparse.ArgumentParser(prog="scan.py", description="Scan files for markers and secret-shaped strings.")
    _root(parser)
    parser.add_argument("files", nargs="*", help="files to scan (default: files changed since HEAD)")
    parser.add_argument("--all", action="store_true", help="scan every tracked file")
    parser.add_argument("--gitleaks", action="store_true", help="also run gitleaks on the staged changes if installed")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        config = load_scan_config(root)
        paths = args.files or (_tracked(root) if args.all else _changed(root))
        result = scan_files(config, root, paths)
    except (ScanConfigError, GitError, OSError) as exc:
        return _fail(str(exc))
    for finding in result.findings:
        print(finding.human(), file=sys.stderr)
    print(
        f"{len(result.findings)} finding(s) in {result.scanned} file(s); {result.excluded} excluded, "
        f"{result.skipped_binary} binary and {result.skipped_large} large skipped",
        file=sys.stderr,
    )
    if args.json:
        print(result.to_json())
    status = EXIT_OK if result.ok else EXIT_FINDINGS
    if args.gitleaks:
        code = run_gitleaks(root)
        if code:
            status = EXIT_FINDINGS
    return status


def licences_main(argv: Sequence[str] | None = None) -> int:
    """``check_licences.py``: check installed, locked packages against the allowlist in ``constraints.md``."""
    parser = argparse.ArgumentParser(prog="check_licences.py", description="Check dependency licences.")
    _root(parser)
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    try:
        report = check_repository(Path(args.root).resolve())
    except (PolicyError, OSError, ValueError) as exc:
        return _fail(str(exc))
    for finding in report.findings:
        print(finding.human(), file=sys.stderr)
    if report.not_installed:
        print(f"notice: not installed here, so not checked: {', '.join(report.not_installed)}", file=sys.stderr)
    print(f"{len(report.findings)} finding(s) in {report.checked} package(s)", file=sys.stderr)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "checked": report.checked,
                    "not_installed": report.not_installed,
                    "findings": [
                        {"package": f.package, "version": f.version, "licence": f.licence, "reason": f.reason}
                        for f in report.findings
                    ],
                },
                indent=2,
            )
        )
    return EXIT_OK if report.ok else EXIT_FINDINGS


def audit_command(root: Path) -> list[str]:
    """The ``pip-audit`` command for the locked set, with the exceptions recorded in ``constraints.md``.

    Args:
        root: Repository root.

    Returns:
        The argument list.
    """
    ignored = audit_exceptions((root / CONSTRAINTS).read_text(encoding="utf-8"))
    command = ["uvx", "pip-audit", "--disable-pip", "--no-deps", "-r", "requirements/dev.txt"]
    for advisory in ignored:
        command += ["--ignore-vuln", advisory]
    return command


def audit_main(argv: Sequence[str] | None = None) -> int:
    """``audit.py``: run pip-audit on the exported lock (needs network and ``uvx``)."""
    parser = argparse.ArgumentParser(
        prog="audit.py", description="Audit locked dependencies for known vulnerabilities."
    )
    _root(parser)
    parser.add_argument("--print-command", action="store_true", help="print the command and exit")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        command = audit_command(root)
    except (PolicyError, OSError) as exc:
        return _fail(str(exc))
    if args.print_command:
        print(" ".join(command))
        return EXIT_OK
    if shutil.which("uvx") is None:
        return _fail("uvx is not installed (it comes with uv)")
    return subprocess.run(command, cwd=root, check=False).returncode  # noqa: S603 - fixed arguments


def export_text(root: Path, target: str) -> str:
    """The hash-locked requirements text for ``target``, exported from ``uv.lock``.

    Args:
        root: Repository root.
        target: A key of ``EXPORTS``.

    Returns:
        The file content, LF line endings.

    Raises:
        OSError: If ``uv`` cannot be run.
        ValueError: If ``uv export`` fails.
    """
    flags = EXPORTS[target]
    done = subprocess.run(  # noqa: S603 - fixed arguments
        ["uv", "export", *EXPORT_BASE, *flags],  # noqa: S607 - uv is found on PATH by design
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if done.returncode:
        msg = f"uv export failed: {done.stderr.strip()}"
        raise ValueError(msg)
    body = [line for line in done.stdout.replace("\r\n", "\n").splitlines() if not line.startswith("#    uv export")]
    body = [line for line in body if line != "# This file was autogenerated by uv via the following command:"]
    header = (
        "# Exported from uv.lock by scripts/export_requirements.py. Do not edit.\n"
        f"# uv export {' '.join((*EXPORT_BASE, *flags))}\n"
    )
    return header + "\n".join(body) + "\n"


def export_main(argv: Sequence[str] | None = None) -> int:
    """``export_requirements.py``: write, or with ``--check`` verify, the hash-locked requirements files."""
    parser = argparse.ArgumentParser(prog="export_requirements.py", description="Export the lock with hashes.")
    _root(parser)
    parser.add_argument("--check", action="store_true", help="fail if a committed file differs from the lock")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    stale = []
    try:
        for target in EXPORTS:
            text = export_text(root, target)
            file = root / target
            current = file.read_text(encoding="utf-8").replace("\r\n", "\n") if file.is_file() else None
            if args.check:
                if current != text:
                    stale.append(target)
            elif current != text:
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text, encoding="utf-8", newline="\n")
                print(f"wrote {target}", file=sys.stderr)
    except (OSError, ValueError) as exc:
        return _fail(str(exc))
    if stale:
        print(f"out of date with uv.lock: {', '.join(stale)}; run `uv run poe export`", file=sys.stderr)
        return EXIT_FINDINGS
    return EXIT_OK


CONFIG_SCHEMAS = (
    ("vendor.github-issue-forms", ".github/ISSUE_TEMPLATE", "*.yml", ("config.yml",)),
    ("vendor.github-issue-config", ".github/ISSUE_TEMPLATE", "config.yml", ()),
    ("vendor.github-workflows", ".github/workflows", "*.yml", ()),
    ("vendor.dependabot", ".github", "dependabot.yml", ()),
)


def config_commands(root: Path) -> list[list[str]]:
    """The ``check-jsonschema`` commands for the configuration files that exist under ``root``.

    Args:
        root: Repository root.

    Returns:
        One command per built-in schema that has at least one file; nothing is run for a missing folder.
    """
    commands = []
    for schema, folder, pattern, skip in CONFIG_SCHEMAS:
        files = sorted(p.relative_to(root).as_posix() for p in (root / folder).glob(pattern) if p.name not in skip)
        if files:
            commands.append(["uvx", "check-jsonschema", "--builtin-schema", schema, *files])
    return commands


def check_config_main(argv: Sequence[str] | None = None) -> int:
    """``check_config.py``: validate workflows, issue forms and Dependabot configuration (needs ``uvx``, network)."""
    parser = argparse.ArgumentParser(prog="check_config.py", description="Check CI configuration against its schemas.")
    _root(parser)
    parser.add_argument("--print-command", action="store_true", help="print the commands and exit")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    commands = config_commands(root)
    if args.print_command:
        print("\n".join(" ".join(c) for c in commands))
        return EXIT_OK
    if shutil.which("uvx") is None:
        return _fail("uvx is not installed (it comes with uv)")
    status = EXIT_OK
    for command in commands:
        if subprocess.run(command, cwd=root, check=False).returncode:  # noqa: S603 - fixed arguments
            status = EXIT_FINDINGS
    return status
