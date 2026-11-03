"""The licence check against the allowlist in constraints.md (plan step 2, ADR-006, ADR-007)."""

import json
from datetime import date
from pathlib import Path

import pytest
from okfprofile.licences import (
    CONSTRAINTS,
    Package,
    Policy,
    PolicyError,
    RecordedException,
    audit_exceptions,
    check_packages,
    installed_packages,
    locked_names,
    normalise,
    parse_policy,
)
from okfprofile.supply_cli import licences_main
from support import ROOT

TODAY = date(2026, 11, 3)
POLICY = Policy(
    allowed=frozenset({"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "PSF-2.0"}),
    exceptions={"pathspec": RecordedException("ADR-007", date(2027, 4, 30))},
    resolutions={("colorama", "0.4.6"): "BSD-3-Clause"},
)


def findings(*packages: Package, today: date = TODAY) -> list[str]:
    return [f.package for f in check_packages(POLICY, list(packages), today).findings]


def test_the_real_policy_is_read_from_constraints() -> None:
    policy = parse_policy((ROOT / CONSTRAINTS).read_text(encoding="utf-8"))
    assert {"MIT", "Apache-2.0", "BSD-3-Clause", "Zlib"} <= policy.allowed
    assert "MPL-2.0" not in policy.allowed
    assert set(policy.exceptions) == {"pathspec", "certifi"}
    assert policy.exceptions["pathspec"].adr == "ADR-007"
    assert policy.resolutions[("nodeenv", "1.11.1")] == "BSD-3-Clause"


def test_missing_policy_parts_are_refused() -> None:
    with pytest.raises(PolicyError, match="no heading"):
        parse_policy("# Constraints\n")
    with pytest.raises(PolicyError, match="Allowed SPDX"):
        parse_policy("### Licence allowlist\n\nNothing here.\n")


@pytest.mark.parametrize(
    "package",
    [
        Package("a", "1", expression="MIT"),
        Package("a", "1", expression="Apache-2.0 OR BSD-2-Clause"),
        Package("a", "1", expression="(MIT AND PSF-2.0)"),
        Package("a", "1", licence="MIT"),
        Package("a", "1", classifiers=("License :: OSI Approved :: MIT License",)),
    ],
)
def test_allowed_licences_pass(package: Package) -> None:
    assert findings(package) == []


@pytest.mark.parametrize(
    "package",
    [
        Package("a", "1", expression="GPL-3.0-only"),
        Package("a", "1", expression="MIT AND GPL-3.0-only"),
        Package("a", "1", expression="MIT WITH Classpath-exception-2.0"),
        Package("a", "1", licence="Dual License"),
        Package("a", "1", licence="Some very long licence text. " * 10),
        Package("a", "1", classifiers=("License :: OSI Approved :: BSD License",)),
        Package("a", "1", classifiers=("License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",)),
        Package("a", "1"),
    ],
)
def test_other_licences_are_findings(package: Package) -> None:
    assert findings(package) == ["a"]


def test_a_recorded_exception_covers_its_package_until_it_expires() -> None:
    mpl = ("License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",)
    assert findings(Package("pathspec", "1.1.1", classifiers=mpl)) == []
    report = check_packages(POLICY, [Package("pathspec", "1.1.1", classifiers=mpl)], date(2027, 5, 1))
    assert "ADR-007 exception expired on 2027-04-30" in report.findings[0].reason


def test_a_metadata_resolution_applies_to_its_version_only() -> None:
    bsd = ("License :: OSI Approved :: BSD License",)
    assert findings(Package("colorama", "0.4.6", classifiers=bsd)) == []
    report = check_packages(POLICY, [Package("colorama", "0.5.0", classifiers=bsd)], TODAY)
    assert "another version" in report.findings[0].reason


def test_names_are_normalised_and_the_project_is_skipped() -> None:
    lock = (
        '[[package]]\nname = "Ruamel.Yaml"\nversion = "1"\nsource = { registry = "https://pypi.org/simple" }\n'
        '[[package]]\nname = "okf-library-template"\nversion = "0.1"\nsource = { virtual = "." }\n'
    )
    assert locked_names(lock) == {"ruamel-yaml"}
    assert normalise("Mdit_Py.Plugins") == "mdit-py-plugins"


def test_installed_packages_report_what_is_missing() -> None:
    packages, missing = installed_packages({"pytest", "no-such-package-here"})
    assert [p.name for p in packages] == ["pytest"]
    assert missing == ["no-such-package-here"]


def test_audit_exceptions_are_read_from_the_table() -> None:
    assert audit_exceptions((ROOT / CONSTRAINTS).read_text(encoding="utf-8")) == []
    text = "### pip-audit exceptions\n\n| Advisory | Package | Reason | Review by |\n| --- | --- | --- | --- |\n| PYSEC-1 | x | y | 2027-01-01 |\n"
    assert audit_exceptions(text) == ["PYSEC-1"]


def test_this_repository_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert licences_main(["--root", str(ROOT), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["checked"] > 20


def test_a_missing_constraints_file_is_a_usage_error(tmp_path: Path) -> None:
    assert licences_main(["--root", str(tmp_path)]) == 2
