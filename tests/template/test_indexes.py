"""Revision tiers (golden cases), generated indexes (golden files) and index freshness."""

import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.checks import check_indexes
from okfprofile.history import history_lines
from okfprofile.indexes import (
    IndexHeader,
    expected_indexes,
    folders_of,
    humanise,
    read_header,
    unexpected_indexes,
    write_indexes,
)
from okfprofile.registry import RegistryEntry
from okfprofile.revision import Tier, concept_tier, parse_revision_line
from support import MakeRepo, item_text

GOLDEN = Path(__file__).parent / "golden"
CASES = json.loads((GOLDEN / "tiers.json").read_text(encoding="utf-8"))
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_tier_golden_cases(case: dict) -> None:  # type: ignore[type-arg]  # JSON case
    lines = [parse_revision_line(text) for text in case["lines"]]
    assert None not in lines
    result = concept_tier([line for line in lines if line], case.get("require_non_author_approver", False))
    assert result.label == case["expected"]


def test_tier_enum_and_label() -> None:
    assert concept_tier([]).tier is Tier.UNVERIFIED
    assert concept_tier([]).label == "unverified"


ITEMS = {
    "example-group/example-category/alpha.md": (
        "ITM-0001",
        "2026-10-20 · author @a · approved @b (owner) · PR #1",
        "stable",
    ),
    "example-group/example-category/beta.md": (
        "ITM-0002",
        "2026-10-21 · author @a · self-approved (owner) · PR #2",
        "draft",
    ),
    "example-group/example-category/gamma.md": ("ITM-0003", "", "draft"),
}


def sample(make_repo: MakeRepo):  # type: ignore[no-untyped-def]  # returns Profile
    files = {}
    registry = {}
    for rel, (uid, line, status) in ITEMS.items():
        text = item_text(uid, description=f"About {rel.rsplit('/', 1)[1][:-3]}.").replace(
            "status: draft", f"status: {status}"
        )
        if line:
            text = text.replace(
                "<!-- Maintained by CI. Do not edit. -->", f"<!-- Maintained by CI. Do not edit. -->\n- {line}"
            )
        files[rel] = text.replace("title: T", f"title: {rel.rsplit('/', 1)[1][:-3].title()}").replace(
            "# T\n", f"# {rel.rsplit('/', 1)[1][:-3].title()}\n"
        )
        registry[uid] = RegistryEntry(rel[:-3], "Item")
    return make_repo(files, registry, indexes=False)


@pytest.mark.parametrize(
    ("relative", "golden"),
    [
        ("index.md", "index-root.md"),
        ("example-group/index.md", "index-group.md"),
        ("example-group/example-category/index.md", "index-category.md"),
        ("vocab/index.md", "index-vocab.md"),
    ],
)
def test_generated_indexes_match_the_golden_files(make_repo: MakeRepo, relative: str, golden: str) -> None:
    profile = sample(make_repo)
    text = expected_indexes(profile, load_bundle(profile.bundle_root, profile.root))[relative]
    file = GOLDEN / golden
    if UPDATE:
        file.write_text(text, encoding="utf-8", newline="\n")
    assert text == file.read_text(encoding="utf-8")


