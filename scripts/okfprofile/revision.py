"""Revision-history lines (SDD I-08): the line grammar.

One line per merged change is appended to a concept's *Revision history* section by CI::

    - <date> · author @<login> · <approval> · <change>[ · full-review][ · agent-drafted]

The grammar and the trust-tier rules are here. Reading pull requests or commits and writing lines come in a
later build phase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Literal

SEPARATOR = " · "
LOGIN = r"[A-Za-z0-9][A-Za-z0-9._+-]*"

_AUTHOR = re.compile(rf"author @(?P<login>{LOGIN})")
_APPROVED = re.compile(rf"approved(?P<stale> \(stale\))? @(?P<login>{LOGIN}) \((?P<owner>owner|non-owner)\)")
_SELF = re.compile(r"self-approved \((?P<owner>owner|non-owner)\)")
_UNAPPROVED = re.compile(rf"merged without approval @(?P<login>{LOGIN})")
_PR = re.compile(r"PR #(?P<number>[0-9]+)")
_COMMIT = re.compile(r"commit (?P<sha>[0-9a-f]{7})")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

Approval = Literal["approved", "approved-stale", "self-approved", "merged-without-approval"]
Change = Literal["pr", "pr-none", "commit"]


@dataclass(frozen=True)
class RevisionLine:
    """A parsed revision line.

    Attributes:
        date: Merge date (UTC).
        author: Login of the author.
        approval: Approval outcome.
        approver: Login of the approver (or of the merger when merged without approval); None for a
            self-approval.
        owner: True if the approver (or self-approving author) owns the concept, False if not, None when the
            outcome carries no owner status.
        change: Kind of change reference.
        reference: Pull request number or short commit hash; None for ``PR none``.
        full_review: True if the line carries ``full-review``.
        agent_drafted: True if the line carries ``agent-drafted``.
    """

    date: date
    author: str
    approval: Approval
    approver: str | None
    owner: bool | None
    change: Change
    reference: str | None
    full_review: bool
    agent_drafted: bool


def _approval(text: str) -> tuple[Approval, str | None, bool | None] | None:
    if m := _APPROVED.fullmatch(text):
        kind: Approval = "approved-stale" if m["stale"] else "approved"
        return kind, m["login"], m["owner"] == "owner"
    if m := _SELF.fullmatch(text):
        return "self-approved", None, m["owner"] == "owner"
    if m := _UNAPPROVED.fullmatch(text):
        return "merged-without-approval", m["login"], None
    return None


def _change(text: str) -> tuple[Change, str | None] | None:
    if text == "PR none":
        return "pr-none", None
    if m := _PR.fullmatch(text):
        return "pr", m["number"]
    if m := _COMMIT.fullmatch(text):
        return "commit", m["sha"]
    return None


def _parse_date(text: str) -> date | None:
    if not _DATE.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_revision_line(text: str) -> RevisionLine | None:
    """Parse the text of one revision-history list item.

    Args:
        text: The item's first line with the list marker removed.

    Returns:
        The parsed line, or None if it does not follow the I-08 grammar.
    """
    parts = text.strip().split(SEPARATOR)
    minimum = 4
    if len(parts) < minimum:
        return None
    when = _parse_date(parts[0])
    author = _AUTHOR.fullmatch(parts[1])
    approval = _approval(parts[2])
    change = _change(parts[3])
    flags = parts[4:]
    if when is None or author is None or approval is None or change is None:
        return None
    if flags not in ([], ["full-review"], ["agent-drafted"], ["full-review", "agent-drafted"]):
        return None
    return RevisionLine(
        when,
        author["login"],
        approval[0],
        approval[1],
        approval[2],
        change[0],
        change[1],
        "full-review" in flags,
        "agent-drafted" in flags,
    )


class Tier(StrEnum):
    """Trust tier of a revision or a concept, lowest first (OKF section 5.3)."""

    UNVERIFIED = "unverified"
    MACHINE_CONFIRMED = "machine-confirmed"
    HUMAN_REVIEWED = "human-reviewed"


_ORDER = {Tier.UNVERIFIED: 0, Tier.MACHINE_CONFIRMED: 1, Tier.HUMAN_REVIEWED: 2}


@dataclass(frozen=True)
class TierResult:
    """A concept's trust tier.

    Attributes:
        tier: The tier.
        self_approved: True if the tier is human-reviewed and some revision in its window was self-approved.
    """

    tier: Tier
    self_approved: bool = False

    @property
    def label(self) -> str:
        """The tier as shown in indexes: ``human-reviewed (self)`` when self-approval contributes."""
        return (
            f"{self.tier.value} (self)" if self.tier is Tier.HUMAN_REVIEWED and self.self_approved else self.tier.value
        )


def owner_approved(line: RevisionLine) -> bool:
    """True if an owner approved the revision on the merged head (a stale approval does not count)."""
    return line.owner is True and line.approval in {"approved", "self-approved"}


def revision_tier(line: RevisionLine, require_non_author_approver: bool = False) -> tuple[Tier, bool]:
    """Tier of one revision (SDD I-08) and whether it rests on a self-approval.

    Args:
        line: The parsed revision line.
        require_non_author_approver: The profile setting; when true, a self-approval is machine-confirmed.

    Returns:
        The tier, and True if it is human-reviewed by self-approval.
    """
    machine = (Tier.MACHINE_CONFIRMED, False)
    if line.agent_drafted or line.approval in {"approved-stale", "merged-without-approval"}:
        return machine
    if line.approval == "approved":
        return (Tier.HUMAN_REVIEWED, False) if line.owner else machine
    if line.owner and not require_non_author_approver:
        return Tier.HUMAN_REVIEWED, True
    return machine


def concept_tier(lines: list[RevisionLine], require_non_author_approver: bool = False) -> TierResult:
    """A concept's tier: the lowest revision tier since the latest owner-approved full review.

    Args:
        lines: The concept's revision lines, oldest first.
        require_non_author_approver: The profile setting.

    Returns:
        The tier; unverified if there are no revisions.
    """
    if not lines:
        return TierResult(Tier.UNVERIFIED)
    start = max((i for i, line in enumerate(lines) if line.full_review and owner_approved(line)), default=0)
    results = [revision_tier(line, require_non_author_approver) for line in lines[start:]]
    lowest = min((tier for tier, _ in results), key=_ORDER.__getitem__)
    return TierResult(lowest, lowest is Tier.HUMAN_REVIEWED and any(self for _, self in results))
