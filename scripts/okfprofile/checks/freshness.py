"""Check 5: index freshness (SDD W-04, I-07; I-09 ``OKF5xx``)."""

from __future__ import annotations

import posixpath
from collections import Counter

from okfprofile.bundle import display_path
from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.indexes import INDEX, expected_indexes, unexpected_indexes
from okfprofile.report import Finding


def check_indexes(profile: Profile, concepts: list[Concept]) -> list[Finding]:
    """Compare the committed indexes with what the generator would write.

    Args:
        profile: The loaded profile.
        concepts: Every concept of the bundle.

    Returns:
        ``OKF501`` for a missing index, ``OKF502`` for one that differs (stale or edited by hand), ``OKF503`` for an
        index in a folder without concepts, and ``OKF504`` (warning) for a folder over the profile's size limit.
    """
    findings = []
    for relative, text in expected_indexes(profile, concepts).items():
        file = profile.bundle_root / relative
        shown = display_path(file, profile.root)
        if not file.is_file():
            findings.append(Finding.make("OKF501", shown, 0, "the folder has no index.md; run build_indexes.py"))
        elif file.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n") != text:
            message = "the index is out of date or was edited; run build_indexes.py"
            findings.append(Finding.make("OKF502", shown, 0, message))
    for relative in unexpected_indexes(profile, concepts):
        shown = display_path(profile.bundle_root / relative, profile.root)
        findings.append(Finding.make("OKF503", shown, 0, "this folder holds no concepts, so it has no index"))
    limit = profile.index.max_concepts_per_directory
    counts = Counter(posixpath.dirname(c.concept_id) for c in concepts)
    for folder, count in sorted(counts.items()):
        if count > limit:
            shown = display_path(profile.bundle_root / posixpath.join(folder, INDEX), profile.root)
            message = f"the folder holds {count} concepts; the profile suggests at most {limit}"
            findings.append(Finding.make("OKF504", shown, 0, message))
    return findings
