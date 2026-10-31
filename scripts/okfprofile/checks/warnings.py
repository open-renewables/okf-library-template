"""Profile-declared warnings (SDD I-02; I-09 ``OKF8xx``). The kinds are a closed set implemented here."""

from __future__ import annotations

import posixpath
from collections import Counter

from okfprofile.bundle import display_path
from okfprofile.changes import ChangeContext
from okfprofile.config import Profile, WarningDecl
from okfprofile.document import Concept
from okfprofile.report import Finding


def _tag_values(concept: Concept, namespace: str) -> list[str]:
    tags = (concept.frontmatter or {}).get("tags")
    pairs = (t.partition(":") for t in tags if isinstance(t, str)) if isinstance(tags, list) else ()
    return [value for ns, _, value in pairs if ns == namespace]


def _tag_restates_folder(decl: WarningDecl, concepts: list[Concept]) -> list[Finding]:
    findings: list[Finding] = []
    for concept in concepts:
        folders = concept.concept_id.split("/")[:-1]
        named = {folders[i] for i in decl.params["segments"] if i < len(folders)}
        findings.extend(
            Finding.make(
                "OKF801",
                concept.path,
                concept.line_of("tags"),
                f"[{decl.id}] tag '{decl.params['namespace']}:{v}' restates a folder name",
            )
            for v in _tag_values(concept, decl.params["namespace"])
            if v in named
        )
    return findings


def _agent_label(profile: Profile, decl: WarningDecl, change: ChangeContext | None) -> list[Finding]:
    if change is None or not change.agent_markers or profile.rules.agent_label in change.labels:
        return []
    message = f"[{decl.id}] agent markers were found but the change lacks the '{profile.rules.agent_label}' label"
    return [Finding.make("OKF802", "(change)", 0, message)]


def _placeholder_left(profile: Profile, decl: WarningDecl, concepts: list[Concept]) -> list[Finding]:
    findings: list[Finding] = []
    for concept in concepts:
        declared = profile.type_named(str((concept.frontmatter or {}).get("type")))
        if (concept.frontmatter or {}).get("status") != "stable" or declared is None or declared.body is None:
            continue
        for heading in decl.params["sections"]:
            section = concept.section(heading)
            if section is None:
                continue
            only_placeholder = [p.text for p in section.paragraphs] == [
                declared.body.empty_placeholder
            ] and not section.items
            if not section.has_content or only_placeholder:
                message = f"[{decl.id}] section '{heading}' of a stable concept still holds the placeholder"
                findings.append(Finding.make("OKF803", concept.path, section.heading.line, message))
    return findings


def _directory_size(profile: Profile, decl: WarningDecl, concepts: list[Concept]) -> list[Finding]:
    limit = decl.params["max"]
    counts = Counter(posixpath.dirname(c.concept_id) for c in concepts)
    return [
        Finding.make(
            "OKF804",
            display_path(profile.bundle_root / folder, profile.root),
            0,
            f"[{decl.id}] the folder holds {count} concepts; the limit is {limit}",
        )
        for folder, count in sorted(counts.items())
        if count > limit
    ]


def check_profile_warnings(profile: Profile, concepts: list[Concept], change: ChangeContext | None) -> list[Finding]:
    """Run each enabled warning the profile declares.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.
        change: The change proposal, for the warning that needs one.

    Returns:
        Findings at warning level, never errors.
    """
    findings: list[Finding] = []
    for decl in profile.warnings:
        if not decl.enabled:
            continue
        if decl.kind == "tag_not_equal_segment":
            findings.extend(_tag_restates_folder(decl, concepts))
        elif decl.kind == "agent_label_missing":
            findings.extend(_agent_label(profile, decl, change))
        elif decl.kind == "stable_section_nonempty":
            findings.extend(_placeholder_left(profile, decl, concepts))
        elif decl.kind == "directory_size":
            findings.extend(_directory_size(profile, decl, concepts))
    return findings
