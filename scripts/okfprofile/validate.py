"""Run the validation checks on a bundle (SDD W-04).

Checks are added here as they are built; each returns findings and none writes to disk.
"""

from __future__ import annotations

from okfprofile.bundle import display_path, load_bundle
from okfprofile.checks import (
    BaseState,
    check_body,
    check_conformance,
    check_frontmatter,
    check_identifiers,
    check_links,
    check_paths,
    check_tags,
)
from okfprofile.config import Profile
from okfprofile.registry import load_registry
from okfprofile.report import Report
from okfprofile.vocab import load_vocabularies


def validate_bundle(profile: Profile, base: BaseState | None = None, approved_move: bool = False) -> Report:
    """Validate every concept of the profile's bundle.

    Args:
        profile: The loaded profile.
        base: The repository at the base commit. Without it the checks that compare against the base (a changed or
            removed ``uid``, a moved concept, a removed anchor) are skipped.
        approved_move: True if the change proposal carries the approved-move label.

    Returns:
        The findings of checks 1 to 4 and 6. A bundle folder that does not exist has no findings.

    Raises:
        okfprofile.registry.RegistryError: If the registry file is invalid.
    """
    report = Report()
    if not profile.bundle_root.is_dir():
        return report
    concepts = load_bundle(profile.bundle_root, profile.root)
    prefix = display_path(profile.bundle_root, profile.root)
    report.extend(check_conformance(profile.bundle_root, concepts, prefix))
    for concept in concepts:
        report.extend(check_frontmatter(profile, concept))
        report.extend(check_body(profile, concept))
    vocabularies, vocabulary_findings = load_vocabularies(profile, concepts)
    report.extend(vocabulary_findings)
    report.extend(check_links(profile, concepts, base.concepts if base else None))
    report.extend(check_tags(profile, concepts, vocabularies))
    report.extend(check_paths(profile, concepts, vocabularies))
    report.extend(check_identifiers(profile, concepts, load_registry(profile.root), base, approved_move))
    return report
