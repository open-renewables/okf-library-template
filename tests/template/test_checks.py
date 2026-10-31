"""Checks 2 and 3 on small inline concepts, and the bundle loader."""

from dataclasses import replace
from pathlib import Path

import pytest
from okfprofile.bundle import concept_files, display_path, load_bundle
from okfprofile.checks import check_body, check_frontmatter
from okfprofile.checks.frontmatter import declared_properties
from okfprofile.config import Profile, StatusExtension, load_profile
from okfprofile.document import parse_concept

ROOT = Path(__file__).resolve().parents[2]
PROFILE = load_profile(ROOT)

ITEM_FRONT = "---\ntype: Item\nuid: ITM-0001\ntitle: T\ndescription: D\ntags: [group:g]\nstatus: draft\n{extra}---\n"
GOOD_BODY = "\n# T\n\n## Description\n\nText.\n\n## Revision history\n\n<!-- Maintained by CI. Do not edit. -->\n"


def item(body: str = GOOD_BODY, extra: str = "") -> str:
    return ITEM_FRONT.format(extra=extra) + body


def codes(findings: list) -> list[str]:  # type: ignore[type-arg]  # list of Finding, kept untyped for brevity
    return [f.code for f in findings]


def body_codes(text: str, profile: Profile = PROFILE) -> list[str]:
    return codes(check_body(profile, parse_concept(text, "a.md")))


def test_a_conforming_item_has_no_findings() -> None:
    concept = parse_concept(item(), "a.md")
    assert check_frontmatter(PROFILE, concept) == []
    assert check_body(PROFILE, concept) == []


def test_concepts_without_usable_frontmatter_are_left_to_check_1() -> None:
    for text in ["no frontmatter", "---\ntitle: x\n---\n", "---\ntype: 5\n---\n", "---\ntype: ''\n---\n"]:
        concept = parse_concept(text, "a.md")
        assert check_frontmatter(PROFILE, concept) == []
        assert check_body(PROFILE, concept) == []


def test_declared_properties_follow_references() -> None:
    declared = declared_properties(PROFILE.registry, {"$ref": "item.schema.json"})
    assert {"type", "uid", "tags", "status", "stale_after", "verified", "sources", "title"} <= declared
    assert "colour" not in declared
    assert "namespace" not in declared
    combined = declared_properties(
        PROFILE.registry, {"allOf": [{"$ref": "item.schema.json"}, {"properties": {"x": {}}}]}
    )
    assert {"x", "uid"} <= combined


def test_unknown_fields_are_accepted_when_the_profile_allows_them() -> None:
    relaxed = replace(PROFILE, rules=replace(PROFILE.rules, reject_unknown_fields=False))
    concept = parse_concept(item(extra="colour: red\n"), "a.md")
    assert codes(check_frontmatter(PROFILE, concept)) == ["OKF203"]
    assert check_frontmatter(relaxed, concept) == []


def test_a_declared_status_extension_is_accepted() -> None:
    extended = replace(PROFILE, status_extensions=(StatusExtension("reviewed", "human-reviewed", "stable"),))
    concept = parse_concept(item().replace("status: draft", "status: reviewed"), "a.md")
    assert codes(check_frontmatter(PROFILE, concept)) == ["OKF205"]
    assert check_frontmatter(extended, concept) == []


def test_missing_and_invalid_fields_are_reported_one_by_one() -> None:
    concept = parse_concept("---\ntype: Item\nuid: bad\nstatus: draft\n---\n", "a.md")
    found = check_frontmatter(PROFILE, concept)
    assert codes(found).count("OKF202") == 3
    assert "OKF204" in codes(found)
    assert {"title", "description", "tags"} <= {m.split("`")[1] for m in (f.message for f in found) if "missing" in m}


def test_schema_errors_inside_nested_values_name_their_location() -> None:
    concept = parse_concept(item(extra="sources:\n  - id: s\n"), "a.md")
    found = check_frontmatter(PROFILE, concept)
    assert codes(found) == ["OKF202"]
    assert found[0].line == 9


