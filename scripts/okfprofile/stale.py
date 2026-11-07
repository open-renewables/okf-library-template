"""Concepts that are due for review (SRS FR3.11, SDD W-06, DDR QA-49).

A concept is stale at the earlier of its own ``stale_after`` instant and the profile's default interval after its
last revision, so ``stale_after`` can only bring review forward. A concept with no revision has no baseline for the
interval: it is reported as unverified, and only its ``stale_after`` can make it stale. Deprecated concepts are left
out, because nothing is left to review in them.
"""

from __future__ import annotations

import calendar
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.history import history_lines
from okfprofile.report import Finding

DURATION = re.compile(r"^P(?:(?P<y>\d+)Y)?(?:(?P<m>\d+)M)?(?:(?P<w>\d+)W)?(?:(?P<d>\d+)D)?$")
MARKER = "<!-- stale-report -->"
DEPRECATED = "deprecated"
BASIS_STALE_AFTER = "stale_after"
BASIS_INTERVAL = "default interval"


class DurationError(ValueError):
    """An ISO 8601 duration that this tool does not read (only years, months, weeks and days)."""


def add_duration(start: date, text: str) -> date:
    """Add an ISO 8601 duration of years, months, weeks and days to a date.

    Months and years are calendar months; a day that does not exist in the target month moves to its last day.

    Args:
        start: The date.
        text: A duration such as ``P2Y``, ``P6M`` or ``P1Y2M10D``.

    Returns:
        The later date.

    Raises:
        DurationError: If ``text`` is not such a duration, or is empty (``P``).
    """
    match = DURATION.match(text)
    if match is None or text == "P" or not any(match.groupdict().values()):
        msg = f"cannot read duration '{text}' (use years, months, weeks and days, for example P2Y)"
        raise DurationError(msg)
    years, months, weeks, days = (int(match[k] or 0) for k in ("y", "m", "w", "d"))
    month_index = start.month - 1 + years * 12 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(weeks=weeks, days=days)


def _stale_after(concept: Concept) -> datetime | None:
    raw = (concept.frontmatter or {}).get(BASIS_STALE_AFTER)
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo is not None else None


@dataclass(frozen=True)
class StaleEntry:
    """A concept that is past its review date.

    Attributes:
        concept_id: Path under the bundle root without ``.md``.
        path: Repository-relative path.
        uid: The concept's ``uid``.
        status: The concept's ``status``.
        due: The instant it became stale (the earlier limit), in UTC.
        basis: ``stale_after`` or ``default interval``.
        last_revision: Date of its latest revision line, if any.
    """

    concept_id: str
    path: str
    uid: str
    status: str
    due: datetime
    basis: str
    last_revision: date | None

    def to_dict(self) -> dict[str, Any]:
        """The JSON form."""
        return {
            "concept": self.concept_id,
            "path": self.path,
            "uid": self.uid,
            "status": self.status,
            "due": self.due.isoformat().replace("+00:00", "Z"),
            "basis": self.basis,
            "last_revision": self.last_revision.isoformat() if self.last_revision else None,
        }


@dataclass
class StaleReport:
    """The result of a staleness check.

    Attributes:
        now: The instant the check was made against (UTC).
        stale: Concepts past their review date, most overdue first.
        unrevised: Concepts with no revision line (unverified), for information.
        gaps: Merged changes without a revision line (``OKF901``), when ``--check-since`` was given.
    """

    now: datetime
    stale: list[StaleEntry] = field(default_factory=list)
    unrevised: list[str] = field(default_factory=list)
    gaps: list[Finding] | None = None

    def to_json(self) -> str:
        """The JSON report."""
        return json.dumps(
            {
                "as_of": self.now.isoformat().replace("+00:00", "Z"),
                "stale": [e.to_dict() for e in self.stale],
                "unrevised": self.unrevised,
                "revision_gaps": None
                if self.gaps is None
                else [{"file": f.file, "line": f.line, "message": f.message} for f in self.gaps],
            },
            indent=2,
        )

    def to_markdown(self) -> str:
        """The body of the tracking issue; it starts with a marker the workflow uses to find the issue."""
        lines = [MARKER, "# Review report", "", f"As of {self.now.date().isoformat()}.", "", "## Stale concepts", ""]
        if self.stale:
            lines += [
                "| Concept | uid | Status | Stale since | Basis | Last revision |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            lines += [
                f"| `{e.path}` | {e.uid} | {e.status} | {e.due.date().isoformat()} | {e.basis} | "
                f"{e.last_revision.isoformat() if e.last_revision else 'none'} |"
                for e in self.stale
            ]
        else:
            lines.append("None.")
        lines += ["", "## Concepts with no revision (unverified)", ""]
        lines += [f"- `{path}`" for path in self.unrevised] or ["None."]
        if self.gaps is not None:
            lines += ["", "## Merged changes without a revision line", ""]
            lines += [f"- `{f.file}`: {f.message}" for f in self.gaps] or ["None."]
        return "\n".join(lines) + "\n"

    def human(self) -> str:
        """A few lines for the terminal."""
        rows = [f"{e.path}: stale since {e.due.date()} ({e.basis})" for e in self.stale]
        rows += [f"{path}: no revision yet" for path in self.unrevised]
        return "\n".join(rows)


def find_stale(profile: Profile, concepts: list[Concept], now: datetime | None = None) -> StaleReport:
    """Find the concepts that are past their review date.

    Args:
        profile: The loaded profile (``rules.stale_after_default``).
        concepts: Every concept of the bundle.
        now: The instant to judge by; default is the current time. It needs an offset.

    Returns:
        The report: stale concepts most overdue first, and concepts with no revision.

    Raises:
        DurationError: If the profile's default interval cannot be read.
    """
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    report = StaleReport(moment)
    for concept in concepts:
        meta = concept.frontmatter or {}
        status = str(meta.get("status", ""))
        if status == DEPRECATED:
            continue
        lines = history_lines(profile, concept)
        last = max((line.date for line in lines), default=None)
        limits: list[tuple[datetime, str]] = []
        if last is not None:
            limit = add_duration(last, profile.rules.stale_after_default)
            limits.append((datetime(limit.year, limit.month, limit.day, tzinfo=UTC), BASIS_INTERVAL))
        explicit = _stale_after(concept)
        if explicit is not None:
            limits.append((explicit, BASIS_STALE_AFTER))
        if last is None:
            report.unrevised.append(concept.path)
        if limits:
            due, basis = min(limits, key=lambda item: (item[0], item[1] != BASIS_STALE_AFTER))
            if due <= moment:
                report.stale.append(
                    StaleEntry(concept.concept_id, concept.path, str(meta.get("uid", "")), status, due, basis, last)
                )
    report.stale.sort(key=lambda e: (e.due, e.concept_id))
    return report
