"""Findings and their output formats: JSON, GitHub workflow annotations, Markdown summary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from okfprofile.codes import CODES, Level


@dataclass(frozen=True)
class Finding:
    """One validation finding.

    Attributes:
        code: A code defined in ``okfprofile.codes``.
        level: ``error`` or ``warning``.
        file: Path of the file, relative to the repository root where known.
        line: 1-based line, or 0 when the finding concerns the whole file.
        message: Human-readable explanation.
    """

    code: str
    level: Level
    file: str
    line: int
    message: str

    @classmethod
    def make(cls, code: str, file: str, line: int, message: str, level: Level | None = None) -> Finding:
        """Create a finding, taking the level from the code's default unless given.

        Args:
            code: A code defined in ``okfprofile.codes``.
            file: Path of the file concerned.
            line: 1-based line, or 0 for the whole file.
            message: Human-readable explanation.
            level: Override of the code's default level.

        Returns:
            The finding.

        Raises:
            ValueError: If ``code`` is not defined.
        """
        info = CODES.get(code)
        if info is None:
            msg = f"undefined finding code {code}"
            raise ValueError(msg)
        return cls(code, level or info.level, file, line, message)


def _escape_data(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")


@dataclass
class Report:
    """A collection of findings with the three output formats of SDD I-09."""

    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        """Append one finding."""
        self.findings.append(finding)

    def extend(self, findings: list[Finding]) -> None:
        """Append several findings."""
        self.findings.extend(findings)

    @property
    def errors(self) -> list[Finding]:
        """Findings at error level, in report order."""
        return [f for f in self.findings if f.level is Level.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        """Findings at warning level, in report order."""
        return [f for f in self.findings if f.level is Level.WARNING]

    @property
    def ok(self) -> bool:
        """True when there is no error (warnings do not fail a run)."""
        return not self.errors

    def sorted(self) -> list[Finding]:
        """Findings ordered by file, line, code, so local and CI output compare equal."""
        return sorted(self.findings, key=lambda f: (f.file, f.line, f.code, f.message))

    def to_json(self) -> str:
        """Machine-readable form: findings and counts."""
        payload = {
            "findings": [asdict(f) for f in self.sorted()],
            "counts": {"error": len(self.errors), "warning": len(self.warnings)},
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def annotations(self) -> list[str]:
        """GitHub workflow commands, one per finding."""
        lines = []
        for f in self.sorted():
            props = f"file={_escape_property(f.file)}"
            if f.line:
                props += f",line={f.line}"
            props += f",title={_escape_property(f.code)}"
            lines.append(f"::{f.level.value} {props}::{_escape_data(f.message)}")
        return lines

    def summary(self) -> str:
        """Markdown job summary."""
        if not self.findings:
            return "No findings.\n"
        rows = ["| Level | Code | File | Line | Message |", "| --- | --- | --- | --- | --- |"]
        for f in self.sorted():
            message = f.message.replace("|", "\\|").replace("\n", " ")
            rows.append(f"| {f.level.value} | {f.code} | `{f.file}` | {f.line or ''} | {message} |")
        head = f"{len(self.errors)} error(s), {len(self.warnings)} warning(s).\n\n"
        return head + "\n".join(rows) + "\n"

    def human(self) -> str:
        """Plain text for a terminal, one line per finding."""
        return "\n".join(f"{f.file}:{f.line or 1}: {f.level.value} {f.code} {f.message}" for f in self.sorted())
