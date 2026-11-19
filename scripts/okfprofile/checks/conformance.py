"""Check 1: OKF conformance (SDD W-04, AD-08 as amended by ADR-013, I-09 ``OKF1xx``).

Three parts: frontmatter problems found by the reader (``OKF101`` to ``OKF103``); the OKF project's validator for
OKF v0.3, vendored unmodified and its findings mapped **by code** (``CODE_TABLE``); and the datetime rule, which the
profile keeps stricter than v0.3 (``OKF120``, RFC-002 D4).

A folder index may carry a scope header (ADR-010), which OKF v0.3 §8 does not allow: the validator reports each as
an error, ``E004``. A usable header is the template's recorded departure (ADR-012, RFC-002 D3), so those errors are
replaced by one bundle-level ``OKF121`` warning naming the files; a header that is not usable is reported by check 5
(``OKF505``, ``OKF506``) instead. The root index may carry bundle metadata under v0.3 §8.1, so it is not counted.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

from okfprofile.document import Concept, KeyPath
from okfprofile.indexes import INDEX, read_header
from okfprofile.report import Finding

VENDORED = Path(__file__).resolve().parents[2] / "vendor" / "okf" / "validate.py"
MODULE_NAME = "okf_validate_v0_3"

DATETIME_WITH_OFFSET = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
)

# Every code the vendored validator can emit, mapped to this tool's code. None drops a finding because another
# check owns it: check 2 (the type's schema) owns the shape of frontmatter values, `OKF120` owns timestamps, check 4
# owns body links and frontmatter path fields, and the stale report owns staleness. Three codes need the file as
# well as the code and are handled in `_map`: `E004` (folder index headers, ADR-012), `W117` (kept only for an
# index), `W120` (reported only when the reader found no frontmatter problem in the file) and `W125` (dropped when
# the root index is missing, which check 5 reports as OKF501).
CODE_TABLE: dict[str, str | None] = {
    "E002": "OKF102",  # frontmatter not a YAML mapping; the reader reports it first, with its line
    "E004": "OKF121",  # header on a folder index; see `_map`
    "E005": "OKF105",  # log.md date heading
    "E006": "OKF105",  # log.md with frontmatter
    "E007": "OKF102",  # duplicate frontmatter key; the reader reports it first
    "W101": None,  # timestamp or window shape: check 2 and OKF120
    "W102": None,  # generated shape: check 2
    "W103": "OKF113",  # actor convention
    "W104": None,  # verified shape: check 2
    "W105": None,  # status value: check 2 (profile status values, FR3.9)
    "W106": None,  # sources entry shape: check 2
    "W107": "OKF116",  # sources[].id not unique
    "W108": "OKF116",  # footnote label matches no sources[].id
    "W109": "OKF116",  # usage_count without a usage_window
    "W110": None,  # tags shape: check 2
    "W111": "OKF118",  # Attested Computation: runtime
    "W112": "OKF118",  # Attested Computation: computation
    "W113": "OKF118",  # Attested Computation: parameters
    "W114": "OKF118",  # Attested Computation: executor, attester
    "W115": None,  # body link target: check 4
    "W116": None,  # path field target: check 4 (OKF412)
    "W117": "OKF117",  # an unquoted okf_version on the root index; elsewhere check 2 owns value types
    "W118": "OKF117",  # log.md date order
    "W119": None,  # v0.2 root fallback for a path field: check 4 (OKF412)
    "W120": "OKF104",  # not a concept: no frontmatter (the reader's OKF101) or no type
    "W122": None,  # date-only generated.at or verified.at: OKF120
    "W123": "OKF122",  # superseded_by without status: deprecated
    "W125": "OKF117",  # root index without okf_version
    "W126": "OKF118",  # Attested Computation: more than one fenced block
    "I201": None,  # stale: the stale report (W-06)
    "I203": None,  # extension keys without x-: uid and namespace stay unprefixed (RFC-002 D6)
    "I204": None,  # no current verification: derived by the trust tier from revision history (I-08)
    "I205": None,  # Attested Computation without an attester: information only
}
FRONTMATTER_CODES = frozenset({"OKF101", "OKF102", "OKF103"})


def load_vendored() -> ModuleType:
    """Load the vendored OKF validator by path.

    Returns:
        The module, registered in ``sys.modules`` under ``MODULE_NAME``.
    """
    existing = sys.modules.get(MODULE_NAME)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(MODULE_NAME, VENDORED)
    if spec is None or spec.loader is None:  # pragma: no cover - the file ships with the repository
        msg = f"cannot load {VENDORED}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _is_folder_index(rel: str) -> bool:
    return rel.endswith(f"/{INDEX}")


def _usable_header(bundle: Path, rel: str) -> bool:
    file = bundle / rel
    return (
        file.is_file() and read_header(file.read_bytes().decode("utf-8", errors="replace"), root=False).problem is None
    )


def _map(bundle: Path, code: str, rel: str, frontmatter_files: set[str]) -> str | None:
    """This tool's code for one validator finding, or None to drop it. Unknown codes map to ``OKF119``."""
    if code not in CODE_TABLE:
        return "OKF119"
    if code == "E004":
        return "OKF121" if _is_folder_index(rel) and _usable_header(bundle, rel) else None
    if code == "W117":
        return "OKF117" if rel == INDEX else None
    if code == "W120" and rel in frontmatter_files:
        return None
    if code == "W125" and not (bundle / INDEX).is_file():
        return None  # a missing root index is check 5's OKF501
    return CODE_TABLE[code]


