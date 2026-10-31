"""The identifier registry, check 6 rules not covered by fixtures, renumbering and scaffolding."""

import shutil
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.changes import ChangeContext
from okfprofile.config import load_profile
from okfprofile.document import parse_concept
from okfprofile.indexes import write_indexes
from okfprofile.registry import (
    Registry,
    RegistryEntry,
    RegistryError,
    apply_moves,
    load_registry,
    parse_registry,
    registry_path,
    renumber,
    save_registry,
    uid_of_concept,
)
from okfprofile.scaffold import create_concept, renumber_concept
from okfprofile.validate import validate_bundle
from support import ROOT, MakeRepo, item_text

ITEM_ID = "example-group/example-category/example-item"
SCHEMA = {"type": "object"}


def test_registry_round_trips_in_canonical_order(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    registry = Registry(
        {
            "ITM-0002": RegistryEntry("b", "Item", ("old/b",)),
            "ITM-0001": RegistryEntry("a", "Item"),
        }
    )
    save_registry(tmp_path, registry)
    text = registry_path(tmp_path).read_text(encoding="utf-8")
    assert text.index("ITM-0001") < text.index("ITM-0002")
    assert "moved_from" in text
    assert load_registry(tmp_path) == registry
    assert Registry().to_text() == "{}\n"


def test_a_missing_registry_file_is_empty(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    registry_path(tmp_path).unlink()
    assert load_registry(tmp_path).entries == {}


@pytest.mark.parametrize(
    "text",
    ["a: [", "ITM-1: {path: a, type: Item}", "ITM-0001: {path: a}", "ITM-0001: {path: a, type: Item, extra: 1}"],
)
def test_invalid_registries_are_rejected(text: str) -> None:
    import json

    schema = json.loads((ROOT / "profile" / "schemas" / "uid-registry.schema.json").read_text(encoding="utf-8"))
    with pytest.raises(RegistryError):
        parse_registry(text, schema, "uid-registry.yaml")


def test_an_unreadable_meta_schema_is_reported(tmp_path: Path) -> None:
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "uid-registry.yaml").write_text("{}", encoding="utf-8")
    with pytest.raises(RegistryError, match="meta-schema"):
        load_registry(tmp_path)


def test_next_uid_never_reuses_a_number() -> None:
    registry = Registry({"ITM-0003": RegistryEntry("a", "Item"), "VOC-0009": RegistryEntry("v", "Vocabulary")})
    assert registry.next_uid("ITM") == "ITM-0004"
    assert registry.next_uid("ITM", {"ITM-0010", "VOC-0099"}) == "ITM-0011"
    assert registry.next_uid("GLS") == "GLS-0001"
    assert registry.highest("VOC") == 9
    full = Registry({"ITM-9999": RegistryEntry("a", "Item")})
    with pytest.raises(ValueError, match="no numbers left"):
        full.next_uid("ITM")


def test_apply_moves_records_the_old_path() -> None:
    registry = Registry({"ITM-0001": RegistryEntry("old", "Item"), "ITM-0002": RegistryEntry("same", "Item")})
    moved = apply_moves(registry, {"new": "ITM-0001", "same": "ITM-0002", "unregistered": "ITM-0009"})
    assert moved.entries["ITM-0001"] == RegistryEntry("new", "Item", ("old",))
    assert moved.entries["ITM-0002"] == registry.entries["ITM-0002"]
    assert registry.entries["ITM-0001"].path == "old"
    again = apply_moves(moved, {"newer": "ITM-0001"})
    assert again.entries["ITM-0001"].moved_from == ("old", "new")
    assert apply_moves(again, {"new": "ITM-0001"}).entries["ITM-0001"].moved_from == ("old", "new", "newer")


def test_uid_of_concept_only_accepts_strings() -> None:
    assert uid_of_concept(parse_concept("---\ntype: T\nuid: ITM-0001\n---\n")) == "ITM-0001"
    assert uid_of_concept(parse_concept("---\ntype: T\nuid: 5\n---\n")) is None
    assert uid_of_concept(parse_concept("no frontmatter")) is None


def test_removing_a_registry_entry_is_reported(make_repo: MakeRepo) -> None:
    from okfprofile.checks import BaseState

    profile = make_repo(
        {"example-group/example-category/example-item.md": item_text()}, {"ITM-0001": RegistryEntry(ITEM_ID, "Item")}
    )
    base_registry = Registry({"ITM-0001": RegistryEntry(ITEM_ID, "Item"), "ITM-0005": RegistryEntry("gone", "Item")})
    found = validate_bundle(profile, base=BaseState([], base_registry)).findings
    assert [f.code for f in found] == ["OKF607"]
    assert "ITM-0005" in found[0].message


def test_a_move_whose_old_path_is_not_recorded_is_still_rejected(make_repo: MakeRepo) -> None:
    from okfprofile.checks import BaseState

    profile = make_repo(
        {"example-group/example-category/renamed.md": item_text()},
        {"ITM-0001": RegistryEntry("example-group/example-category/renamed", "Item")},
    )
    base = BaseState([], Registry({"ITM-0001": RegistryEntry(ITEM_ID, "Item")}))
    found = validate_bundle(profile, base=base, change=ChangeContext(labels={"approved-move"})).findings
    assert [f.code for f in found] == ["OKF605"]
    assert "not recorded" in found[0].message


def test_type_mismatch_with_the_registry(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {"example-group/example-category/example-item.md": item_text()},
        {"ITM-0001": RegistryEntry(ITEM_ID, "Glossary")},
    )
    assert [f.code for f in validate_bundle(profile).findings] == ["OKF608"]


def test_renumbering_clears_a_clash_after_two_branches_took_the_same_number(make_repo: MakeRepo) -> None:
    first = "example-group/example-category/first.md"
    second = "example-group/example-category/second.md"
    profile = make_repo(
        {first: item_text("ITM-0001", description="First."), second: item_text("ITM-0001", description="Second.")},
        {"ITM-0001": RegistryEntry("example-group/example-category/first", "Item")},
    )
    assert "OKF603" in {f.code for f in validate_bundle(profile).findings}

    old, new = renumber_concept(profile, "example-group/example-category/second")
    assert (old, new) == ("ITM-0001", "ITM-0002")
    assert "uid: ITM-0002" in (profile.bundle_root / second).read_text(encoding="utf-8")
    assert validate_bundle(load_profile(profile.root)).findings == []
    registry = load_registry(profile.root)
    assert registry.entries["ITM-0001"].path == "example-group/example-category/first"
    assert registry.entries["ITM-0002"].path == "example-group/example-category/second"


def test_renumbering_keeps_crlf_endings_and_repoints_a_registry_entry_that_named_the_target(
    make_repo: MakeRepo,
) -> None:
    first, second = "example-group/example-category/first", "example-group/example-category/second"
    profile = make_repo(
        {f"{first}.md": item_text("ITM-0001"), f"{second}.md": item_text("ITM-0001")},
        {"ITM-0001": RegistryEntry(second, "Item")},
    )
    file = profile.bundle_root / f"{second}.md"
    file.write_bytes(file.read_bytes().replace(b"\n", b"\r\n"))
    renumber_concept(profile, second)
    data = file.read_bytes()
    assert b"uid: ITM-0002\r\n" in data
    assert data.count(b"\n") == data.count(b"\r\n")
    registry = load_registry(profile.root)
    assert registry.entries["ITM-0001"].path == first
    assert registry.entries["ITM-0002"].path == second


def test_renumber_refuses_unshared_or_unknown_concepts(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {"example-group/example-category/a.md": item_text()},
        {"ITM-0001": RegistryEntry("example-group/example-category/a", "Item")},
    )
    concepts = load_bundle(profile.bundle_root, profile.root)
    registry = load_registry(profile.root)
    with pytest.raises(ValueError, match="not shared"):
        renumber(registry, concepts, "example-group/example-category/a")
    with pytest.raises(ValueError, match="not found"):
        renumber(registry, concepts, "nope")


def test_create_concept_writes_a_valid_registered_file(make_repo: MakeRepo) -> None:
    profile = make_repo({})
    file = create_concept(
        profile, "Item", "example-group/example-category/new-thing", description="Says something: here."
    )
    text = file.read_text(encoding="utf-8")
    assert "uid: ITM-0001" in text
    assert "title: New thing" in text
    assert 'description: "Says something: here."' in text
    assert "tags: [group:example-group, category:example-category]" in text
    assert "## Revision history\n\n<!-- Maintained by CI. Do not edit. -->" in text
    refreshed = load_profile(profile.root)
    write_indexes(refreshed, load_bundle(refreshed.bundle_root, refreshed.root))
    assert validate_bundle(refreshed).findings == []
    again = create_concept(profile, "Item", "example-group/example-category/another")
    assert "uid: ITM-0002" in again.read_text(encoding="utf-8")
    assert load_registry(profile.root).entries["ITM-0002"].path == "example-group/example-category/another"


@pytest.mark.parametrize(
    ("type_name", "concept_id", "message"),
    [
        ("Widget", "a/b/c", "not declared"),
        ("Item", "A/b/c", "lower-case"),
        ("Item", "a/b/c.md", "lower-case"),
        ("Item", "a/c", "belongs at"),
        ("Item", "example-group/example-category/example-item", "already exists"),
    ],
)
def test_create_concept_refuses_bad_input(make_repo: MakeRepo, type_name: str, concept_id: str, message: str) -> None:
    profile = make_repo(
        {"example-group/example-category/example-item.md": item_text()}, {"ITM-0001": RegistryEntry(ITEM_ID, "Item")}
    )
    with pytest.raises(ValueError, match=message):
        create_concept(profile, type_name, concept_id)


def test_create_concept_for_a_type_without_path_tags(make_repo: MakeRepo) -> None:
    profile = make_repo({})
    file = create_concept(profile, "Glossary", "glossary", title="No")
    text = file.read_text(encoding="utf-8")
    assert 'title: "No"' in text
    assert "tags:" not in text
    refreshed = load_profile(profile.root)
    write_indexes(refreshed, load_bundle(refreshed.bundle_root, refreshed.root))
    assert validate_bundle(refreshed).findings == []


def test_a_path_without_the_folders_a_tag_rule_needs_is_refused(make_repo: MakeRepo) -> None:
    def widen(text: str) -> str:
        return text.replace('paths: ["*/*/*.md"]', 'paths: ["**/*.md"]')

    profile = make_repo({}, profile_edit=widen)
    with pytest.raises(ValueError, match="needs a folder at index 1"):
        create_concept(profile, "Item", "example-group/flat")


def test_an_empty_registry_file_parses_as_empty() -> None:
    import json

    schema = json.loads((ROOT / "profile" / "schemas" / "uid-registry.schema.json").read_text(encoding="utf-8"))
    assert parse_registry("", schema, "uid-registry.yaml").entries == {}


def test_registry_path_that_differs_from_the_concept_is_reported_without_a_base(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {"example-group/example-category/a.md": item_text()},
        {"ITM-0001": RegistryEntry("example-group/example-category/b", "Item")},
    )
    found = validate_bundle(profile).findings
    assert [f.code for f in found] == ["OKF605"]
    assert "'example-group/example-category/b'" in found[0].message


def test_base_concepts_without_a_uid_are_skipped(make_repo: MakeRepo) -> None:
    from okfprofile.checks import BaseState

    profile = make_repo(
        {"example-group/example-category/a.md": item_text()},
        {"ITM-0001": RegistryEntry("example-group/example-category/a", "Item")},
    )
    old = parse_concept("---\ntype: Item\n---\n")
    old.concept_id = "example-group/example-category/a"
    assert validate_bundle(profile, base=BaseState([old], Registry())).findings == []


def test_renumber_refuses_a_uid_line_it_cannot_find(make_repo: MakeRepo) -> None:
    quoted = item_text("ITM-0001").replace("uid: ITM-0001", '"uid": ITM-0001')
    profile = make_repo(
        {"example-group/example-category/a.md": item_text("ITM-0001"), "example-group/example-category/b.md": quoted},
        {"ITM-0001": RegistryEntry("example-group/example-category/a", "Item")},
    )
    with pytest.raises(ValueError, match="cannot find the uid line"):
        renumber_concept(profile, "example-group/example-category/b")