def test_indexes_are_written_checked_and_idempotent(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    assert {f.code for f in check_indexes(profile, concepts)} == {"OKF501"}
    written = write_indexes(profile, concepts)
    assert len(written) == 4
    assert check_indexes(profile, concepts) == []
    assert write_indexes(profile, concepts, only_missing=True) == []
    first = [p.read_bytes() for p in written]
    write_indexes(profile, concepts)
    assert [p.read_bytes() for p in written] == first


def test_a_stale_edited_or_crlf_index(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    write_indexes(profile, concepts)
    root_index = profile.bundle_root / "index.md"
    root_index.write_bytes(root_index.read_bytes().replace(b"\n", b"\r\n"))
    assert check_indexes(profile, concepts) == []
    root_index.write_text(root_index.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
    assert [f.code for f in check_indexes(profile, concepts)] == ["OKF502"]


def test_regenerating_only_some_folders(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    written = write_indexes(profile, concepts, only_folders={"vocab"})
    assert [p.relative_to(profile.bundle_root).as_posix() for p in written] == ["vocab/index.md"]


def test_unexpected_indexes_and_folder_set(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    (profile.bundle_root / "empty").mkdir()
    (profile.bundle_root / "empty" / "index.md").write_text("x", encoding="utf-8")
    assert unexpected_indexes(profile, concepts) == ["empty/index.md"]
    assert folders_of(concepts) == {"", "example-group", "example-group/example-category", "vocab"}
    assert folders_of([]) == set()


def test_humanise_and_history_lines(make_repo: MakeRepo) -> None:
    assert humanise("example-category") == "Example category"
    assert humanise("") == ""
    profile = sample(make_repo)
    concepts = {c.concept_id: c for c in load_bundle(profile.bundle_root, profile.root)}
    assert len(history_lines(profile, concepts["example-group/example-category/alpha"])) == 1
    assert history_lines(profile, concepts["example-group/example-category/gamma"]) == []
    assert history_lines(profile, concepts["vocab/group"]) == []


def test_tier_follows_the_require_non_author_setting(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    key = "example-group/example-category/index.md"
    assert "human-reviewed (self)" in expected_indexes(profile, concepts)[key]
    strict = replace(profile, rules=replace(profile.rules, require_non_author_approver=True))
    text = expected_indexes(strict, concepts)[key]
    assert "human-reviewed (self)" not in text
    assert "[Beta](beta.md) — D · draft · machine-confirmed" in text


def test_read_header_cases() -> None:
    assert read_header("# Title\n", root=False) == IndexHeader()
    good = read_header('---\ndescription: "Scope."\n---\n\nbody\n', root=False)
    assert good.raw == '---\ndescription: "Scope."\n---\n'
    assert good.description == "Scope."
    assert good.problem is None
    assert read_header("---\ndescription: x\n", root=False).problem == (
        "OKF505",
        1,
        "the index header is not closed with '---'",
    )
    assert read_header("---\n[a\n---\n", root=False).problem[0] == "OKF505"  # type: ignore[index]
    assert read_header("---\n- a\n---\n", root=False).problem[0] == "OKF505"  # type: ignore[index]
    unknown = read_header("---\ndescription: a\nowner: b\n---\n", root=False)
    assert unknown.problem is not None
    assert unknown.problem[:2] == ("OKF506", 3)
    assert unknown.description is None
    assert read_header('---\nokf_version: "0.2"\n---\n', root=False).problem[0] == "OKF506"  # type: ignore[index]
    assert read_header('---\nokf_version: "0.2"\ndescription: a\n---\n', root=True).problem is None
    for bad in ('""', "[a]", "|\n  first line\n  second line"):
        assert read_header(f"---\ndescription: {bad}\n---\n", root=False).problem[0] == "OKF506"  # type: ignore[index]


def test_a_folder_header_is_kept_and_shown_on_the_parent_line(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    write_indexes(profile, concepts)
    group = profile.bundle_root / "example-group" / "index.md"
    group.write_text(
        "---\ndescription: 'Things  grouped.'\n---\n\n" + group.read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert [f.code for f in check_indexes(profile, concepts)] == ["OKF502"]
    write_indexes(profile, concepts)
    assert group.read_text(encoding="utf-8").startswith("---\ndescription: 'Things  grouped.'\n---\n\n<!-- Generated")
    root = (profile.bundle_root / "index.md").read_text(encoding="utf-8")
    assert "- [Example group](example-group/index.md) — Things grouped.\n" in root
    assert check_indexes(profile, concepts) == []
    group.write_text(group.read_text(encoding="utf-8").replace("Things", "Items"), encoding="utf-8")
    assert [f.file for f in check_indexes(profile, concepts)] == [f"{profile.bundle_root.name}/index.md"]
    write_indexes(profile, concepts)
    group.write_text(group.read_text(encoding="utf-8") + "- hand edit\n", encoding="utf-8")
    assert [f.code for f in check_indexes(profile, concepts)] == ["OKF502"]


def test_the_root_header_keeps_a_description_and_follows_the_profile_version(make_repo: MakeRepo) -> None:
    profile = sample(make_repo)
    concepts = load_bundle(profile.bundle_root, profile.root)
    root = profile.bundle_root / "index.md"
    root.write_text('---\nokf_version: "0.1"\ndescription: "The whole bundle."\n---\n\nold\n', encoding="utf-8")
    write_indexes(profile, concepts)
    text = root.read_text(encoding="utf-8")
    assert text.startswith(f'---\nokf_version: "{profile.okf_version}"\ndescription: "The whole bundle."\n---\n\n')
    assert check_indexes(profile, concepts) == []
    root.write_text("---\n[a\n---\n\nold\n", encoding="utf-8")
    write_indexes(profile, concepts)
    assert root.read_text(encoding="utf-8").startswith("---\n[a\n---\n\n<!-- Generated")
    assert {f.code for f in check_indexes(profile, concepts)} == {"OKF505"}
