"""Licence check of the locked dependencies against the allowlist in ``docs/development/constraints.md``.

``constraints.md`` is the single source: the allowlist, the exceptions (ADR-006, ADR-007) and the metadata
resolutions are read from its tables, so the prose and the check cannot drift apart (plan OD-6).
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from datetime import date
from importlib import metadata
from pathlib import Path

CONSTRAINTS = "docs/development/constraints.md"
LOCK = "uv.lock"

CLASSIFIERS = {
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "License :: OSI Approved :: The Unlicense (Unlicense)": "Unlicense",
}
SPDX_WORD = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*$")


class PolicyError(Exception):
    """``constraints.md`` has no readable allowlist."""


@dataclass(frozen=True)
class RecordedException:
    """A recorded exception for one package (an ``MPL-2.0`` package, by an ADR).

    Attributes:
        adr: Deciding record, for example ``ADR-006``.
        review_by: Date after which the exception must be reviewed.
    """

    adr: str
    review_by: date


@dataclass(frozen=True)
class Policy:
    """The licence policy read from ``constraints.md``.

    Attributes:
        allowed: Allowed SPDX identifiers.
        exceptions: Package name to recorded exception.
        resolutions: ``(package, version)`` to the SPDX identifier a human read from the licence text (ADR-007).
    """

    allowed: frozenset[str]
    exceptions: dict[str, RecordedException]
    resolutions: dict[tuple[str, str], str]


@dataclass(frozen=True)
class Package:
    """An installed package that the lock names.

    Attributes:
        name: Normalised name.
        version: Installed version.
        expression: ``License-Expression`` metadata, if any.
        licence: ``License`` metadata, if any.
        classifiers: Licence classifiers.
    """

    name: str
    version: str
    expression: str = ""
    licence: str = ""
    classifiers: tuple[str, ...] = ()


@dataclass(frozen=True)
class LicenceFinding:
    """A package that is not on the allowlist, or an exception that has expired."""

    package: str
    version: str
    licence: str
    reason: str

    def human(self) -> str:
        """One line for the terminal."""
        return f"{self.package} {self.version} ({self.licence or 'no licence metadata'}): {self.reason}"


@dataclass
class LicenceReport:
    """The result of a licence check."""

    findings: list[LicenceFinding] = field(default_factory=list)
    checked: int = 0
    not_installed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if there is no finding."""
        return not self.findings


