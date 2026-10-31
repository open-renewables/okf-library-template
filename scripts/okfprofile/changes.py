"""A change proposal as the checks see it, and the change rules (SDD AD-18, W-04; I-09 ``OKF0xx``).

The platform adapter (a later build phase) fills a ``ChangeContext`` from a pull request or a commit; the
command line can read one from a JSON file. Nothing here calls a platform.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from okfprofile.codeowners import CodeOwners
from okfprofile.config import Profile
from okfprofile.report import Finding

APPROVED_MOVE_LABEL = "approved-move"
REGISTRY_PATH = "profile/uid-registry.yaml"
DECISIONS_PATH = "DECISIONS.md"
TOOLING_PREFIXES = ("scripts/", "profile/", ".github/", "tests/", "docs/", "requirements/")
TOOLING_FILES = frozenset({"pyproject.toml", "uv.lock", ".python-version", ".pre-commit-config.yaml", "mkdocs.yml"})


@dataclass(frozen=True)
class Review:
    """The latest review by one reviewer.

    Attributes:
        login: Reviewer login.
        approved: True if the review approves.
        commit_id: Commit the review was given on.
    """

    login: str
    approved: bool
    commit_id: str


@dataclass
class ChangeContext:
    """What the checks need to know about a change proposal.

    Attributes:
        paths: Files the change touches, relative to the repository root.
        labels: Labels on the change.
        author: Author login.
        head_sha: The head commit that will be merged.
        reviews: Latest review per reviewer.
        agent_markers: True if commit trailers or the description indicate agent assistance.
        revision_bot: True if this is a revision-writer commit, which may append revision lines.
        reviews_known: True if ``reviews`` holds real review data; the approval pre-check is skipped otherwise.
    """

    paths: list[str] = field(default_factory=list)
    labels: set[str] = field(default_factory=set)
    author: str = ""
    head_sha: str = ""
    reviews: list[Review] = field(default_factory=list)
    agent_markers: bool = False
    revision_bot: bool = False
    reviews_known: bool = False

    def to_dict(self) -> dict[str, Any]:
        """The JSON form read back by ``from_dict``."""
        data: dict[str, Any] = {
            "paths": self.paths,
            "labels": sorted(self.labels),
            "author": self.author,
            "head_sha": self.head_sha,
            "agent_markers": self.agent_markers,
            "revision_bot": self.revision_bot,
        }
        if self.reviews_known:
            data["reviews"] = [
                {"login": r.login, "approved": r.approved, "commit_id": r.commit_id} for r in self.reviews
            ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChangeContext:
        """Build a context from parsed JSON; unknown keys are ignored."""
        reviews = [Review(str(r["login"]), bool(r["approved"]), str(r["commit_id"])) for r in data.get("reviews", [])]
        return cls(
            paths=[str(p).replace("\\", "/") for p in data.get("paths", [])],
            labels={str(label) for label in data.get("labels", [])},
            author=str(data.get("author", "")),
            head_sha=str(data.get("head_sha", "")),
            reviews=reviews,
            agent_markers=bool(data.get("agent_markers", False)),
            revision_bot=bool(data.get("revision_bot", False)),
            reviews_known="reviews" in data,
        )

    @classmethod
    def from_file(cls, file: Path) -> ChangeContext:
        """Read a context from a JSON file."""
        return cls.from_dict(json.loads(file.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class ChangeSet:
    """Changed paths sorted by kind (SDD section 6, tooling paths).

    Attributes:
        tooling: Tooling paths: scripts, profile (except the registry), workflows, tests, docs, lock and configuration.
        content: The bundle and the registry.
        other: Everything else, such as README.md.
    """

    tooling: list[str]
    content: list[str]
    other: list[str]


def classify(paths: list[str], bundle_root: str) -> ChangeSet:
    """Sort changed paths into tooling, content and other.

    Args:
        paths: Repository-relative paths with forward slashes.
        bundle_root: The bundle folder, relative to the repository root.

    Returns:
        The three groups. ``profile/uid-registry.yaml`` counts as content because every new concept updates it.
    """
    tooling, content, other = [], [], []
    for path in paths:
        if path == REGISTRY_PATH or path.startswith(f"{bundle_root.strip('/')}/"):
            content.append(path)
        elif path in TOOLING_FILES or path.startswith(TOOLING_PREFIXES):
            tooling.append(path)
        else:
            other.append(path)
    return ChangeSet(tooling, content, other)


def maintainer_logins(profile: Profile, owners: CodeOwners) -> set[str]:
    """Logins that count as maintainers: the profile's map plus the owners of ``profile/profile.yaml``."""
    named = {login.lower() for login in profile.maintainers}
    return named | {o.lower().removeprefix("@") for o in owners.owners_for("profile/profile.yaml")}


def _maintainer_approved(profile: Profile, change: ChangeContext, owners: CodeOwners) -> bool:
    maintainers = maintainer_logins(profile, owners)
    approving = {r.login.lower() for r in change.reviews if r.approved and r.commit_id == change.head_sha}
    if (approving - {change.author.lower()}) & maintainers:
        return True
    rules = profile.rules
    self_ok = rules.allow_recorded_self_approval and not rules.require_non_author_approver
    return self_ok and change.author.lower() in maintainers


def check_change_rules(profile: Profile, change: ChangeContext, owners: CodeOwners) -> list[Finding]:
    """Apply the mixed-change rule (SDD AD-18).

    A change proposal changes tooling or content, not both, unless it carries the migration label. A migration
    needs a maintainer's approval (on a single-maintainer library, the recorded self-approval) and a change to
    ``DECISIONS.md``.

    Args:
        profile: The loaded profile.
        change: The change proposal.
        owners: Directory owners.

    Returns:
        ``OKF001`` for a mixed change without the label, ``OKF002`` for a migration without a maintainer's approval,
        ``OKF003`` for a migration that leaves ``DECISIONS.md`` unchanged.
    """
    bundle = profile.bundle_root.relative_to(profile.root).as_posix()
    grouped = classify(change.paths, bundle)
    if not (grouped.tooling and grouped.content):
        return []
    if profile.rules.migration_label not in change.labels:
        message = (
            f"the change touches tooling ({grouped.tooling[0]}) and content ({grouped.content[0]}); "
            f"split it, or label it '{profile.rules.migration_label}'"
        )
        return [Finding.make("OKF001", grouped.tooling[0], 0, message)]
    findings = []
    if not _maintainer_approved(profile, change, owners):
        message = "a profile migration needs a maintainer's approval of the current head"
        findings.append(Finding.make("OKF002", grouped.tooling[0], 0, message))
    if DECISIONS_PATH not in change.paths:
        findings.append(
            Finding.make("OKF003", grouped.tooling[0], 0, f"a profile migration needs an entry in {DECISIONS_PATH}")
        )
    return findings
