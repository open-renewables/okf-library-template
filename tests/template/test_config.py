"""Profile loading, meta-schemas and type schemas."""

import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from okfprofile.config import ProfileError, load_profile, load_schema_registry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A scratch repository holding a copy of the real profile folder."""
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    return tmp_path


def edit_profile(repo: Path, old: str, new: str) -> None:
    path = repo / "profile" / "profile.yaml"
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def problems_of(repo: Path) -> str:
    with pytest.raises(ProfileError) as info:
        load_profile(repo)
    return "\n".join(info.value.problems)


def test_the_template_profile_loads() -> None:
    profile = load_profile(ROOT)
    assert [(t.name, t.uid_prefix) for t in profile.types] == [
        ("Item", "ITM"),
        ("Vocabulary", "VOC"),
        ("Glossary", "GLS"),
    ]
    item = profile.type_named("Item")
    assert item is not None
    assert item.body is not None
    assert [s.heading for s in item.body.sections] == ["Description", "Checks", "Revision history"]
    assert item.body.sections[2].managed_by_ci
    assert profile.type_named("Nope") is None
    assert profile.bundle_root == ROOT / "knowledge"
    assert profile.platform == "github"
    assert [n.name for n in profile.namespaces] == ["group", "category"]
    assert profile.statuses == ("draft", "stable", "deprecated")
    assert profile.rules.reject_unknown_fields
    assert profile.rules.stale_after_default == "P2Y"
    assert {w.kind for w in profile.warnings} == {"agent_label_missing", "stable_section_nonempty", "directory_size"}
    assert profile.path_rules[0].kind == "tag_equals_segment"
    assert profile.path_rules[0].types == ("Item",)
    assert profile.path_rules[0].params == {"segment": 0}
    check = profile.formats["check"]
    assert [(c.label, c.required) for c in check.children] == [("Pass", True), ("Flag", True)]
    assert check.pattern.match("**Name**: does a thing")
    assert profile.tag_pattern.match("group:example")
    assert profile.index.max_concepts_per_directory == 100


def test_scripts_hold_no_domain_value() -> None:
    profile = load_profile(ROOT)
    domain = [t.name for t in profile.types] + [t.uid_prefix for t in profile.types]
    domain += [n.name for n in profile.namespaces] + list(profile.formats)
    sources = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "scripts" / "okfprofile").glob("*.py"))
    code = re.sub(r'""".*?"""|#.*', "", sources, flags=re.DOTALL)
    for word in domain:
        assert not re.search(rf"[\"']{re.escape(word)}[\"']", code), f"domain value {word!r} found in scripts"


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("platform: github", "platform: gitlab", "platform"),
        ("profile_version: 0.1.0", "profile_version: one", "profile_version"),
        ("    uid_prefix: ITM", "    uid_prefix: itm", "uid_prefix"),
        ("  reject_unknown_fields: true", "  reject_unknown_fields: yes", "reject_unknown_fields"),
        (
            "  - kind: tag_equals_segment\n    namespace: group",
            "  - kind: tag_somethings\n    namespace: group",
            "path_rules",
        ),
        ("    max: 100\n    level: low", "    max: 0\n    level: low", "max"),
        ("bundle_root: knowledge", "bundle_root: /abs", "bundle_root must be a relative"),
        ("namespace: group\n    segment: 0", "namespace: nope\n    segment: 0", "undeclared namespace 'nope'"),
        ("    types: [Item]\n  - kind", "    types: [Missing]\n  - kind", "undeclared type 'Missing'"),
        (
            "        - heading: Checks\n          required: false\n          format: check",
            "        - heading: Checks\n          required: false\n          format: nope",
            "undeclared format 'nope'",
        ),
        (
            "    schema: types/glossary.schema.json",
            "    schema: types/absent.schema.json",
            "is not a file in profile/types",
        ),
        ("    schema: types/glossary.schema.json", "    schema: ../elsewhere.json", "is not a file in profile/types"),
        (
            "  - name: Glossary\n    uid_prefix: GLS",
            "  - name: Glossary\n    uid_prefix: VOC",
            "uid prefix 'VOC' is used twice",
        ),
        ("  - name: Glossary", "  - name: Item", "type 'Item' is declared twice"),
        ("  - id: directory-size", "  - id: agent-label-missing", "warning id 'agent-label-missing' is used twice"),
        (
            "  extensions: []",
            "  extensions:\n    - value: draft\n      trust_tier: unverified\n      publishing: x",
            "repeats a status value",
        ),
        ('    paths: ["glossary.md"]', '    paths: ["../glossary.md"]', "must be relative to the bundle root"),
        ("  pattern: '^[a-z][a-z0-9-]*:[a-z0-9][a-z0-9-]*$'", "  pattern: '[unclosed'", "invalid tag pattern"),
    ],
)
def test_invalid_profiles_are_reported_with_a_reason(repo: Path, old: str, new: str, message: str) -> None:
    edit_profile(repo, old, new)
    assert message in problems_of(repo)


def test_a_heading_declared_twice_is_reported(repo: Path) -> None:
    edit_profile(
        repo,
        "        - heading: Revision history\n          required: true\n          managed_by: ci\n  - name: Vocabulary",
        "        - heading: Description\n          required: true\n  - name: Vocabulary",
    )
    assert "declares a heading twice" in problems_of(repo)


def test_path_rule_and_warning_references_are_checked(repo: Path) -> None:
    edit_profile(
        repo,
        "    kind: agent_label_missing",
        "    kind: tag_not_equal_segment\n    namespace: topic\n    segments: [0]",
    )
    assert "warning names undeclared namespace 'topic'" in problems_of(repo)


def test_vocabulary_reference_in_a_rule_is_checked(repo: Path) -> None:
    edit_profile(
        repo,
        "  - kind: tag_equals_segment\n    namespace: category",
        "  - kind: tag_required_if_segment_kind\n    namespace: category\n    segment: 0\n    vocabulary: nope\n    kind_value: x\n  - kind: tag_equals_segment\n    namespace: category",
    )
    assert "undeclared vocabulary 'nope'" in problems_of(repo)


def test_yaml_and_file_errors_are_reported(repo: Path) -> None:
    (repo / "profile" / "profile.yaml").write_text("a: [", encoding="utf-8")
    assert "invalid YAML" in problems_of(repo)
    (repo / "profile" / "profile.yaml").unlink()
    assert "cannot read" in problems_of(repo)


def test_missing_meta_schema_is_reported(repo: Path) -> None:
    (repo / "profile" / "schemas" / "profile.schema.json").write_text("{", encoding="utf-8")
    assert "invalid JSON" in problems_of(repo)
    (repo / "profile" / "schemas" / "profile.schema.json").write_text("[]", encoding="utf-8")
    assert "expected a JSON object" in problems_of(repo)


def test_type_schema_problems_are_reported(repo: Path) -> None:
    types = repo / "profile" / "types"
    (types / "broken.schema.json").write_text('{"$id": "x", "type": 5}', encoding="utf-8")
    assert "invalid JSON Schema" in problems_of(repo)
    (types / "broken.schema.json").write_text('{"type": "object"}', encoding="utf-8")
    assert "missing $id" in problems_of(repo)
    (types / "broken.schema.json").write_text("{", encoding="utf-8")
    assert "invalid JSON" in problems_of(repo)


def format_file(repo: Path) -> Path:
    return repo / "profile" / "formats" / "check.md"


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("format: check", "format: other", "must equal the file name"),
        ("pattern: '^\\*\\*(?P<name>[^*]+)\\*\\*: (?P<text>.+)$'", "pattern: '[unclosed'", "invalid item pattern"),
        ("  enums: {}", "  enums: {missing: [a]}", "'missing' is not a named group"),
        ("  vocab: {}", "  vocab: {name: nope}", "undeclared namespace 'nope'"),
        ("  - label: Flag", "  - label: Pass", "duplicate child label"),
        ("format: check", "format: Check", "format"),
    ],
)
def test_invalid_formats_are_reported(repo: Path, old: str, new: str, message: str) -> None:
    path = format_file(repo)
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    assert message in problems_of(repo)


def test_format_file_without_frontmatter_is_reported(repo: Path) -> None:
    format_file(repo).write_text("no frontmatter", encoding="utf-8")
    assert "frontmatter must open" in problems_of(repo)


GOOD_ITEM: dict[str, Any] = {
    "type": "Item",
    "uid": "ITM-0001",
    "title": "Example",
    "description": "One sentence.",
    "tags": ["group:example-group", "category:example-category"],
    "status": "draft",
}


def errors_for(profile_type: str, frontmatter: dict[str, Any], reject_unknown: bool = True) -> list[str]:
    profile = load_profile(ROOT)
    if not reject_unknown:
        object.__setattr__(
            profile, "rules", type(profile.rules)(**{**profile.rules.__dict__, "reject_unknown_fields": False})
        )
    return [e.message for e in profile.type_validator(profile_type).iter_errors(frontmatter)]


def test_a_conforming_item_passes_and_okf_optional_keys_are_accepted() -> None:
    assert errors_for("Item", GOOD_ITEM) == []
    extended = {
        **GOOD_ITEM,
        "stale_after": "2027-01-01T00:00:00Z",
        "verified": {"by": "human:alice", "at": "2026-10-20T09:00:00+01:00"},
        "generated": {"by": "agent/1", "at": "2026-10-20T09:00:00Z"},
        "sources": [{"id": "s1", "resource": "https://example.org", "usage_count": 3}],
    }
    assert errors_for("Item", extended) == []
    assert errors_for("Item", {**extended, "verified": [extended["verified"]]}) == []


@pytest.mark.parametrize(
    ("change", "fragment"),
    [
        ({"extra": "x"}, "extra"),
        ({"type": "Other"}, "Item"),
        ({"uid": "ITM-1"}, "does not match"),
        ({"uid": "VOC-0001"}, "does not match"),
        ({"stale_after": "2027-01-01"}, "does not match"),
        ({"stale_after": "2027-01-01T00:00:00"}, "does not match"),
        ({"tags": ["Group:x"]}, "does not match"),
        ({"tags": []}, "non-empty"),
        ({"tags": ["a:b", "a:b"]}, "non-unique"),
        ({"verified": {"by": "human:a"}}, "not valid under any"),
        ({"sources": [{"id": "s"}]}, "resource"),
        ({"status": 5}, "not of type"),
    ],
)
def test_item_frontmatter_rules(change: dict[str, Any], fragment: str) -> None:
    errors = errors_for("Item", {**GOOD_ITEM, **change})
    assert errors, change
    assert any(fragment in e for e in errors), errors


@pytest.mark.parametrize("missing", ["type", "uid", "title", "description", "tags", "status"])
def test_item_required_keys(missing: str) -> None:
    frontmatter = {k: v for k, v in GOOD_ITEM.items() if k != missing}
    assert any(missing in e for e in errors_for("Item", frontmatter))


def test_unknown_fields_are_accepted_when_the_profile_allows_them() -> None:
    assert errors_for("Item", {**GOOD_ITEM, "extra": 1}, reject_unknown=False) == []


def test_vocabulary_and_glossary_schemas() -> None:
    vocab = {
        "type": "Vocabulary",
        "uid": "VOC-0001",
        "title": "t",
        "description": "d",
        "status": "draft",
        "namespace": "group",
    }
    assert errors_for("Vocabulary", vocab) == []
    assert any("namespace" in e for e in errors_for("Vocabulary", {k: v for k, v in vocab.items() if k != "namespace"}))
    assert errors_for("Vocabulary", {**vocab, "namespace": "Bad Name"})
    glossary = {"type": "Glossary", "uid": "GLS-0001", "title": "t", "description": "d", "status": "draft"}
    assert errors_for("Glossary", glossary) == []
    assert errors_for("Glossary", {**glossary, "uid": "ITM-0001"})


def test_unknown_type_has_no_validator() -> None:
    with pytest.raises(KeyError):
        load_profile(ROOT).type_validator("Nope")


def test_registry_schema_accepts_and_rejects_samples() -> None:
    schema = json.loads((ROOT / "profile" / "schemas" / "uid-registry.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    assert validator.is_valid({})
    assert validator.is_valid({"ITM-0001": {"path": "a/b/c", "type": "Item", "moved_from": ["a/x/c"]}})
    assert not validator.is_valid({"ITM-1": {"path": "a", "type": "Item"}})
    assert not validator.is_valid({"ITM-0001": {"path": "a"}})
    assert not validator.is_valid({"ITM-0001": {"path": "a", "type": "Item", "extra": 1}})


def test_schema_registry_lists_every_type_schema() -> None:
    _, ids, problems = load_schema_registry(ROOT)
    assert problems == []
    assert set(ids) == {"okf-base.schema.json", "item.schema.json", "vocabulary.schema.json", "glossary.schema.json"}


def test_every_profile_file_is_valid_for_its_meta_schema() -> None:
    for name in ("profile", "format", "uid-registry"):
        schema = json.loads((ROOT / "profile" / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


Mutator = Callable[[str], str]


def test_missing_required_key_is_reported_at_the_top_of_the_file(repo: Path) -> None:
    path = repo / "profile" / "profile.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(text[: text.index("index:")], encoding="utf-8", newline="\n")
    assert "profile.yaml:1: (root): 'index' is a required property" in problems_of(repo)


def test_missing_meta_schema_files_are_reported(repo: Path) -> None:
    (repo / "profile" / "schemas" / "profile.schema.json").unlink()
    assert "cannot read" in problems_of(repo)


def test_a_missing_format_meta_schema_is_reported(repo: Path) -> None:
    (repo / "profile" / "schemas" / "format.schema.json").unlink()
    assert "format.schema.json: cannot read" in problems_of(repo)
