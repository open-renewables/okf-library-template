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
CHECK_2 = "2 Frontmatter schema"
CHECK_3 = "3 Body structure"

CODES: dict[str, CodeInfo] = _define(
    CodeInfo("OKF101", Level.ERROR, CHECK_1, "Frontmatter block missing, not on line 1, or not closed"),
    CodeInfo("OKF102", Level.ERROR, CHECK_1, "Frontmatter is not valid YAML"),
    CodeInfo("OKF103", Level.ERROR, CHECK_1, "Frontmatter is not a mapping"),
    CodeInfo("OKF104", Level.ERROR, CHECK_1, "Required `type` key missing or empty"),
    CodeInfo("OKF111", Level.WARNING, CHECK_1, "Legacy OKF v0.1 construct"),
    CodeInfo("OKF113", Level.WARNING, CHECK_1, "Actor does not follow the OKF actor convention"),
    CodeInfo("OKF116", Level.WARNING, CHECK_1, "`usage_count` has no window, or a footnote matches no `sources[].id`"),
    CodeInfo("OKF117", Level.WARNING, CHECK_1, "Reserved file (`index.md`, `log.md`) breaks OKF section 8, 9 or 12"),
    CodeInfo("OKF118", Level.WARNING, CHECK_1, "Attested Computation contract field is missing or dangling"),
    CodeInfo("OKF119", Level.WARNING, CHECK_1, "okf-skills reported a message this tool does not map"),
    CodeInfo("OKF120", Level.ERROR, CHECK_1, "Timestamp is not an ISO 8601 datetime with an explicit UTC offset"),
    CodeInfo("OKF201", Level.ERROR, CHECK_2, "Concept type is not declared in the profile"),
    CodeInfo("OKF202", Level.ERROR, CHECK_2, "Required frontmatter field missing"),
    CodeInfo("OKF203", Level.ERROR, CHECK_2, "Unknown frontmatter field (the profile rejects them)"),
    CodeInfo("OKF204", Level.ERROR, CHECK_2, "Frontmatter value does not satisfy the type schema"),
    CodeInfo("OKF205", Level.ERROR, CHECK_2, "`status` is not declared in the profile"),
    CodeInfo("OKF301", Level.ERROR, CHECK_3, "Title heading missing, repeated, or different from `title`"),
    CodeInfo("OKF302", Level.ERROR, CHECK_3, "Required body section missing"),
    CodeInfo("OKF303", Level.ERROR, CHECK_3, "Body section out of the declared order"),
    CodeInfo("OKF304", Level.ERROR, CHECK_3, "Body section not declared for the type"),
    CodeInfo("OKF305", Level.ERROR, CHECK_3, "Body section appears more than once"),
    CodeInfo("OKF306", Level.ERROR, CHECK_3, "Body section is empty and does not hold the placeholder"),
    CodeInfo("OKF307", Level.ERROR, CHECK_3, "List item does not match its section format"),
    CodeInfo("OKF308", Level.ERROR, CHECK_3, "List item value is not among the format's allowed values"),
    CodeInfo("OKF309", Level.ERROR, CHECK_3, "Required child of a format item missing"),
    CodeInfo("OKF310", Level.ERROR, CHECK_3, "Child of a format item unexpected, repeated or out of order"),
    CodeInfo("OKF311", Level.ERROR, CHECK_3, "Child value is not among the allowed values"),
    CodeInfo("OKF312", Level.ERROR, CHECK_3, "Nested list item is not indented four spaces"),
    CodeInfo("OKF313", Level.ERROR, CHECK_3, "Raw HTML in prose; write it as a code span or escape it"),
    CodeInfo("OKF314", Level.ERROR, CHECK_3, "CI-managed section holds something other than valid revision lines"),
)
