"""Check 1: OKF conformance (SDD W-04, AD-08, I-09 ``OKF1xx``).

Three parts: frontmatter problems found by the reader (``OKF101`` to ``OKF103``); the vendored okf-skills
validator, run unmodified and its messages mapped to codes; and the datetime rule that the vendored
validator tolerates breaking, enforced here (``OKF120``).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from okfprofile.document import Concept, KeyPath
from okfprofile.report import Finding

VENDORED = Path(__file__).resolve().parents[2] / "vendor" / "okf-skills" / "okf_validate.py"

DATETIME_WITH_OFFSET = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
)

# okf-skills emits strings without codes (V-08). Each rule is (text that identifies the message, code);
# a code of None drops the message because another check owns it: the profile schema (check 2) covers
# recommended fields, the shape of `generated`, `verified` and `sources`, status and timestamps, and
# check 4 covers links. The first matching rule wins.
_DROPPED = None
MESSAGE_RULES: tuple[tuple[str, str | None], ...] = (
    ("§11.1 no parseable YAML frontmatter", "OKF101"),
    ("cannot read file", "OKF101"),
    ("§11.1 frontmatter is not valid YAML", "OKF102"),
    ("§11.1 frontmatter must be a YAML mapping", "OKF103"),
    ("§11.2 missing or empty required `type`", "OKF104"),
    ("recommended field `", _DROPPED),
    ("cross-link target not found", _DROPPED),
    ("is not an RFC 3339 timestamp", _DROPPED),
    ("is not an ISO 8601 datetime", _DROPPED),
    ("§5.4 unknown `status`", _DROPPED),
    ("§5.2 `generated` must be a mapping", _DROPPED),
    ("§5.2 `generated.by` is required", _DROPPED),
    ("§5.2 `verified` must be", _DROPPED),
    ("§5.2 every `verified` entry", _DROPPED),
    ("§5.1 `sources` must be a list", _DROPPED),
    ("must be a mapping", _DROPPED),
    ("must be a `{from, to}` mapping", _DROPPED),
    ("is missing the required `resource`", _DROPPED),
    ("`usage_window` is missing", _DROPPED),
    ("legacy v0.1", "OKF111"),
    ("§7 ", "OKF113"),
    ("has no `usage_window` framing", "OKF116"),
    ("matches no `sources[].id`", "OKF116"),
    ("§8 ", "OKF117"),
    ("§9 ", "OKF117"),
    ("§12 ", "OKF117"),
    ("§10.2 ", "OKF118"),
    ("§6.2 ", "OKF118"),
)
FRONTMATTER_CODES = frozenset({"OKF101", "OKF102", "OKF103"})


def load_vendored() -> ModuleType:
    """Load the vendored okf-skills validator by path.

    Returns:
        The module, registered in ``sys.modules`` as ``okf_validate``.
    """
    existing = sys.modules.get("okf_validate")
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location("okf_validate", VENDORED)
    if spec is None or spec.loader is None:  # pragma: no cover - the file ships with the repository
        msg = f"cannot load {VENDORED}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules["okf_validate"] = module
    spec.loader.exec_module(module)
    return module


def map_message(message: str) -> tuple[str | None, str, str]:
    """Map one okf-skills message to a finding code.

    Args:
        message: A string from the validator's report, ``<path>: <text>``.

    Returns:
        The code (None if the message is dropped), the path it names and the text after the path. A message
        that no rule matches maps to ``OKF119``.
    """
    path, _, text = message.partition(": ")
    for needle, code in MESSAGE_RULES:
        if needle in text:
            return code, path, text
    return "OKF119", path, text


def _okf_skills_findings(bundle: Path, prefix: str) -> list[Finding]:
    report = load_vendored().validate(bundle)
    findings = []
    for message in [*report.errors, *report.warnings]:
        code, rel, text = map_message(message)
        if code is not None:
            file = f"{prefix}/{rel}" if prefix else rel
            findings.append(Finding.make(code, file, 0, text))
    return findings


def datetime_paths(frontmatter: dict[str, Any]) -> list[KeyPath]:
    """Paths of the timestamp-valued OKF keys present in a frontmatter mapping (OKF section 5)."""
    paths: list[KeyPath] = []
    if "stale_after" in frontmatter:
        paths.append(("stale_after",))
    generated = frontmatter.get("generated")
    if isinstance(generated, dict) and "at" in generated:
        paths.append(("generated", "at"))
    verified = frontmatter.get("verified")
    if isinstance(verified, dict) and "at" in verified:
        paths.append(("verified", "at"))
    if isinstance(verified, list):
        paths.extend(("verified", i, "at") for i, v in enumerate(verified) if isinstance(v, dict) and "at" in v)
    paths.extend(_window_paths(frontmatter.get("usage_window"), ("usage_window",)))
    sources = frontmatter.get("sources")
    for i, source in enumerate(sources if isinstance(sources, list) else []):
        if not isinstance(source, dict):
            continue
        if "last_modified" in source:
            paths.append(("sources", i, "last_modified"))
        paths.extend(_window_paths(source.get("usage_window"), ("sources", i, "usage_window")))
    return paths


def _window_paths(window: object, base: KeyPath) -> list[KeyPath]:
    if not isinstance(window, dict):
        return []
    return [(*base, bound) for bound in ("from", "to") if bound in window]


def _value_at(frontmatter: dict[str, Any], path: KeyPath) -> object:
    node: Any = frontmatter
    for step in path:
        node = node[step]
    return node


def datetime_findings(concept: Concept) -> list[Finding]:
    """``OKF120`` for each timestamp-valued key without an ISO 8601 datetime and explicit UTC offset."""
    if concept.frontmatter is None:
        return []
    findings = []
    for path in datetime_paths(concept.frontmatter):
        value = _value_at(concept.frontmatter, path)
        if not isinstance(value, str) or not DATETIME_WITH_OFFSET.match(value):
            name = ".".join(str(step) for step in path)
            message = f"`{name}` must be an ISO 8601 datetime with an explicit UTC offset, such as 2027-01-01T00:00:00Z"
            findings.append(Finding.make("OKF120", concept.path, concept.line_of(*path), message))
    return findings


def check_conformance(bundle: Path, concepts: list[Concept], prefix: str = "") -> list[Finding]:
    """Run check 1 on a bundle.

    Args:
        bundle: The bundle folder.
        concepts: The bundle's concepts, as read by ``load_bundle``.
        prefix: Folder shown before the path in okf-skills findings (the bundle's path under the repository).

    Returns:
        All findings of check 1. A frontmatter problem that both the reader and okf-skills report is
        reported once, with the reader's line number.
    """
    findings: list[Finding] = []
    for concept in concepts:
        findings.extend(concept.findings)
        findings.extend(datetime_findings(concept))
    seen = {(f.code, f.file) for f in findings if f.code in FRONTMATTER_CODES}
    for finding in _okf_skills_findings(bundle, prefix):
        if (finding.code, finding.file) not in seen:
            findings.append(finding)
    return findings
