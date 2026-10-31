"""Check 6: identifiers and the registry (SDD I-06, SRS FR1.3 to FR1.7; I-09 ``OKF6xx``)."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from okfprofile.config import Profile
from okfprofile.document import Concept
from okfprofile.registry import Registry, uid_of_concept
from okfprofile.report import Finding

REGISTRY_FILE = "profile/uid-registry.yaml"


@dataclass
class BaseState:
    """The repository at the base commit, for the checks that compare against it.

    Attributes:
        concepts: The bundle's concepts at the base.
        registry: The registry at the base.
    """

    concepts: list[Concept] = field(default_factory=list)
    registry: Registry = field(default_factory=Registry)


@dataclass(frozen=True)
class _Held:
    concept: Concept
    uid: str


def _shape_findings(profile: Profile, concepts: list[Concept]) -> tuple[list[Finding], list[_Held]]:
    findings: list[Finding] = []
    held: list[_Held] = []
    for concept in concepts:
        declared = profile.type_named(str((concept.frontmatter or {}).get("type")))
        if declared is None:
            continue
        uid = (concept.frontmatter or {}).get("uid")
        if uid is None:
            findings.append(Finding.make("OKF601", concept.path, 1, "the concept has no `uid`"))
        elif not isinstance(uid, str) or not re.fullmatch(rf"{declared.uid_prefix}-[0-9]{{4}}", uid):
            message = f"`uid` {uid!r} must look like {declared.uid_prefix}-0001 for type '{declared.name}'"
            findings.append(Finding.make("OKF602", concept.path, concept.line_of("uid"), message))
        else:
            held.append(_Held(concept, uid))
    return findings, held


def _duplicates(held: list[_Held]) -> list[Finding]:
    users: dict[str, list[Concept]] = defaultdict(list)
    for item in held:
        users[item.uid].append(item.concept)
    return [
        Finding.make("OKF603", c.path, c.line_of("uid"), f"`uid` {uid} is also used by {others}")
        for uid, concepts in users.items()
        if len(concepts) > 1
        for c in concepts
        for others in [", ".join(o.concept_id for o in concepts if o is not c)]
    ]


def _registry_findings(
    held: list[_Held], registry: Registry, base: BaseState | None, approved_move: bool
) -> list[Finding]:
    findings = []
    counts = Counter(i.uid for i in held)
    for item in (i for i in held if counts[i.uid] == 1):
        concept, entry = item.concept, registry.get(item.uid)
        line = concept.line_of("uid")
        if entry is None:
            findings.append(Finding.make("OKF604", concept.path, line, f"`uid` {item.uid} is not in the registry"))
            continue
        if entry.type != (concept.frontmatter or {}).get("type"):
            message = f"the registry records type '{entry.type}' for {item.uid}"
            findings.append(Finding.make("OKF608", concept.path, line, message))
        if entry.path != concept.concept_id:
            message = f"the registry has {item.uid} at '{entry.path}' but the concept is at '{concept.concept_id}'"
            findings.append(Finding.make("OKF605", concept.path, line, message))
            continue
        earlier = base.registry.get(item.uid) if base else None
        if earlier and earlier.path != concept.concept_id and not (approved_move and earlier.path in entry.moved_from):
            reason = "the old path is not recorded in the registry" if approved_move else "the move is not approved"
            message = f"{item.uid} moved from '{earlier.path}' and {reason}"
            findings.append(Finding.make("OKF605", concept.path, line, message))
    return findings


def _base_findings(held: list[_Held], registry: Registry, base: BaseState) -> list[Finding]:
    findings = []
    head_by_id = {i.concept.concept_id: i for i in held}
    head_uids = {i.uid for i in held}
    for old in base.concepts:
        old_uid = uid_of_concept(old)
        now = head_by_id.get(old.concept_id)
        if old_uid is None:
            continue
        if now is not None and now.uid != old_uid:
            message = f"`uid` changed from {old_uid} to {now.uid}"
            findings.append(Finding.make("OKF606", now.concept.path, now.concept.line_of("uid"), message))
        elif now is None and old_uid not in head_uids:
            message = f"{old_uid} ({old.concept_id}) is gone; concepts are deprecated, not deleted"
            findings.append(Finding.make("OKF607", old.path, 0, message))
    findings.extend(
        Finding.make("OKF607", REGISTRY_FILE, 0, f"registry entry {uid} was removed; entries are never removed")
        for uid in base.registry.entries
        if registry.get(uid) is None
    )
    return findings


def _orphans(concepts: list[Concept], registry: Registry, base: BaseState | None) -> list[Finding]:
    present = {uid for c in concepts if (uid := uid_of_concept(c))}
    known_before = set(base.registry.entries) if base else set()
    return [
        Finding.make("OKF608", REGISTRY_FILE, 0, f"registry entry {uid} ({entry.path}) matches no concept")
        for uid, entry in registry.entries.items()
        if uid not in present and uid not in known_before
    ]


def check_identifiers(
    profile: Profile,
    concepts: list[Concept],
    registry: Registry,
    base: BaseState | None = None,
    approved_move: bool = False,
) -> list[Finding]:
    """Run check 6.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.
        registry: The registry at the head.
        base: The repository at the base commit; without it, the checks that compare against the base are skipped.
        approved_move: True if the change proposal carries the approved-move label.

    Returns:
        Findings for a missing, malformed, duplicated, unregistered, changed or removed ``uid``, and for a path
        that differs from the registry without an approved move.
    """
    findings, held = _shape_findings(profile, concepts)
    findings.extend(_duplicates(held))
    findings.extend(_registry_findings(held, registry, base, approved_move))
    if base is not None:
        findings.extend(_base_findings(held, registry, base))
    findings.extend(_orphans(concepts, registry, base))
    return findings
