"""Check 1: the vendored okf-skills validator, its message mapping, and the datetime rule."""

import ast
import hashlib
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.checks import conformance
from okfprofile.checks.conformance import (
    VENDORED,
    check_conformance,
    datetime_findings,
    datetime_paths,
    load_vendored,
    map_message,
)
from okfprofile.codes import CODES
from okfprofile.document import parse_concept

ROOT = Path(__file__).resolve().parents[2]
VENDOR_DIR = VENDORED.parent


def _text(node: ast.expr) -> str:
    """The constant text of a message expression, with every interpolation replaced by ``X``."""
    if isinstance(node, ast.Constant):
        return str(node.value)
    if isinstance(node, ast.JoinedStr):
        return "".join(
            _text(part.value) if isinstance(part, ast.FormattedValue) else _text(part) for part in node.values
        )
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return _text(node.func.value)
    return "X"


def vendored_messages() -> list[str]:
    tree = ast.parse(VENDORED.read_text(encoding="utf-8"))
    messages = []
    for node in ast.walk(tree):
        is_report_call = isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        if is_report_call and node.func.attr in {"warn", "err"} and len(node.args) == 2:  # type: ignore[attr-defined]  # narrowed by is_report_call
            messages.append(_text(node.args[1]))  # type: ignore[attr-defined]  # narrowed by is_report_call
    return messages


def test_the_vendored_file_is_the_recorded_one() -> None:
    recorded = re.search(
        r"\| SHA-256 of the file \(LF line endings\) \| `([0-9a-f]{64})`",
        (VENDOR_DIR / "VENDORED.md").read_text(encoding="utf-8"),
    )
    assert recorded is not None
    content = VENDORED.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(content).hexdigest() == recorded.group(1)
    assert (VENDOR_DIR / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
    assert "Apache License" in (VENDOR_DIR / "NOTICE").read_text(encoding="utf-8")


def test_every_message_the_vendored_validator_can_emit_is_mapped() -> None:
    messages = vendored_messages()
    assert len(messages) >= 30
    unmapped = [m for m in messages if map_message(f"f.md: {m}")[0] == "OKF119"]
    assert unmapped == []
    codes = {map_message(f"f.md: {m}")[0] for m in messages} - {None}
    assert codes == {"OKF101", "OKF102", "OKF103", "OKF104", "OKF111", "OKF113", "OKF116", "OKF117", "OKF118"}
    assert codes <= set(CODES)


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ("a.md: §11.1 no parseable YAML frontmatter block (x)", "OKF101"),
        ("a.md: cannot read file: boom", "OKF101"),
        ("a.md: §11.1 frontmatter is not valid YAML: x", "OKF102"),
        ("a.md: §11.1 frontmatter must be a YAML mapping", "OKF103"),
        ("a.md: §11.2 missing or empty required `type` field", "OKF104"),
        ("a.md: recommended field `title` is absent (§4.1)", None),
        ("a.md: cross-link target not found: `x.md` (tolerated under §6.1)", None),
        ("a.md: §5.2 `stale_after` `x` is not an RFC 3339 timestamp", None),
        ("a.md: §7 `generated.by` `Human:x` is a near-miss of `human:`", "OKF113"),
        ("a.md: §5.1 `sources[0].usage_count` has no `usage_window` framing it", "OKF116"),
        ("a.md: §5.1 footnote `[^x]` matches no `sources[].id`", "OKF116"),
        ("a.md: legacy v0.1 `timestamp`: x", "OKF111"),
        ("index.md: §8 index.md should contain no frontmatter", "OKF117"),
        ("a.md: §10.2 an Attested Computation concept requires `runtime`", "OKF118"),
        ("a.md: a message nobody has seen", "OKF119"),
    ],
)
def test_map_message(message: str, code: str | None) -> None:
    assert map_message(message)[0] == code
    assert map_message(message)[1] == message.partition(": ")[0]


def test_vendored_module_loads_once_and_validates_a_directory(tmp_path: Path) -> None:
    assert load_vendored() is load_vendored()
    (tmp_path / "a.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
    report = load_vendored().validate(tmp_path)
    assert report.errors == []


def check_dir(bundle: Path, prefix: str = "knowledge") -> list[tuple[str, str]]:
    findings = check_conformance(bundle, load_bundle(bundle, bundle), prefix)
    return sorted((f.code, f.file) for f in findings)


def test_frontmatter_problem_is_reported_once_with_the_readers_line(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: [oops\n---\n", encoding="utf-8")
    findings = check_conformance(tmp_path, load_bundle(tmp_path, tmp_path.parent), tmp_path.name)
    assert [(f.code, f.file, f.line) for f in findings] == [("OKF102", f"{tmp_path.name}/a.md", 2)]


def test_okf_skills_findings_get_the_bundle_prefix(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntitle: no type\n---\n", encoding="utf-8")
    assert check_dir(tmp_path) == [("OKF104", "knowledge/a.md")]
    assert check_dir(tmp_path, prefix="") == [("OKF104", "a.md")]


def test_attested_computation_without_runtime_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntype: Attested Computation\ncomputation: missing.sql\n---\n", encoding="utf-8")
    assert [c for c, _ in check_dir(tmp_path)] == ["OKF118", "OKF118"]


def test_unmapped_message_becomes_a_warning(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(validate=lambda _bundle: SimpleNamespace(errors=[], warnings=["a.md: brand new message"]))
    monkeypatch.setattr(conformance, "load_vendored", lambda: fake)
    findings = check_conformance(tmp_path, [], "knowledge")
    assert [(f.code, f.level.value, f.message) for f in findings] == [("OKF119", "warning", "brand new message")]


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
