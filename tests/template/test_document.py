"""Reading concept files: frontmatter, structure, line numbers."""

from pathlib import Path

import pytest
from okfprofile.document import github_slug, load_concept, parse_concept, parse_yaml
from ruamel.yaml.error import YAMLError

GOOD = """---
type: Item
uid: ITM-0001
status: no
stale_after: 2027-01-01
verified_at: 2027-01-01T00:00:00Z
count: 5
ratio: 1.5
flag: true
tags: [group:g, category:c]
nested:
  key: value
---

# Title

## Description

Text with a footnote.[^1] And a [link](other.md#frag) and ![alt](pic.png).
Second line has <a id="my-anchor"></a>anchor and a <b>bare tag</b>.

<div id="block">x</div>

## Checks

- **One**: first
    - Pass: yes
    - Flag: no
  - Odd: two-space
1. numbered

## Revision history

- 2026-10-20 · author @a

[^1]: A footnote.
"""


def test_frontmatter_types_follow_yaml_12_with_strings_for_dates() -> None:
    concept = parse_concept(GOOD, "x.md")
    assert not concept.findings
    fm = concept.frontmatter
    assert fm is not None
    assert fm["status"] == "no"
    assert fm["stale_after"] == "2027-01-01"
    assert fm["verified_at"] == "2027-01-01T00:00:00Z"
    assert fm["count"] == 5
    assert fm["ratio"] == 1.5
    assert fm["flag"] is True
    assert fm["tags"] == ["group:g", "category:c"]
    assert fm["nested"] == {"key": "value"}
    assert concept.line_of("tags", 1) == 10
    assert concept.line_of("nested", "key") == 12
    assert concept.line_of("missing", "deep") == 1
    assert concept.line_of() == 1


def test_headings_sections_and_slugs() -> None:
    concept = parse_concept(GOOD)
    assert [(h.level, h.text) for h in concept.headings] == [
        (1, "Title"),
        (2, "Description"),
        (2, "Checks"),
        (2, "Revision history"),
    ]
    assert concept.headings[0].line == 15
    checks = concept.section("Checks")
    assert checks is not None
    assert checks.heading.slug == "checks"
    assert checks.end_line == concept.section("Revision history").heading.line - 1  # type: ignore[union-attr]
    assert concept.section("Nope") is None


def test_list_items_keep_marker_free_text_indent_and_nesting() -> None:
    concept = parse_concept(GOOD)
    checks = concept.section("Checks")
    assert checks is not None
    first, numbered = checks.items
    assert first.text == "**One**: first"
    assert first.indent == 0
    assert not first.ordered
    assert [(c.text, c.indent) for c in first.children] == [("Pass: yes", 4), ("Flag: no", 4), ("Odd: two-space", 2)]
    assert numbered.ordered
    assert numbered.text == "numbered"
    assert first.line + 1 == first.children[0].line


def test_links_images_html_anchors_and_footnotes() -> None:
    concept = parse_concept(GOOD)
    links = {(link.kind, link.href): link for link in concept.links}
    assert set(links) == {("link", "other.md#frag"), ("image", "pic.png")}
    assert links[("link", "other.md#frag")].text == "link"
    assert links[("link", "other.md#frag")].section == "Description"
    assert [a.id for a in concept.anchors] == ["my-anchor"]
    assert any(h.block for h in concept.html)
    assert any(not h.block and h.text == "<b>" for h in concept.html)
    assert [f.label for f in concept.footnote_refs] == ["1"]
    assert [f.label for f in concept.footnote_defs] == ["1"]
    assert concept.footnote_defs[0].line == len(GOOD.splitlines())


def test_crlf_input_gives_the_same_result() -> None:
    lf = parse_concept(GOOD)
    crlf = parse_concept(GOOD.replace("\n", "\r\n"))
    assert crlf.frontmatter == lf.frontmatter
    assert [(h.text, h.line) for h in crlf.headings] == [(h.text, h.line) for h in lf.headings]


def test_duplicate_headings_get_numbered_slugs() -> None:
    concept = parse_concept("---\ntype: T\n---\n# A\n## Same\n## Same\n## Same\n")
    assert [h.slug for h in concept.headings] == ["a", "same", "same-1", "same-2"]


@pytest.mark.parametrize(
    ("text", "slug"),
    [
        ("Überschuss", "überschuss"),
        ("Soiling loss (PID)", "soiling-loss-pid"),
        ("Café", "café"),
        ("a_b - c!", "a_b---c"),
        ("  Padded  ", "padded"),
    ],
)
def test_github_slug(text: str, slug: str) -> None:
    assert github_slug(text) == slug


@pytest.mark.parametrize(
    ("text", "code", "line"),
    [
        ("# no frontmatter\n", "OKF101", 1),
        ("\n---\ntype: T\n---\n", "OKF101", 1),
        ("\ufeff---\ntype: T\n---\n", "OKF101", 1),
        ("---\ntype: T\n", "OKF101", 1),
        ("", "OKF101", 1),
        ("---\ntype: [unclosed\n---\n", "OKF102", 2),
        ("---\ntype: A\ntype: B\n---\n", "OKF102", 3),
        ("---\n- a\n- b\n---\n", "OKF103", 2),
        ("---\n---\n", "OKF103", 2),
    ],
)
def test_frontmatter_problems(text: str, code: str, line: int) -> None:
    concept = parse_concept(text, "bad.md")
    assert [(f.code, f.line, f.file) for f in concept.findings] == [(code, line, "bad.md")]
    assert concept.frontmatter is None


def test_body_is_still_parsed_when_frontmatter_is_missing() -> None:
    concept = parse_concept("# Heading\n\n- item\n")
    assert concept.headings[0].line == 1
    assert concept.body_first_line == 1


def test_parse_yaml_raises_on_invalid_input() -> None:
    with pytest.raises(YAMLError):
        parse_yaml("a: [")


def test_load_concept_reads_a_file_and_reports_bad_encoding(tmp_path: Path) -> None:
    good = tmp_path / "good.md"
    good.write_text(GOOD, encoding="utf-8", newline="\n")
    assert load_concept(good).frontmatter is not None
    assert load_concept(good, "shown.md").path == "shown.md"
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"---\ntype: \xff\xfe\n---\n")
    concept = load_concept(bad)
    assert [f.code for f in concept.findings] == ["OKF101"]
    assert "UTF-8" in concept.findings[0].message


def test_heading_text_ignores_emphasis_markers() -> None:
    concept = parse_concept("---\ntype: T\n---\n## *Soft* and `code`\n")
    assert concept.headings[0].text == "Soft and code"
