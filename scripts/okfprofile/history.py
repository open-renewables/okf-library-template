"""A concept's revision history, read from its CI-managed section (SDD I-08)."""

from __future__ import annotations

from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.revision import RevisionLine, parse_revision_line


def history_heading(profile: Profile, type_name: str) -> str | None:
    """Heading of the CI-managed section declared for a type, if it has one."""
    declared = profile.type_named(type_name)
    if declared is None or declared.body is None:
        return None
    return next((s.heading for s in declared.body.sections if s.managed_by_ci), None)


def history_lines(profile: Profile, concept: Concept) -> list[RevisionLine]:
    """The valid revision lines of a concept, oldest first; lines that break the grammar are skipped.

    Args:
        profile: The loaded profile.
        concept: The parsed concept.

    Returns:
        The parsed lines of the concept's CI-managed section, or an empty list if its type has none.
    """
    heading = history_heading(profile, str((concept.frontmatter or {}).get("type")))
    section = concept.section(heading) if heading else None
    if section is None:
        return []
    return [line for item in section.items if (line := parse_revision_line(item.text)) is not None]