def okf_findings(bundle: Path, prefix: str, frontmatter_files: set[str] | None = None) -> list[Finding]:
    """Run the vendored validator on a bundle and map its findings.

    Args:
        bundle: The bundle folder.
        prefix: Folder shown before each path (the bundle's path under the repository).
        frontmatter_files: Bundle-relative files for which the reader already reported a frontmatter problem.

    Returns:
        The mapped findings, with the validator's line numbers; usable folder-index headers give one ``OKF121``.
    """
    module = load_vendored()
    checker = module.Checker(bundle.resolve(), datetime.now(UTC))
    checker.run()
    done = frontmatter_files or set()
    findings: list[Finding] = []
    headers: list[str] = []
    for raw in checker.findings:
        code = _map(bundle, raw.code, raw.path, done)
        if code is None or (code in FRONTMATTER_CODES and raw.path in done):
            continue
        file = f"{prefix}/{raw.path}" if prefix else raw.path
        if code == "OKF121":
            headers.append(file)
            continue
        message = f"{raw.code}: {raw.message}" if code == "OKF119" else raw.message
        findings.append(Finding.make(code, file, raw.line or 0, message))
    if headers:
        files = ", ".join(sorted(set(headers)))
        message = (
            f"{len(set(headers))} folder index header(s) carry a scope `description` (ADR-010); in OKF v0.3 a "
            f"subdirectory index has no frontmatter (§8, §11.1): {files}. Consumers must still read the bundle (§11)"
        )
        root = f"{prefix}/{INDEX}" if prefix else INDEX
        findings.append(Finding.make("OKF121", root, 0, message))
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
        prefix: Folder shown before the path in validator findings (the bundle's path under the repository).

    Returns:
        All findings of check 1. A frontmatter problem that both the reader and the validator report is
        reported once, with the reader's line number; index scope headers give one ``OKF121`` warning.
    """
    findings: list[Finding] = []
    for concept in concepts:
        findings.extend(concept.findings)
        findings.extend(datetime_findings(concept))
    shown = f"{prefix}/" if prefix else ""
    done = {f.file[len(shown) :] for f in findings if f.code in FRONTMATTER_CODES and f.file.startswith(shown)}
    findings.extend(okf_findings(bundle, prefix, done))
    return findings