def test_title_heading_cases() -> None:
    assert body_codes(item(GOOD_BODY.replace("# T\n", ""))) == ["OKF301"]
    assert body_codes(item(GOOD_BODY.replace("## Description", "# T again\n\n## Description"))) == ["OKF301"]
    relaxed_body = replace(PROFILE.types[0].body, title_heading="none")  # type: ignore[type-var]  # the Item type declares a body
    relaxed = replace(PROFILE, types=(replace(PROFILE.types[0], body=relaxed_body), *PROFILE.types[1:]))
    assert body_codes(item(GOOD_BODY.replace("# T\n", "")), relaxed) == []


def test_order_any_allows_other_sections_and_any_order() -> None:
    vocab = (
        "---\ntype: Vocabulary\nuid: VOC-0001\ntitle: V\ndescription: D\nstatus: draft\nnamespace: group\n---\n"
        "\n# V\n\n## Some kind\n\n- `x`: y\n\n## Revision history\n"
    )
    assert body_codes(vocab) == []
    assert body_codes(vocab.replace("## Revision history", "## Another")) == ["OKF302"]


def test_the_placeholder_counts_as_content() -> None:
    assert body_codes(item(GOOD_BODY.replace("Text.", "_To be completed._"))) == []
    assert body_codes(item(GOOD_BODY.replace("Text.", ""))) == ["OKF306"]


def test_html_anchors_and_comments_are_allowed_but_other_html_is_not() -> None:
    body = GOOD_BODY.replace("Text.", 'An <a id="x"></a>anchor, <!-- note --> and `<code>`.')
    assert body_codes(item(body)) == []
    assert body_codes(item(GOOD_BODY.replace("Text.", "Some <i>text</i>."))) == ["OKF313", "OKF313"]
    assert body_codes(item(GOOD_BODY.replace("Text.", "<div>block</div>"))) == ["OKF313"]


def test_revision_history_accepts_ci_lines_and_rejects_everything_else() -> None:
    line = "- 2026-10-20 · author @a · self-approved (owner) · PR #1"
    ok = GOOD_BODY.rstrip() + f"\n{line}\n"
    assert body_codes(item(ok)) == []
    assert body_codes(item(ok + "    - nested\n")) == ["OKF314"]
    assert body_codes(item(GOOD_BODY.rstrip() + "\n\nA paragraph.\n")) == ["OKF314"]
    assert body_codes(item(GOOD_BODY.rstrip() + "\n\n```\ncode\n```\n")) == ["OKF314"]


def test_format_children_enum_and_order() -> None:
    checks = "## Checks\n\n{checks}\n\n## Revision history"
    base = GOOD_BODY.replace("## Revision history", checks)
    good = "- **N**: x\n    - Pass: a\n    - Flag: b\n"
    assert body_codes(item(base.format(checks=good))) == []
    swapped = "- **N**: x\n    - Flag: b\n    - Pass: a\n"
    assert body_codes(item(base.format(checks=swapped))) == ["OKF310"]
    repeated = good + "    - Pass: again\n"
    assert body_codes(item(base.format(checks=repeated))) == ["OKF310"]
    deeper = "- **N**: x\n    - Pass: a\n        - deeper\n    - Flag: b\n"
    assert body_codes(item(base.format(checks=deeper))) == []
    wrong_indent = "- **N**: x\n    - Pass: a\n      - deeper\n    - Flag: b\n"
    assert body_codes(item(base.format(checks=wrong_indent))) == ["OKF312"]


def test_concept_files_skip_reserved_names_and_missing_folders(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    for name in ["a.md", "index.md", "log.md", "sub/b.md", "sub/index.md", "sub/c.txt"]:
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert [p.relative_to(tmp_path).as_posix() for p in concept_files(tmp_path)] == ["a.md", "sub/b.md"]
    assert concept_files(tmp_path / "missing") == []


def test_load_bundle_sets_ids_and_display_paths(tmp_path: Path) -> None:
    bundle = tmp_path / "knowledge" / "g"
    bundle.mkdir(parents=True)
    (bundle / "x.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
    concepts = load_bundle(tmp_path / "knowledge", tmp_path)
    assert [(c.concept_id, c.path) for c in concepts] == [("g/x", "knowledge/g/x.md")]
    assert display_path(Path("elsewhere") / "y.md", tmp_path) == "elsewhere/y.md"


@pytest.mark.parametrize("name", ["Item", "Vocabulary", "Glossary"])
def test_every_declared_type_has_a_body_and_a_schema(name: str) -> None:
    declared = PROFILE.type_named(name)
    assert declared is not None
    assert declared.body is not None
    assert declared.schema_path.exists()
