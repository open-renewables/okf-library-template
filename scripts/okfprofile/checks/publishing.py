"""Publishing rules for ``stable`` concepts (SDD W-04, FR3.5, FR3.6, FR3.10; I-09 ``OKF7xx``).

Both functions are pure: the approval check takes review data as input and does not fetch it.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from okfprofile.changes import ChangeContext
from okfprofile.codeowners import CodeOwners
from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.report import Finding

STABLE = "stable"


def _is_stable(concept: Concept) -> bool:
    return (concept.frontmatter or {}).get("status") == STABLE


def has_citation(concept: Concept) -> bool:
    """True if the body cites a source: a footnote reference or an external link (SRS FR3.10)."""
    if concept.footnote_refs:
        return True
    return any(urlsplit(link.href).netloc for link in concept.links if link.kind == "link")


def check_citations(profile: Profile, concepts: list[Concept]) -> list[Finding]:
    """``OKF703`` for each ``stable`` concept without a citation, when the profile requires one."""
    if not profile.rules.stable_requires_citation:
        return []
    return [
        Finding.make("OKF703", c.path, c.line_of("status"), "a stable concept cites at least one source in its body")
        for c in concepts
        if _is_stable(c) and not has_citation(c)
    ]


def _precheck_one(profile: Profile, concept: Concept, change: ChangeContext, owners: CodeOwners) -> list[Finding]:
    rules = profile.rules
    line = concept.line_of("status")
    current = {
        r.login.lower()
        for r in change.reviews
        if r.approved
        and r.commit_id == change.head_sha
        and r.login.lower() != change.author.lower()
        and owners.is_owner(r.login, concept.path)
    }
    if len(current) >= rules.stable_approvals:
        return []
    self_ok = (
        rules.allow_recorded_self_approval and not rules.require_non_author_approver and rules.stable_approvals == 1
    )
    if self_ok and owners.is_owner(change.author, concept.path):
        message = "no owner other than the author has approved; the merge will be recorded as self-approved"
        return [Finding.make("OKF702", concept.path, line, message)]
    stale = any(
        r.approved and r.commit_id != change.head_sha and owners.is_owner(r.login, concept.path) for r in change.reviews
    )
    detail = " (an earlier approval was given on a different commit)" if stale else ""
    message = (
        f"a stable concept needs {rules.stable_approvals} approval(s) by a directory owner of the current head{detail}"
    )
    return [Finding.make("OKF701", concept.path, line, message)]


def publishing_precheck(
    profile: Profile, concepts: list[Concept], change: ChangeContext, owners: CodeOwners
) -> list[Finding]:
    """The approval pre-check for concepts the change touches that are ``stable`` (SDD W-04).

    1. Enough approving reviews on the current head from owners of the concept other than the author: pass.
    2. Otherwise, if the author owns the concept and the profile allows recorded self-approval: pass with a notice.
    3. Otherwise fail until an owner approves.

    Args:
        profile: The loaded profile.
        concepts: Every concept of the bundle.
        change: The change proposal, with its reviews.
        owners: Directory owners.

    Returns:
        ``OKF701`` (error) or ``OKF702`` (warning, the self-approval notice) per touched stable concept.
    """
    if not profile.rules.stable_requires_human_approval or not change.reviews_known:
        return []
    touched = set(change.paths)
    findings = []
    for concept in concepts:
        if _is_stable(concept) and concept.path in touched:
            findings.extend(_precheck_one(profile, concept, change, owners))
    return findings
