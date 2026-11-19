"""Check 1: the vendored OKF v0.3 validator, its code table, and the datetime rule (ADR-013)."""

import hashlib
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.checks import conformance
from okfprofile.checks.conformance import (
    CODE_TABLE,
    VENDORED,
    check_conformance,
    datetime_findings,
    datetime_paths,
    load_vendored,
)
from okfprofile.codes import CODES
from okfprofile.document import parse_concept

ROOT = Path(__file__).resolve().parents[2]
VENDOR_DIR = VENDORED.parent


def vendored_codes() -> set[str]:
    """Every finding code the vendored validator's source can emit."""
    return set(re.findall(r'"([EWI][0-9]{3})"', VENDORED.read_text(encoding="utf-8")))


def test_the_vendored_file_is_the_recorded_one() -> None:
    recorded = re.search(
        r"\| SHA-256 of the file \(LF line endings\) \| `([0-9a-f]{64})`",
        (VENDOR_DIR / "VENDORED.md").read_text(encoding="utf-8"),
    )
    assert recorded is not None
    content = VENDORED.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(content).hexdigest() == recorded.group(1)
    assert "Apache License" in (VENDOR_DIR / "LICENSE.md").read_text(encoding="utf-8")


def test_every_code_the_vendored_validator_can_emit_is_in_the_table() -> None:
    codes = vendored_codes()
    assert len(codes) >= 30
    assert sorted(codes - set(CODE_TABLE)) == []
    assert sorted(set(CODE_TABLE) - codes) == []
    mapped = {c for c in CODE_TABLE.values() if c is not None}
    assert mapped <= set(CODES)
    assert mapped == {"OKF102", "OKF104", "OKF105", "OKF113", "OKF116", "OKF117", "OKF118", "OKF121", "OKF122"}


