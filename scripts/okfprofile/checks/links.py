"""Check 4, links, anchors and path fields (SDD I-01, AD-14, ADR-005; I-09 ``OKF401`` to ``OKF404``, ``OKF411``,
``OKF412``).

Internal links are relative. A target must exist in the bundle and a fragment must match a heading's automatic
slug or an explicit ``<a id>`` anchor, compared without regard to case because GitHub lower-cases explicit ids.
Frontmatter path fields resolve by OKF v0.3 §6.2: from the concept's own folder, or from the bundle root when
they start with ``/`` (body links stay relative, ADR-005).
"""

from __future__ import annotations

import posixpath
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from okfprofile.bundle import BaseIndex
from okfprofile.config import Profile
from okfprofile.document import Concept, KeyPath, parse_concept
from okfprofile.report import Finding

URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class _Targets:
    """Look up link targets in the bundle, parsing a Markdown target at most once."""

    def __init__(self, bundle_root: Path, concepts: list[Concept]) -> None:
        self.bundle_root = bundle_root
        self.parsed: dict[str, Concept] = {f"{c.concept_id}.md": c for c in concepts}

    def resolve(self, relative: str) -> str | None:
        """The bundle-relative file a path names, or None if it names nothing (a folder means its index)."""
        file = self.bundle_root / relative
        if file.is_dir():
            index = posixpath.join(relative, "index.md")
            return index if (self.bundle_root / index).is_file() else None
        return relative if relative in self.parsed or file.is_file() else None

    def anchors(self, relative: str) -> set[str] | None:
        """Lower-case anchors of a Markdown file; None for a file that is not Markdown."""
        if not relative.endswith(".md"):
            return None
        if relative not in self.parsed:
            self.parsed[relative] = parse_concept((self.bundle_root / relative).read_text(encoding="utf-8"), relative)
        return anchors_of(self.parsed[relative])


def anchors_of(concept: Concept) -> set[str]:
    """Heading slugs and explicit anchor ids of a concept, lower-cased."""
    return {h.slug.lower() for h in concept.headings} | {a.id.lower() for a in concept.anchors}


def _link_findings(concept: Concept, targets: _Targets) -> list[Finding]:
    findings = []
    own = f"{concept.concept_id}.md"
    for link in concept.links:
        parts = urlsplit(link.href)
        if parts.scheme or parts.netloc:
            continue
        if link.href.startswith("/"):
            message = f"link '{link.href}' starts with '/'; internal links are relative (ADR-005)"
            findings.append(Finding.make("OKF401", concept.path, link.line, message))
            continue
        path = unquote(parts.path)
        relative = posixpath.normpath(posixpath.join(posixpath.dirname(own), path)) if path else own
        if relative.startswith(".."):
            message = f"link '{link.href}' points outside the bundle"
            findings.append(Finding.make("OKF402", concept.path, link.line, message))
            continue
        target = targets.resolve(relative)
        if target is None:
            findings.append(
                Finding.make("OKF402", concept.path, link.line, f"link target '{link.href}' does not exist")
            )
            continue
        found = targets.anchors(target) if parts.fragment else None
        if found is not None and unquote(parts.fragment).lower() not in found:
            message = f"'#{parts.fragment}' matches no heading or anchor in {target}"
            findings.append(Finding.make("OKF403", concept.path, link.line, message))
    return findings


def path_fields(frontmatter: dict[str, Any]) -> list[tuple[KeyPath, str]]:
    """The path-valued frontmatter fields of a concept and their values (OKF v0.3 §6.2).

    ``resource``, ``superseded_by``, ``computation``, ``executor.resource``, ``attester.resource`` and each
    ``sources[].resource``. A value that is not a string, is a URI (it has a scheme or starts with ``//``) or holds
    whitespace (a ``sources`` scope descriptor, §5.1) is not a path and is left out.
    """
    found: list[tuple[KeyPath, str]] = [
        ((key,), frontmatter[key]) for key in ("resource", "superseded_by", "computation") if key in frontmatter
    ]
    for key in ("executor", "attester"):
        value = frontmatter.get(key)
        if isinstance(value, dict) and "resource" in value:
            found.append(((key, "resource"), value["resource"]))
    sources = frontmatter.get("sources")
    for index, source in enumerate(sources if isinstance(sources, list) else []):
        if isinstance(source, dict) and "resource" in source:
            found.append((("sources", index, "resource"), source["resource"]))
    return [
        (key, value)
        for key, value in found
        if isinstance(value, str)
        and value
        and not URI_SCHEME.match(value)
        and not value.startswith("//")
        and not any(c.isspace() for c in value)
    ]


def _path_field_findings(concept: Concept, targets: _Targets) -> list[Finding]:
    """``OKF412`` for a path field that names no file in the bundle (OKF v0.3 §6.2; a leading ``/`` is the root)."""
    findings = []
    own = f"{concept.concept_id}.md"
    for key, value in path_fields(concept.frontmatter or {}):
        path = unquote(value.split("#", 1)[0].split("?", 1)[0])
        if not path:
            continue
        joined = path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(own), path)
        relative = posixpath.normpath(joined)
        name = ".".join(str(part) for part in key)
        if relative.startswith("..") or targets.resolve(relative) is None:
            message = f"`{name}` '{value}' does not resolve to a file in the bundle (OKF v0.3 section 6.2)"
            findings.append(Finding.make("OKF412", concept.path, concept.line_of(*key), message))
    return findings


def _anchor_findings(concept: Concept) -> list[Finding]:
    findings = [
        Finding.make("OKF404", concept.path, a.line, f"anchor id '{a.id}' must be lower case; GitHub lower-cases it")
        for a in concept.anchors
        if a.id != a.id.lower()
    ]
    counts = Counter(a.id.lower() for a in concept.anchors)
    findings.extend(
        Finding.make("OKF404", concept.path, a.line, f"anchor id '{a.id}' is used more than once in this file")
        for a in concept.anchors
        if counts[a.id.lower()] > 1
    )
    findings.extend(
        Finding.make(
            "OKF404", concept.path, h.line, "'{#id}' heading ids are not rendered by GitHub; use <a id=\"...\"></a>"
        )
        for h in concept.headings
        if h.text.rstrip().endswith("}") and "{#" in h.text
    )
    return findings


def _base_findings(concept: Concept, base: BaseIndex) -> list[Finding]:
    earlier = base.find(concept)
    if earlier is None:
        return []
    kept = {a.id.lower() for a in concept.anchors}
    return [
        Finding.make(
            "OKF411", concept.path, 1, f"anchor id '{a.id}' existed in the base and must not be removed or renamed"
        )
        for a in earlier.anchors
        if a.id.lower() not in kept
    ]


def check_links(profile: Profile, concepts: list[Concept], base: list[Concept] | None = None) -> list[Finding]:
    """Run the link and anchor part of check 4.

    Args:
        profile: The loaded profile.
        concepts: The bundle's concepts.
        base: The same bundle at the base commit, if known; explicit anchors present there must remain.

    Returns:
        Findings for root-relative links, missing targets, unmatched fragments, anchor misuse, removed anchors
        and path fields that resolve to nothing.
    """
    targets = _Targets(profile.bundle_root, concepts)
    earlier = BaseIndex(base or [])
    findings: list[Finding] = []
    for concept in concepts:
        findings.extend(_link_findings(concept, targets))
        findings.extend(_path_field_findings(concept, targets))
        findings.extend(_anchor_findings(concept))
        findings.extend(_base_findings(concept, earlier))
    return findings
