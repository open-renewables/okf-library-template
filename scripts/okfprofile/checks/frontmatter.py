"""Check 2: frontmatter against the type's schema (SDD I-03, I-09 ``OKF2xx``)."""

from __future__ import annotations

from typing import Any

from jsonschema.exceptions import ValidationError, best_match
from referencing import Registry

from okfprofile.checks.conformance import datetime_paths
from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.report import Finding


def declared_properties(registry: Registry[Any], schema: dict[str, Any]) -> set[str]:
    """Property names a schema declares, following ``$ref`` and ``allOf`` to other schemas in the registry."""
    names = set(schema.get("properties", {}))
    references = [schema["$ref"]] if isinstance(schema.get("$ref"), str) else []
    for reference in references:
        names |= declared_properties(registry, registry.get_or_retrieve(reference).value.contents)
    for part in schema.get("allOf", []):
        names |= declared_properties(registry, part)
    return names


def _unknown_fields(profile: Profile, concept: Concept, type_name: str) -> list[Finding]:
    declared_type = profile.type_named(type_name)
    assert declared_type is not None  # noqa: S101 - the caller checked the type is declared
    frontmatter = concept.frontmatter or {}
    declared = declared_properties(profile.registry, {"$ref": declared_type.schema_id})
    return [
        Finding.make("OKF203", concept.path, concept.line_of(key), f"unknown frontmatter field `{key}`")
        for key in frontmatter
        if key not in declared
    ]


def _schema_finding(concept: Concept, error: ValidationError, skip: set[tuple[str | int, ...]]) -> list[Finding]:
    path = tuple(error.absolute_path)
    if tuple(path) in skip:
        return []
    if error.validator == "required":
        present = error.instance if isinstance(error.instance, dict) else {}
        return [
            Finding.make("OKF202", concept.path, concept.line_of(*path), f"missing required field `{key}`")
            for key in (error.validator_value if isinstance(error.validator_value, list) else [])
            if key not in present
        ]
    best = best_match([error]) or error
    where = ".".join(str(step) for step in best.absolute_path) or "(frontmatter)"
    return [Finding.make("OKF204", concept.path, concept.line_of(*best.absolute_path), f"{where}: {best.message}")]


def _status_finding(profile: Profile, concept: Concept) -> list[Finding]:
    status = (concept.frontmatter or {}).get("status")
    allowed = [*profile.statuses, *(e.value for e in profile.status_extensions)]
    if isinstance(status, str) and status not in allowed:
        message = f"`status` '{status}' is not declared; allowed: {', '.join(allowed)}"
        return [Finding.make("OKF205", concept.path, concept.line_of("status"), message)]
    return []


def check_frontmatter(profile: Profile, concept: Concept) -> list[Finding]:
    """Run check 2 on one concept.

    A concept whose frontmatter did not parse, or has no `type`, is left to check 1.

    Args:
        profile: The loaded profile.
        concept: The parsed concept.

    Returns:
        Findings for an undeclared type, missing or invalid fields, unknown fields (when the profile
        rejects them) and an undeclared status. A timestamp the datetime rule of check 1 already reports is
        not reported again.
    """
    frontmatter = concept.frontmatter
    type_name = frontmatter.get("type") if frontmatter else None
    if frontmatter is None or not isinstance(type_name, str) or not type_name:
        return []
    if profile.type_named(type_name) is None:
        message = f"type '{type_name}' is not declared in the profile"
        return [Finding.make("OKF201", concept.path, concept.line_of("type"), message)]
    validator = profile.type_validator(type_name, reject_unknown=False)
    skip = set(datetime_paths(frontmatter))
    findings: list[Finding] = []
    for error in sorted(validator.iter_errors(frontmatter), key=lambda e: [str(p) for p in e.absolute_path]):
        findings.extend(_schema_finding(concept, error, skip))
    if profile.rules.reject_unknown_fields:
        findings.extend(_unknown_fields(profile, concept, type_name))
    findings.extend(_status_finding(profile, concept))
    return list(dict.fromkeys(findings))