def test_vendored_module_loads_once_and_validates_a_directory(tmp_path: Path) -> None:
    assert load_vendored() is load_vendored()
    (tmp_path / "a.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
    checker = load_vendored().Checker(tmp_path, None)
    checker.run()
    assert [f.level for f in checker.findings if f.level == "error"] == []


def check_dir(bundle: Path, prefix: str = "knowledge") -> list[tuple[str, str]]:
    findings = check_conformance(bundle, load_bundle(bundle, bundle), prefix)
    return sorted((f.code, f.file) for f in findings)


def test_frontmatter_problem_is_reported_once_with_the_readers_line(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: [oops\n---\n", encoding="utf-8")
    findings = check_conformance(tmp_path, load_bundle(tmp_path, tmp_path.parent), tmp_path.name)
    assert [(f.code, f.file, f.line) for f in findings] == [("OKF102", f"{tmp_path.name}/a.md", 2)]


def test_a_missing_type_is_okf104_with_the_bundle_prefix(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntitle: no type\n---\n", encoding="utf-8")
    assert check_dir(tmp_path) == [("OKF104", "knowledge/a.md")]
    assert check_dir(tmp_path, prefix="") == [("OKF104", "a.md")]


def test_attested_computation_without_runtime_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: Attested Computation\ncomputation: missing.sql\n---\n", encoding="utf-8")
    assert [c for c, _ in check_dir(tmp_path)] == ["OKF118"]


def test_findings_carry_the_validators_line(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: T\n---\n\nText.[^x]\n", encoding="utf-8")
    findings = check_conformance(tmp_path, load_bundle(tmp_path, tmp_path), "")
    assert [(f.code, f.line) for f in findings] == [("OKF116", 5)]


def test_dropped_codes_give_no_finding(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(
        "---\ntype: T\nuid: ITM-0001\nstatus: reviewed\ntags: x\n---\n\n[gone](missing.md)\n", encoding="utf-8"
    )
    assert check_dir(tmp_path) == []


def test_superseded_by_without_deprecated_is_okf122(tmp_path: Path) -> None:
    (tmp_path / "b.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("---\ntype: T\nstatus: draft\nsuperseded_by: b.md\n---\n", encoding="utf-8")
    assert check_dir(tmp_path) == [("OKF122", "knowledge/a.md")]


def test_log_md_problems(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("---\ntype: Note\n---\n", encoding="utf-8")
    (tmp_path / "log.md").write_text("---\ntype: Log\n---\n## soon\n", encoding="utf-8")
    assert {c for c, _ in check_dir(tmp_path)} == {"OKF105"}
    (tmp_path / "log.md").write_text("## 2026-10-01\n\n## 2026-10-20\n", encoding="utf-8")
    assert check_dir(tmp_path) == [("OKF117", "knowledge/log.md")]


def test_root_index_metadata_is_not_a_departure(tmp_path: Path) -> None:
    (tmp_path / "x.md").write_text("---\ntype: Note\n---\n", encoding="utf-8")
    (tmp_path / "index.md").write_text(
        '---\nokf_version: "0.3"\ntitle: All\ndescription: Everything.\nlicense: CC-BY-4.0\nx-acme-owner: a\n---\n',
        encoding="utf-8",
    )
    assert check_dir(tmp_path) == []
    (tmp_path / "index.md").write_text("---\nokf_version: 0.3\n---\n", encoding="utf-8")
    assert check_dir(tmp_path) == [("OKF117", "knowledge/index.md")]
    (tmp_path / "index.md").unlink()
    assert check_dir(tmp_path) == []


def test_an_unknown_code_becomes_a_warning(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    finding = SimpleNamespace(path="a.md", line=3, level="warning", code="W999", message="brand new")

    class Fake:
        def __init__(self, *_args: object) -> None:
            self.findings = [finding]

        def run(self) -> None:
            return None

    monkeypatch.setattr(conformance, "load_vendored", lambda: SimpleNamespace(Checker=Fake))
    findings = check_conformance(tmp_path, [], "knowledge")
    assert [(f.code, f.level.value, f.line, f.message) for f in findings] == [
        ("OKF119", "warning", 3, "W999: brand new")
    ]


@pytest.mark.parametrize(
    "value",
    ["2027-01-01", "2027-01-01T00:00:00", "2027-01-01 00:00:00Z", "soon", "2027-01-01T00:00Z", "20270101T000000Z"],
)
def test_datetimes_without_an_explicit_offset_are_rejected(value: str) -> None:
    concept = parse_concept(f'---\ntype: T\nstale_after: "{value}"\n---\n', "a.md")
    assert [f.code for f in datetime_findings(concept)] == ["OKF120"]
    assert datetime_findings(concept)[0].line == 3


@pytest.mark.parametrize("value", ["2027-01-01T00:00:00Z", "2027-01-01T00:00:00.5+01:00", "2027-01-01T09:00:00-05:30"])
def test_datetimes_with_an_offset_are_accepted(value: str) -> None:
    concept = parse_concept(f"---\ntype: T\nstale_after: {value}\n---\n", "a.md")
    assert datetime_findings(concept) == []


def test_non_string_timestamp_and_all_timestamp_paths() -> None:
    front = """---
type: T
stale_after: 5
generated: { by: a/1, at: 2026-01-01 }
verified:
  - { by: human:a, at: 2026-01-01T00:00:00Z }
  - { by: human:b, at: nope }
usage_window: { from: 2026-01-01T00:00:00Z, to: 2026-02-01 }
sources:
  - resource: x
    last_modified: 2026-05-30
    usage_window: { from: 2026-01-01T00:00:00Z, to: 2026-01-02T00:00:00Z }
  - not-a-mapping
---
"""
    concept = parse_concept(front, "a.md")
    assert concept.frontmatter is not None
    assert datetime_paths(concept.frontmatter) == [
        ("stale_after",),
        ("generated", "at"),
        ("verified", 0, "at"),
        ("verified", 1, "at"),
        ("usage_window", "from"),
        ("usage_window", "to"),
        ("sources", 0, "last_modified"),
        ("sources", 0, "usage_window", "from"),
        ("sources", 0, "usage_window", "to"),
    ]
    lines = {f.line for f in datetime_findings(concept)}
    assert len(datetime_findings(concept)) == 5
    assert lines == {3, 4, 7, 8, 11}
    bare = parse_concept("---\ntype: T\nverified: { by: human:a, at: 2026 }\n---\n", "a.md")
    assert [f.code for f in datetime_findings(bare)] == ["OKF120"]
    assert datetime_findings(parse_concept("no frontmatter", "a.md")) == []


def test_index_scope_headers_give_one_okf121_instead_of_e004(tmp_path: Path) -> None:
    for folder in ("a", "b", "c"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "x.md").write_text("---\ntype: Note\n---\n", encoding="utf-8")
    (tmp_path / "a" / "index.md").write_text('---\ndescription: "Scope a."\n---\n\n# A\n', encoding="utf-8")
    (tmp_path / "b" / "index.md").write_text('---\ndescription: "Scope b."\n---\n\n# B\n', encoding="utf-8")
    (tmp_path / "c" / "index.md").write_text("---\nowner: x\n---\n\n# C\n", encoding="utf-8")
    (tmp_path / "index.md").write_text(
        '---\nokf_version: "0.3"\ndescription: "All."\n---\n\n# Root\n', encoding="utf-8"
    )
    findings = check_conformance(tmp_path, load_bundle(tmp_path, tmp_path), "knowledge")
    assert sorted((f.code, f.file) for f in findings) == [("OKF121", "knowledge/index.md")]
    message = findings[0].message
    assert message.startswith("2 folder index header(s)")
    assert "knowledge/a/index.md, knowledge/b/index.md." in message
