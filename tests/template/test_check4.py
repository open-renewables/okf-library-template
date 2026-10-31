"""Check 4: vocabularies, links, anchors, tags and path rules."""

from okfprofile.bundle import glob_match
from okfprofile.registry import RegistryEntry
from okfprofile.validate import validate_bundle
from support import MakeRepo, item_text, vocab_text

ITEM = "example-group/example-category/example-item.md"
REG = {"ITM-0001": RegistryEntry("example-group/example-category/example-item", "Item")}


def codes(profile, **kwargs) -> list[str]:  # type: ignore[no-untyped-def]  # thin helper
    return sorted(f.code for f in validate_bundle(profile, **kwargs).findings)


def kinds(text: str) -> str:
    return text.replace(
        "kinds: false\n      values_unique_across_kinds: false",
        "kinds: true\n      values_unique_across_kinds: true",
        1,
    )


def test_a_conforming_bundle_has_no_findings(make_repo: MakeRepo) -> None:
    assert codes(make_repo({ITEM: item_text()}, REG)) == []


def test_glob_matching() -> None:
    assert glob_match("*/*/*.md", "a/b/c.md")
    assert not glob_match("*/*/*.md", "a/b/c/d.md")
    assert not glob_match("*/*/*.md", "a/c.md")
    assert glob_match("**/*.md", "a/b/c.md")
    assert glob_match("**/*.md", "c.md")
    assert glob_match("a/**", "a/b/c.md")
    assert glob_match("v?cab/*.md", "vocab/x.md")
    assert glob_match("glossary.md", "glossary.md")
    assert not glob_match("glossary.md", "glossaryXmd")


def test_vocabulary_problems(make_repo: MakeRepo) -> None:
    broken = vocab_text(
        "group", "VOC-0001", "- `Upper`: Bad value.\n- `a`: One.\n- `a`: Again.\n- no backticks\n- `b`:"
    )
    profile = make_repo({"vocab/group.md": broken})
    found = validate_bundle(profile).findings
    assert {f.code for f in found} == {"OKF407"}
    messages = " | ".join(f.message for f in found)
    assert "lower-case" in messages
    assert "appears twice" in messages
    assert "written `value`" in messages


def test_namespace_must_match_the_file(make_repo: MakeRepo) -> None:
    wrong = vocab_text("other", "VOC-0001", "- `example-group`: The group.")
    profile = make_repo({"vocab/group.md": wrong})
    assert any("`namespace` must be 'group'" in f.message for f in validate_bundle(profile).findings)


def test_a_missing_vocabulary_concept_is_reported_against_its_expected_file(make_repo: MakeRepo) -> None:
    profile = make_repo({ITEM: item_text()}, REG, vocabs=False)
    found = validate_bundle(profile).findings
    assert sorted(f.file for f in found if f.code == "OKF407") == [
        "knowledge/vocab/category.md",
        "knowledge/vocab/group.md",
    ]
    assert all(f.line == 0 for f in found)


def test_kinds_group_values_under_h2_headings(make_repo: MakeRepo) -> None:
    body = "- `loose`: Not under a kind.\n\n## Alpha\n\n- `x`: In alpha.\n\n## Beta\n\n- `x`: Also in beta."
    profile = make_repo({"vocab/group.md": vocab_text("group", "VOC-0001", body)}, profile_edit=kinds)
    messages = [f.message for f in validate_bundle(profile).findings if f.code == "OKF407"]
    assert any("not under a kind heading" in m for m in messages)
    assert any("under two kinds" in m for m in messages)


def test_kinds_allow_the_same_value_under_two_kinds_when_not_required_unique(make_repo: MakeRepo) -> None:
    def edit(text: str) -> str:
        return text.replace(
            "kinds: false\n      values_unique_across_kinds: false",
            "kinds: true\n      values_unique_across_kinds: false",
            1,
        )

    body = "## Alpha\n\n- `example-group`: In alpha.\n\n## Beta\n\n- `example-group`: Also in beta."
    profile = make_repo({"vocab/group.md": vocab_text("group", "VOC-0001", body), ITEM: item_text()}, REG, edit)
    assert codes(profile) == []


def test_links_external_encoded_folder_and_outside(make_repo: MakeRepo) -> None:
    other = "example-group/example-category/other item.md"
    body = (
        "[web](https://example.org/x) [mail](mailto:a@b.c) [enc](other%20item.md) [angle](<other item.md>) "
        "[folder](../) [outside](../../../x.md) [img](missing.png)"
    )
    profile = make_repo(
        {
            ITEM: item_text(description=body),
            other: item_text("ITM-0002", description="Linked."),
            "example-group/index.md": "# G\n",
        },
        {**REG, "ITM-0002": RegistryEntry("example-group/example-category/other item", "Item")},
    )
    messages = [f.message for f in validate_bundle(profile).findings if f.code.startswith("OKF4")]
    assert any("points outside the bundle" in m for m in messages)
    assert any("missing.png" in m for m in messages)
    assert not any("other" in m and "does not exist" in m for m in messages)
    assert not any("'../'" in m for m in messages)


