"""Check 4, tags, vocabularies and paths (SDD I-02, I-05; I-09 ``OKF405`` to ``OKF410``)."""

from __future__ import annotations

from okfprofile.bundle import glob_match
from okfprofile.config import PathRule, Profile
from okfprofile.document import Concept
from okfprofile.report import Finding
from okfprofile.vocab import Vocabulary


def _tags(concept: Concept) -> list[tuple[int, str]]:
    raw = (concept.frontmatter or {}).get("tags")
    if not isinstance(raw, list):
        return []
    return [(i, tag) for i, tag in enumerate(raw) if isinstance(tag, str)]


def _split(tag: str) -> tuple[str, str]:
    namespace, _, value = tag.partition(":")
    return namespace, value


def check_tags(profile: Profile, concepts: list[Concept], vocabularies: dict[str, Vocabulary]) -> list[Finding]:
    """Check each tag's shape, namespace and membership of its vocabulary.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.
        vocabularies: The vocabularies, by namespace.

    Returns:
        ``OKF405`` for a tag that does not match the pattern or names an undeclared namespace, and ``OKF406`` for
        a value missing from its vocabulary.
    """
    declared = {n.name for n in profile.namespaces}
    findings = []
    for concept in concepts:
        for index, tag in _tags(concept):
            line = concept.line_of("tags", index)
            namespace, value = _split(tag)
            if not profile.tag_pattern.match(tag):
                message = f"tag '{tag}' does not match the tag pattern {profile.tag_pattern.pattern}"
                findings.append(Finding.make("OKF405", concept.path, line, message))
            elif namespace not in declared:
                message = f"tag '{tag}' names namespace '{namespace}', which has no vocabulary"
                findings.append(Finding.make("OKF405", concept.path, line, message))
            elif namespace in vocabularies and value not in vocabularies[namespace].values:
                message = f"'{value}' is not in the '{namespace}' vocabulary"
                findings.append(Finding.make("OKF406", concept.path, line, message))
    return findings


def _applies(rule: PathRule, concept: Concept) -> bool:
    type_name = (concept.frontmatter or {}).get("type")
    return not rule.types or type_name in rule.types


def _rule_findings(rule: PathRule, concept: Concept, vocabularies: dict[str, Vocabulary]) -> list[Finding]:
    folders = concept.concept_id.split("/")[:-1]
    values = [v for ns, v in (_split(t) for _, t in _tags(concept)) if ns == rule.namespace]
    line = concept.line_of("tags")
    if rule.kind == "tag_equals_segment":
        segment = rule.params["segment"]
        if segment >= len(folders):
            message = f"the path has no folder at index {segment} for the '{rule.namespace}' tag"
            return [Finding.make("OKF408", concept.path, line, message)]
        if values != [folders[segment]]:
            message = f"the '{rule.namespace}:' tag must be '{rule.namespace}:{folders[segment]}' (the folder name)"
            return [Finding.make("OKF408", concept.path, line, message)]
    elif rule.kind == "tag_count":
        low, high = rule.params["min"], rule.params["max"]
        if not low <= len(values) <= high:
            message = f"{len(values)} '{rule.namespace}:' tags found; between {low} and {high} are required"
            return [Finding.make("OKF408", concept.path, line, message)]
    elif rule.kind == "tag_required_if_segment_kind":
        segment = rule.params["segment"]
        vocabulary = vocabularies.get(rule.params["vocabulary"])
        folder = folders[segment] if segment < len(folders) else None
        if vocabulary and folder and vocabulary.kinds.get(folder) == rule.params["kind_value"] and not values:
            message = f"a '{rule.namespace}:' tag is required under a '{folder}' folder"
            return [Finding.make("OKF408", concept.path, line, message)]
    elif rule.kind == "tag_not_equal_segment":
        named = {folders[i] for i in rule.params["segments"] if i < len(folders)}
        return [
            Finding.make("OKF409", concept.path, line, f"tag '{rule.namespace}:{v}' restates a folder name")
            for v in values
            if v in named
        ]
    return []


def check_paths(profile: Profile, concepts: list[Concept], vocabularies: dict[str, Vocabulary]) -> list[Finding]:
    """Apply the profile's path rules and each type's declared paths.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.
        vocabularies: The vocabularies, by namespace.

    Returns:
        ``OKF408`` for a violated path rule, ``OKF409`` (warning) for a tag that restates a folder, and ``OKF410``
        for a concept outside the paths its type declares.
    """
    findings = []
    for concept in concepts:
        declared = profile.type_named(str((concept.frontmatter or {}).get("type")))
        if declared is None:
            continue
        file = f"{concept.concept_id}.md"
        if declared.paths and not any(glob_match(pattern, file) for pattern in declared.paths):
            message = f"type '{declared.name}' belongs at {', '.join(declared.paths)}; this file is at {file}"
            findings.append(Finding.make("OKF410", concept.path, 1, message))
        for rule in profile.path_rules:
            if _applies(rule, concept):
                findings.extend(_rule_findings(rule, concept, vocabularies))
    return findings
