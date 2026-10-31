"""Registry of validation finding codes (SDD I-09).

A code is stable once defined and is never reused. The registry is the single list that
``Finding`` checks against and that ``docs/development/architecture/finding-codes.md`` mirrors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Level(StrEnum):
    """Severity of a finding."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class CodeInfo:
    """One finding code.

    Attributes:
        code: Stable identifier, ``OKF`` plus three digits; the first digit is the I-09 range.
        level: Default level of findings raised with this code.
        check: Name of the I-09 check that owns the code.
        title: One-line description.
    """

    code: str
    level: Level
    check: str
    title: str


def _define(*infos: CodeInfo) -> dict[str, CodeInfo]:
    table: dict[str, CodeInfo] = {}
    for info in infos:
        if info.code in table:
            msg = f"duplicate finding code {info.code}"
            raise ValueError(msg)
        table[info.code] = info
    return table


CHECK_1 = "1 OKF conformance"

CODES: dict[str, CodeInfo] = _define(
    CodeInfo("OKF101", Level.ERROR, CHECK_1, "Frontmatter block missing, not on line 1, or not closed"),
    CodeInfo("OKF102", Level.ERROR, CHECK_1, "Frontmatter is not valid YAML"),
    CodeInfo("OKF103", Level.ERROR, CHECK_1, "Frontmatter is not a mapping"),
)
