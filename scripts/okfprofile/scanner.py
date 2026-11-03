"""Scan files for confidentiality markers and secret-shaped strings (SDD C-04, QA-56).

The rules are data in ``profile/scan.yaml``; this module holds none. A match is reported by rule, file and line, and
a secret-shaped match is redacted so the report never repeats it.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ruamel.yaml.error import YAMLError

from okfprofile.document import parse_yaml

CONFIG = "profile/scan.yaml"
SCHEMA = "profile/schemas/scan.schema.json"
DEFAULT_MAX_BYTES = 1_048_576
REDACT_KEEP = 4


class ScanConfigError(Exception):
    """The scan rules cannot be read or do not match their schema."""


@dataclass(frozen=True)
class ScanRule:
    """One scan rule.

    Attributes:
        id: Stable rule name.
        kind: ``marker`` (shown as found) or ``secret`` (redacted).
        pattern: Compiled regular expression.
        description: Text for the report.
    """

    id: str
    kind: str
    pattern: re.Pattern[str]
    description: str = ""


@dataclass(frozen=True)
class ScanConfig:
    """The loaded scan rules."""

    rules: tuple[ScanRule, ...]
    exclude: tuple[str, ...] = ()
    max_file_bytes: int = DEFAULT_MAX_BYTES


@dataclass(frozen=True)
class ScanFinding:
    """A match of a rule in a file.

    Attributes:
        rule: Rule ID.
        kind: Rule kind.
        file: Path relative to the scan root, with forward slashes.
        line: 1-based line number.
        excerpt: The marker text, or the first characters of a secret followed by ``***``.
    """

    rule: str
    kind: str
    file: str
    line: int
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        """The JSON form."""
        return {"rule": self.rule, "kind": self.kind, "file": self.file, "line": self.line, "excerpt": self.excerpt}

    def human(self) -> str:
        """One line for the terminal."""
        return f"{self.file}:{self.line}: {self.rule} ({self.kind}): {self.excerpt}"


@dataclass
class ScanResult:
    """What a scan found and what it did not read."""

    findings: list[ScanFinding] = field(default_factory=list)
    scanned: int = 0
    excluded: int = 0
    skipped_binary: int = 0
    skipped_large: int = 0

    @property
    def ok(self) -> bool:
        """True if there is no finding."""
        return not self.findings

    def to_json(self) -> str:
        """The JSON report."""
        return json.dumps(
            {
                "ok": self.ok,
                "scanned": self.scanned,
                "excluded": self.excluded,
                "skipped_binary": self.skipped_binary,
                "skipped_large": self.skipped_large,
                "findings": [f.to_dict() for f in self.findings],
            },
            indent=2,
        )


def load_scan_config(root: Path) -> ScanConfig:
    """Load ``profile/scan.yaml`` and validate it against its schema.

    Args:
        root: Repository root.

    Returns:
        The rules.

    Raises:
        ScanConfigError: If a file is missing or invalid, or a pattern does not compile.
    """
    try:
        schema = json.loads((root / SCHEMA).read_text(encoding="utf-8"))
        data, _lines = parse_yaml((root / CONFIG).read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"cannot read scan rules: {exc.filename}: {exc.strerror}"
        raise ScanConfigError(msg) from exc
    except (YAMLError, json.JSONDecodeError) as exc:
        msg = f"invalid scan rules: {exc}"
        raise ScanConfigError(msg) from exc
    problems = [
        f"{CONFIG}: {'/'.join(str(p) for p in error.absolute_path) or '(root)'}: {error.message}"
        for error in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    ]
    if problems:
        raise ScanConfigError("\n".join(problems))
    rules = []
    for raw in data["rules"]:
        try:
            pattern = re.compile(raw["pattern"])
        except re.error as exc:
            msg = f"{CONFIG}: rule {raw['id']}: pattern does not compile: {exc}"
            raise ScanConfigError(msg) from exc
        rules.append(ScanRule(raw["id"], raw["kind"], pattern, raw.get("description", "")))
    ids = [r.id for r in rules]
    if len(set(ids)) != len(ids):
        msg = f"{CONFIG}: rule IDs must be unique"
        raise ScanConfigError(msg)
    return ScanConfig(tuple(rules), tuple(data.get("exclude", ())), data.get("max_file_bytes", DEFAULT_MAX_BYTES))


def _excerpt(rule: ScanRule, text: str) -> str:
    return text if rule.kind == "marker" else text[:REDACT_KEEP] + "***"


def scan_text(config: ScanConfig, text: str, name: str) -> list[ScanFinding]:
    """Scan one text.

    Args:
        config: The rules.
        text: File content.
        name: Path to report.

    Returns:
        Findings in line order, at most one per rule and line.
    """
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule in config.rules:
            match = rule.pattern.search(line)
            if match:
                findings.append(ScanFinding(rule.id, rule.kind, name, number, _excerpt(rule, match.group(0))))
    return findings


def is_excluded(config: ScanConfig, relative: str) -> bool:
    """True if ``relative`` matches an exclude pattern (``*`` also matches ``/``)."""
    return any(fnmatch.fnmatch(relative, pattern) for pattern in config.exclude)


def scan_files(config: ScanConfig, root: Path, paths: list[str]) -> ScanResult:
    """Scan files under ``root``.

    Args:
        config: The rules.
        root: Repository root.
        paths: Files relative to ``root``; entries that are not files are ignored.

    Returns:
        The findings and counts of files read and skipped. Binary files (with a NUL byte) and files over
        ``max_file_bytes`` are skipped and counted.
    """
    result = ScanResult()
    for relative in sorted({p.replace("\\", "/") for p in paths}):
        file = root / relative
        if not file.is_file():
            continue
        if is_excluded(config, relative):
            result.excluded += 1
            continue
        if file.stat().st_size > config.max_file_bytes:
            result.skipped_large += 1
            continue
        data = file.read_bytes()
        if b"\0" in data:
            result.skipped_binary += 1
            continue
        result.scanned += 1
        result.findings.extend(scan_text(config, data.decode("utf-8", errors="replace"), relative))
    return result
