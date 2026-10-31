"""Run the validation checks on a bundle (SDD W-04).

Checks are added here as they are built; each returns findings and none writes to disk.
"""

from __future__ import annotations

from okfprofile.bundle import display_path, load_bundle
from okfprofile.checks import check_body, check_conformance, check_frontmatter
from okfprofile.config import Profile
from okfprofile.report import Report


def validate_bundle(profile: Profile) -> Report:
    """Validate every concept of the profile's bundle.

    Args:
        profile: The loaded profile.

    Returns:
        The findings of checks 1 to 3. A bundle folder that does not exist has no findings.
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
    return report
