"""The revision history may only grow (SRS FR3.4; I-09 ``OKF315``).

The section is written by CI. Against the base, every line already there must still be there, unchanged and in
order, and a new concept starts with none, unless the change is a revision-writer commit.
"""

from __future__ import annotations

from okfprofile.bundle import BaseIndex
from okfprofile.changes import ChangeContext
from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.history import history_heading
from okfprofile.report import Finding


def _lines(profile: Profile, concept: Concept) -> list[str] | None:
    heading = history_heading(profile, str((concept.frontmatter or {}).get("type")))
    section = concept.section(heading) if heading else None
    return None if section is None else [item.text for item in section.items]


def check_history_appends(
    profile: Profile, concepts: list[Concept], base: list[Concept] | None, change: ChangeContext | None
) -> list[Finding]:
    """Report revision lines that were edited, removed or written by hand.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts at the head.
        base: The bundle's concepts at the base; without them the check is skipped.
        change: The change proposal; a revision-writer commit is exempt.

    Returns:
        ``OKF315`` for each concept whose history does not extend the base's.
    """
    if base is None or (change is not None and change.revision_bot):
        return []
    earlier = BaseIndex(base)
    findings = []
    for concept in concepts:
        head = _lines(profile, concept)
        if head is None:
            continue
        previous = earlier.find(concept)
        before = (_lines(profile, previous) if previous else None) or []
        if head[: len(before)] != before:
            message = "revision lines of the base were edited or removed; only CI appends to this section"
        elif previous is None and head:
            message = "a new concept starts with an empty revision history; CI writes the first line after merge"
        elif len(head) > len(before):
            message = "revision lines were added by hand; CI writes them after merge"
        else:
            continue
        findings.append(Finding.make("OKF315", concept.path, concept.line_of("type"), message))
    return findings