def test_fragments_resolve_against_headings_and_explicit_anchors_without_regard_to_case(make_repo: MakeRepo) -> None:
    target = item_text("ITM-0002", description='<a id="my-anchor"></a>Anchored text.')
    linker = item_text(
        description="[a](other.md#Description) [b](other.md#my-anchor) [c](other.md#MY-ANCHOR) [d](other.md#nope) [e](#description)"
    )
    profile = make_repo(
        {ITEM: linker, "example-group/example-category/other.md": target},
        {**REG, "ITM-0002": RegistryEntry("example-group/example-category/other", "Item")},
    )
    found = [f for f in validate_bundle(profile).findings if f.code == "OKF403"]
    assert len(found) == 1
    assert "#nope" in found[0].message


def test_anchor_misuse(make_repo: MakeRepo) -> None:
    body = '<a id="Dup"></a> and <a id="dup"></a>'
    text = item_text(description=body).replace("## Description", "## Description {#custom}")
    codes_found = codes(make_repo({ITEM: text}, REG))
    assert codes_found.count("OKF404") == 4


def test_anchor_removed_since_the_base(make_repo: MakeRepo) -> None:
    profile = make_repo({ITEM: item_text()}, REG)
    base = make_base(profile, item_text(description='<a id="old-term"></a>Text.'))
    found = validate_bundle(profile, base=base).findings
    assert [f.code for f in found] == ["OKF411"]


def make_base(profile, text: str):  # type: ignore[no-untyped-def]  # thin helper
    from okfprofile.bundle import load_bundle
    from okfprofile.checks import BaseState
    from okfprofile.registry import load_registry

    base_root = profile.root / "base"
    path = base_root / "knowledge" / ITEM
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return BaseState(load_bundle(base_root / "knowledge", base_root), load_registry(profile.root))


def test_tag_problems(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {ITEM: item_text(tags="group:example-group, category:example-category, colour:red, group:nope")}, REG
    )
    found = validate_bundle(profile).findings
    assert sorted(f.code for f in found if f.code in {"OKF405", "OKF406"}) == ["OKF405", "OKF406"]


def test_a_tag_that_breaks_the_pattern_is_reported_once(make_repo: MakeRepo) -> None:
    profile = make_repo({ITEM: item_text(tags="group:example-group, category:example-category, Bad_Tag")}, REG)
    assert codes(profile).count("OKF405") == 1
    assert "OKF204" not in codes(profile)


def test_path_rules_other_than_equals_segment(make_repo: MakeRepo) -> None:
    def edit(text: str) -> str:
        rules = (
            "path_rules:\n  - kind: tag_count\n    namespace: category\n    min: 2\n    max: 3\n    types: [Item]\n"
            "  - kind: tag_equals_segment\n    namespace: group\n    segment: 5\n    types: [Item]\n"
        )
        start, end = text.index("path_rules:"), text.index("status:")
        return text[:start] + rules + "\n" + text[end:]

    profile = make_repo({ITEM: item_text()}, REG, edit)
    messages = [f.message for f in validate_bundle(profile).findings if f.code == "OKF408"]
    assert any("1 'category:' tags found" in m for m in messages)
    assert any("no folder at index 5" in m for m in messages)


def test_tag_required_when_a_folder_has_a_kind(make_repo: MakeRepo) -> None:
    def edit(text: str) -> str:
        text = kinds(text)
        start, end = text.index("path_rules:"), text.index("status:")
        rule = "path_rules:\n  - kind: tag_required_if_segment_kind\n    namespace: category\n    segment: 0\n    vocabulary: group\n    kind_value: Alpha\n\n"
        return text[:start] + rule + text[end:]

    group = vocab_text("group", "VOC-0001", "## Alpha\n\n- `example-group`: In alpha.")
    profile = make_repo({"vocab/group.md": group, ITEM: item_text(tags="group:example-group")}, REG, edit)
    assert [f.code for f in validate_bundle(profile).findings] == ["OKF408"]


def test_type_paths_are_enforced_for_every_declared_type(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {"misplaced.md": item_text("ITM-0002")}, {**REG, "ITM-0002": RegistryEntry("misplaced", "Item")}
    )
    assert "OKF410" in codes(profile)


def test_fragments_into_index_files_and_other_files(make_repo: MakeRepo) -> None:
    body = "[idx](../index.md#group) [file](pic.png#frag) [bad](../index.md#absent)"
    profile = make_repo(
        {
            ITEM: item_text(description=body),
            "example-group/index.md": "# Group\n",
            "example-group/example-category/pic.png": "not really a picture",
        },
        REG,
    )
    found = validate_bundle(profile).findings
    assert [(f.code, "#absent" in f.message) for f in found] == [("OKF403", True)]


def test_vocabulary_ignores_revision_lines_and_reports_an_unclosed_value(make_repo: MakeRepo) -> None:
    line = "- 2026-10-20 · author @a · self-approved (owner) · PR #1"
    text = vocab_text("group", "VOC-0001", "- `example-group`: The group.\n- `unclosed: x").replace(
        "<!-- Maintained by CI. Do not edit. -->", f"<!-- Maintained by CI. Do not edit. -->\n{line}"
    )
    found = validate_bundle(make_repo({"vocab/group.md": text})).findings
    assert [f.code for f in found] == ["OKF407"]
    assert "written `value`" in found[0].message