def normalise(name: str) -> str:
    """The PEP 503 normal form of a distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _section(text: str, heading: str) -> str:
    """The text under ``heading`` up to the next heading of the same or a higher level."""
    match = re.search(rf"^(#+) {re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        msg = f"{CONSTRAINTS}: no heading '{heading}'"
        raise PolicyError(msg)
    rest = text[match.end() :]
    following = re.search(rf"^#{{1,{len(match.group(1))}}} ", rest, re.MULTILINE)
    return rest[: following.start()] if following else rest


def table_rows(section: str, first_header: str) -> list[dict[str, str]]:
    """Rows of the first table in ``section`` whose header begins with ``first_header``.

    Args:
        section: Markdown text.
        first_header: Text of the first header cell.

    Returns:
        One dict per data row, keyed by header cell.
    """
    lines = section.splitlines()
    for index, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == first_header:
            rows = []
            for row in lines[index + 2 :]:
                if not row.startswith("|"):
                    break
                values = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append(dict(zip(cells, values, strict=False)))
            return rows
    return []


def _first_code(cell: str) -> str:
    match = re.search(r"`([^`]+)`", cell)
    return match.group(1) if match else cell.strip()


def parse_policy(constraints: str) -> Policy:
    """Read the policy from the text of ``constraints.md``.

    Args:
        constraints: File content.

    Returns:
        The allowlist, exceptions and metadata resolutions.

    Raises:
        PolicyError: If the allowlist is missing.
    """
    block = _section(constraints, "Licence allowlist")
    match = re.search(r"Allowed SPDX identifiers[^\n]*\n\s*\n([^\n]+)", block)
    if not match:
        msg = f"{CONSTRAINTS}: no 'Allowed SPDX identifiers' list"
        raise PolicyError(msg)
    allowed = frozenset(re.findall(r"`([^`]+)`", match.group(1)))
    exceptions = {}
    for row in table_rows(block, "Exception"):
        adr = row.get("Exception", "")
        when = row.get("Review by", "")
        if adr.startswith("ADR-") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
            exceptions[normalise(_first_code(row.get("Package", "")))] = RecordedException(
                adr, date.fromisoformat(when)
            )
    resolutions = {}
    for row in table_rows(_section(constraints, "Metadata resolutions"), "ADR"):
        key = (normalise(_first_code(row.get("Package", ""))), row.get("Version", ""))
        resolutions[key] = _first_code(row.get("Resolved as", ""))
    return Policy(allowed, exceptions, resolutions)


def audit_exceptions(constraints: str) -> list[str]:
    """Advisory IDs recorded as pip-audit exceptions in ``constraints.md``."""
    section = _section(constraints, "pip-audit exceptions")
    ids = []
    for row in table_rows(section, "Advisory"):
        advisory = row.get("Advisory", "").strip()
        if advisory and advisory not in {"—", "-"}:
            ids.append(advisory)
    return ids


def _expression_ok(expression: str, allowed: frozenset[str]) -> tuple[bool, list[str]]:
    """Evaluate an SPDX expression of identifiers joined by ``AND`` / ``OR``; return (ok, identifiers not allowed)."""
    cleaned = expression.replace("(", " ").replace(")", " ")
    if " WITH " in cleaned or not cleaned.strip():
        return False, [expression]
    for any_of in re.split(r"\s+OR\s+", cleaned.strip()):
        missing = [t for t in re.split(r"\s+AND\s+", any_of.strip()) if t.strip() not in allowed]
        if not missing:
            return True, []
    return False, [t.strip() for t in re.split(r"\s+(?:AND|OR)\s+", cleaned.strip())]


def _declared(package: Package) -> str:
    """The licence the metadata declares, as an SPDX expression where it can be read, else the raw text."""
    if package.expression:
        return package.expression
    if package.licence and len(package.licence) <= 60 and "\n" not in package.licence:
        return package.licence.strip()
    for classifier in package.classifiers:
        if classifier in CLASSIFIERS:
            return CLASSIFIERS[classifier]
    return package.licence.strip()[:60] if package.licence else (package.classifiers[0] if package.classifiers else "")


def check_packages(policy: Policy, packages: list[Package], today: date | None = None) -> LicenceReport:
    """Check packages against the policy.

    A package passes if its licence expression is on the allowlist, if ADR-007 resolves its metadata to an allowed
    identifier for that exact version, or if a recorded exception covers it and has not expired.

    Args:
        policy: The policy.
        packages: Installed packages that the lock names.
        today: Date to judge expiry by (default: today).

    Returns:
        The report.
    """
    today = today or date.today()
    report = LicenceReport()
    for package in packages:
        report.checked += 1
        declared = _declared(package)
        ok, _missing = _expression_ok(declared, policy.allowed)
        resolved = policy.resolutions.get((package.name, package.version))
        if resolved:
            ok = resolved in policy.allowed
            declared = f"{declared} (resolved as {resolved} by ADR-007)"
        exception = policy.exceptions.get(package.name)
        if ok:
            continue
        if exception is None:
            if policy.resolutions and any(k[0] == package.name for k in policy.resolutions):
                reason = "resolved for another version only (ADR-007): read the licence text again and record it"
            else:
                reason = "not on the allowlist and no recorded exception"
            report.findings.append(LicenceFinding(package.name, package.version, declared, reason))
        elif exception.review_by < today:
            reason = f"{exception.adr} exception expired on {exception.review_by}"
            report.findings.append(LicenceFinding(package.name, package.version, declared, reason))
    return report


def locked_names(lock_text: str) -> set[str]:
    """Normalised names of the packages in ``uv.lock``, without the project itself (a virtual source)."""
    data = tomllib.loads(lock_text)
    names = set()
    for entry in data.get("package", []):
        source = entry.get("source", {})
        if "virtual" in source or "editable" in source:
            continue
        names.add(normalise(entry["name"]))
    return names


def _field(meta: metadata.PackageMetadata, key: str) -> str:
    values = meta.get_all(key)
    return values[0].strip() if values else ""


def installed_packages(names: set[str]) -> tuple[list[Package], list[str]]:
    """Read metadata of the installed distributions whose normalised name is in ``names``.

    Args:
        names: Normalised names from the lock.

    Returns:
        The installed packages and the names not installed in this environment (for example a Windows-only
        dependency on Linux).
    """
    found = {}
    for dist in metadata.distributions():
        name = normalise(dist.metadata["Name"] or "")
        if name in names and name not in found:
            meta = dist.metadata
            found[name] = Package(
                name,
                dist.version,
                _field(meta, "License-Expression"),
                _field(meta, "License"),
                tuple(c for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")),
            )
    return [found[n] for n in sorted(found)], sorted(names - set(found))


def check_repository(root: Path, today: date | None = None) -> LicenceReport:
    """Check the installed environment against ``uv.lock`` and ``constraints.md`` under ``root``.

    Args:
        root: Repository root.
        today: Date to judge expiry by.

    Returns:
        The report, with the names the lock lists but this environment does not install.

    Raises:
        PolicyError: If the policy cannot be read.
        OSError: If a file is missing.
    """
    policy = parse_policy((root / CONSTRAINTS).read_text(encoding="utf-8"))
    packages, missing = installed_packages(locked_names((root / LOCK).read_text(encoding="utf-8")))
    report = check_packages(policy, packages, today)
    report.not_installed = missing
    return report
