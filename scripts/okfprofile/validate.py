"""Run the validation checks on a bundle (SDD W-04).

Each check returns findings and none writes to disk.
"""

from __future__ import annotations

from okfprofile.bundle import display_path, load_bundle
from okfprofile.changes import APPROVED_MOVE_LABEL, ChangeContext, check_change_rules
from okfprofile.checks import (
    BaseState,
    check_body,
    check_citations,
    check_conformance,
    check_frontmatter,
    check_history_appends,
    check_identifiers,
    check_indexes,
    check_links,
    check_paths,
    check_profile_warnings,
    check_tags,
    publishing_precheck,
)
from okfprofile.codeowners import load_codeowners
from okfprofile.config import Profile
from okfprofile.registry import load_registry
from okfprofile.report import Report
from okfprofile.vocab import load_vocabularies


def validate_bundle(profile: Profile, base: BaseState | None = None, change: ChangeContext | None = None) -> Report:
    """Validate a library.

    Args:
        profile: The loaded profile.
        base: The repository at the base commit. Without it the checks that compare against the base (a changed or
            removed ``uid``, a moved concept, a removed anchor, an edited revision history) are skipped.
        change: The change proposal, if there is one. Without it the change rules, the approval pre-check and the
            agent-label warning are skipped.

    Returns:
        The findings of checks 1 to 6, the publishing rules, the change rules and the profile's warnings. A
        bundle folder that does not exist has no findings.

    Raises:
        okfprofile.registry.RegistryError: If the registry file is invalid.
    """
    report = Report()
    owners = load_codeowners(profile.root)
    if change is not None:
        report.extend(check_change_rules(profile, change, owners))
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
    report.extend(check_indexes(profile, concepts))
    approved_move = change is not None and APPROVED_MOVE_LABEL in change.labels
    report.extend(check_identifiers(profile, concepts, load_registry(profile.root), base, approved_move))
    report.extend(check_citations(profile, concepts))
    report.extend(check_history_appends(profile, concepts, base.concepts if base else None, change))
    if change is not None:
        report.extend(publishing_precheck(profile, concepts, change, owners))
    report.extend(check_profile_warnings(profile, concepts, change))
    return report
