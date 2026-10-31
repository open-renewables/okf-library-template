"""Controlled vocabularies (SDD I-05, SRS FR2.9).

A vocabulary is one concept per tag namespace, at ``<bundle>/<vocabularies.path>/<namespace>.md``. Each value is
one bullet, `` - `value`: one-line definition ``. When the namespace declares kinds, values sit under one H2
per kind and are unique across kinds if the namespace says so. The concept is the authoritative list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from okfprofile.config import NamespaceDecl, Profile
from okfprofile.document import Concept, ListItem
from okfprofile.report import Finding

VALUE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass
class Vocabulary:
    """The values of one namespace.

    Attributes:
        namespace: Namespace name.
        values: Definition of each value, by value.
        kinds: Kind of each value (None for a namespace without kinds), by value.
    """

    namespace: str
    values: dict[str, str] = field(default_factory=dict)
    kinds: dict[str, str | None] = field(default_factory=dict)


def vocabulary_id(profile: Profile, namespace: str) -> str:
    """Concept ID of a namespace's vocabulary concept, relative to the bundle root."""
    return f"{profile.vocab_path.strip('/')}/{namespace}"


def _parse_value(item: ListItem) -> tuple[str, str] | None:
    text = item.text
    if not text.startswith("`"):
        return None
    close = text.find("`", 1)
    if close == -1:
        return None
    rest = text[close + 1 :]
    if not rest.startswith(": ") or not rest[2:].strip():
        return None
    return text[1:close], rest[2:].strip()


def _managed_ranges(profile: Profile, concept: Concept) -> list[range]:
    managed = {s.heading for t in profile.types if t.body for s in t.body.sections if s.managed_by_ci}
    return [range(s.heading.line, s.end_line + 1) for s in concept.sections if s.heading.text in managed]


def _items_by_kind(profile: Profile, concept: Concept) -> list[tuple[str | None, ListItem]]:
    ranges = _managed_ranges(profile, concept)
    sections = {s.heading.line: s for s in concept.sections}
    pairs: list[tuple[str | None, ListItem]] = []
    for item in concept.top_items:
        if any(item.line in r for r in ranges):
            continue
        kind = None
        for section in sections.values():
            if section.heading.line < item.line <= section.end_line:
                kind = section.heading.text
        pairs.append((kind, item))
    return pairs


def _read_namespace(profile: Profile, concept: Concept, namespace: NamespaceDecl) -> tuple[Vocabulary, list[Finding]]:
    vocabulary = Vocabulary(namespace.name)
    findings: list[Finding] = []

    def problem(line: int, message: str) -> None:
        findings.append(Finding.make("OKF407", concept.path, line, message))

    declared = (concept.frontmatter or {}).get("namespace")
    if declared != namespace.name:
        problem(concept.line_of("namespace"), f"`namespace` must be '{namespace.name}' (found {declared!r})")
    first_kind: dict[str, str | None] = {}
    for kind, item in _items_by_kind(profile, concept):
        parsed = _parse_value(item)
        if parsed is None:
            problem(item.line, "a vocabulary value is written `value`: one-line definition")
            continue
        value, definition = parsed
        if not VALUE_PATTERN.match(value):
            problem(item.line, f"value '{value}' must be lower-case letters, digits and hyphens")
        if namespace.kinds and kind is None:
            problem(item.line, f"value '{value}' is not under a kind heading")
        if value in first_kind and (first_kind[value] == kind or namespace.values_unique_across_kinds):
            where = "twice" if first_kind[value] == kind else f"under two kinds ('{first_kind[value]}' and '{kind}')"
            problem(item.line, f"value '{value}' appears {where}")
            continue
        first_kind.setdefault(value, kind)
        vocabulary.values[value] = definition
        vocabulary.kinds[value] = kind if namespace.kinds else None
    return vocabulary, findings


def load_vocabularies(profile: Profile, concepts: list[Concept]) -> tuple[dict[str, Vocabulary], list[Finding]]:
    """Read the vocabulary concept of every declared namespace.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.

    Returns:
        The vocabularies by namespace, and findings (``OKF407``) for a missing or malformed vocabulary concept.
    """
    by_id = {c.concept_id: c for c in concepts}
    vocabularies: dict[str, Vocabulary] = {}
    findings: list[Finding] = []
    for namespace in profile.namespaces:
        concept_id = vocabulary_id(profile, namespace.name)
        concept = by_id.get(concept_id)
        if concept is None:
            file = f"{profile.bundle_root.relative_to(profile.root).as_posix()}/{concept_id}.md"
            message = f"namespace '{namespace.name}' has no vocabulary concept (expected {concept_id}.md)"
            findings.append(Finding.make("OKF407", file, 0, message))
            continue
        vocabulary, problems = _read_namespace(profile, concept, namespace)
        vocabularies[namespace.name] = vocabulary
        findings.extend(problems)
    return vocabularies, findings
