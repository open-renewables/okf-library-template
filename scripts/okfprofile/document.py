"""Read a concept file: frontmatter, Markdown structure and line numbers (SDD C-03, I-01).

Frontmatter must open with ``---`` on line 1 (OKF section 4). It is parsed as YAML 1.2 with the
timestamp type disabled, so ``no`` stays a string and dates stay strings; numbers and
``true``/``false`` keep their types. The body is parsed with markdown-it-py (CommonMark plus
footnotes); structure is read from tokens, never from regular expressions over Markdown.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.constructor import RoundTripConstructor
from ruamel.yaml.error import YAMLError

from okfprofile.report import Finding

DELIMITER = "---"
TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"
SECTION_LEVEL = 2
BLOCK_KINDS = frozenset(
    {"paragraph_open", "bullet_list_open", "ordered_list_open", "fence", "code_block", "blockquote_open", "html_block"}
)

KeyPath = tuple[str | int, ...]


class _Constructor(RoundTripConstructor):
    """Round-trip constructor that leaves timestamp-shaped scalars as strings."""


_Constructor.add_constructor(TIMESTAMP_TAG, lambda self, node: self.construct_scalar(node))


@dataclass(frozen=True)
class Heading:
    """A heading in the body.

    Attributes:
        level: 1 to 6.
        text: Plain text of the heading.
        line: 1-based line in the file.
        slug: GitHub's automatic anchor for the heading, including the ``-1``, ``-2`` suffix for repeats.
    """

    level: int
    text: str
    line: int
    slug: str


@dataclass(frozen=True)
class ListItem:
    """A list item.

    Attributes:
        text: First line of the item's source with the list marker removed.
        line: 1-based line in the file.
        indent: Columns before the marker on its line.
        ordered: True for a numbered item.
        children: Items of a list nested inside this item.
    """

    text: str
    line: int
    indent: int
    ordered: bool
    children: tuple[ListItem, ...] = ()


@dataclass(frozen=True)
class Paragraph:
    """A top-level paragraph of a section.

    Attributes:
        text: Source text of the paragraph, lines joined with a newline and stripped.
        line: 1-based line in the file.
    """

    text: str
    line: int


@dataclass(frozen=True)
class Section:
    """An H2 section and what sits directly under it.

    Attributes:
        heading: The H2 heading.
        end_line: Last line of the section (the line before the next H2, or the last line of the file).
        items: Top-level list items in the section.
        paragraphs: Top-level paragraphs in the section.
        has_content: True if the section holds any paragraph, list, code, quote or non-comment HTML block.
            Footnote definitions and HTML comments do not count.
    """

    heading: Heading
    end_line: int
    items: tuple[ListItem, ...]
    paragraphs: tuple[Paragraph, ...] = ()
    has_content: bool = False


@dataclass(frozen=True)
class Link:
    """An inline link or image.

    Attributes:
        href: Destination as written.
        text: Link text (alt text for an image).
        line: 1-based line in the file.
        kind: ``link`` or ``image``.
        section: Text of the H2 heading the link sits under, if any.
    """

    href: str
    text: str
    line: int
    kind: Literal["link", "image"]
    section: str | None


@dataclass(frozen=True)
class HtmlSpan:
    """Raw HTML in the body, inline or as a block.

    Attributes:
        text: The HTML as written.
        line: 1-based line in the file.
        block: True for an HTML block, False for inline HTML.
    """

    text: str
    line: int
    block: bool


@dataclass(frozen=True)
class Anchor:
    """An explicit anchor from an ``<a id>`` or ``<a name>`` tag, id as written (case kept).

    Attributes:
        id: The anchor id.
        line: 1-based line in the file.
    """

    id: str
    line: int


@dataclass(frozen=True)
class Footnote:
    """A footnote reference or definition.

    Attributes:
        label: The footnote label.
        line: 1-based line in the file.
    """

    label: str
    line: int


@dataclass
class Concept:
    """A parsed concept file.

    Attributes:
        path: Path as given by the caller, used in findings.
        concept_id: Path under the bundle root without ``.md`` (set by the bundle loader).
        frontmatter: Parsed mapping, or None when the block is missing or invalid.
        key_lines: 1-based file line of each frontmatter key path.
        body_first_line: 1-based line of the first body line.
        body_lines: Body split into lines (no terminators), CRLF normalised.
        headings: All headings in order.
        sections: H2 sections in order.
        links: Inline links and images.
        html: Raw HTML spans.
        anchors: Explicit anchors found in the HTML.
        footnote_refs: Footnote references in order.
        footnote_defs: Footnote definitions in order.
        findings: Problems found while reading (frontmatter codes only).
    """

    path: str
    concept_id: str = ""
    frontmatter: dict[str, Any] | None = None
    key_lines: dict[KeyPath, int] = field(default_factory=dict)
    body_first_line: int = 1
    body_lines: list[str] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    html: list[HtmlSpan] = field(default_factory=list)
    anchors: list[Anchor] = field(default_factory=list)
    footnote_refs: list[Footnote] = field(default_factory=list)
    footnote_defs: list[Footnote] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def line_of(self, *path: str | int) -> int:
        """Line of a frontmatter key path, falling back to its nearest parent, then to line 1."""
        key: KeyPath = tuple(path)
        while key:
            if key in self.key_lines:
                return self.key_lines[key]
            key = key[:-1]
        return 1

    def section(self, heading: str) -> Section | None:
        """The first H2 section whose heading text equals ``heading``."""
        return next((s for s in self.sections if s.heading.text == heading), None)


def github_slug(text: str) -> str:
    """GitHub's automatic heading anchor, without the numeric suffix for repeats.

    Lower-cases, drops everything except letters, marks, numbers, underscores, hyphens and spaces,
    and turns spaces into hyphens.

    Args:
        text: Plain heading text.

    Returns:
        The slug.
    """
    kept = []
    for ch in text.strip().lower():
        category = unicodedata.category(ch)
        if ch == " ":
            kept.append("-")
        elif ch == "-" or category[0] in "LMN" or category == "Pc":
            kept.append(ch)
    return "".join(kept)


class _AnchorParser(HTMLParser):
    """Collect ``id`` and ``name`` attributes of ``a`` tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.ids.extend(value for name, value in attrs if name in {"id", "name"} and value)


def _plain(node: Any, path: KeyPath, lines: dict[KeyPath, int]) -> Any:
    """Convert ruamel's round-trip nodes to plain Python values, recording 0-based key lines."""
    if isinstance(node, CommentedMap):
        result: dict[str, Any] = {}
        for key, value in node.items():
            child = (*path, str(key))
            lines[child] = node.lc.key(key)[0]
            result[str(key)] = _plain(value, child, lines)
        return result
    if isinstance(node, CommentedSeq):
        items = []
        for index, value in enumerate(node):
            child = (*path, index)
            lines[child] = node.lc.item(index)[0]
            items.append(_plain(value, child, lines))
        return items
    if isinstance(node, bool) or node is None:
        return node
    if isinstance(node, int):
        return int(node)
    if isinstance(node, float):
        return float(node)
    return str(node)


def parse_yaml(text: str) -> tuple[Any, dict[KeyPath, int]]:
    """Parse YAML 1.2 with timestamps left as strings.

    Args:
        text: YAML source.

    Returns:
        The plain value and the 0-based line of each key path.

    Raises:
        ruamel.yaml.YAMLError: If the text is not valid YAML (including a duplicate key).
    """
    yaml = YAML(typ="rt")
    yaml.Constructor = _Constructor
    yaml.version = (1, 2)
    lines: dict[KeyPath, int] = {}
    return _plain(yaml.load(text), (), lines), lines


def _inline_text(token: Token) -> str:
    parts = []
    for child in token.children or []:
        if child.type in {"text", "code_inline"}:
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append(" ")
    return "".join(parts)


@dataclass
class _ItemBuilder:
    text: str
    line: int
    indent: int
    ordered: bool
    children: list[ListItem] = field(default_factory=list)

    def freeze(self) -> ListItem:
        return ListItem(self.text, self.line, self.indent, self.ordered, tuple(self.children))


def _item_source(token: Token, body_lines: list[str]) -> tuple[str, int, bool]:
    """First source line of a list item without its marker, with the marker's column."""
    start = token.map[0] if token.map else 0
    raw = body_lines[start]
    stripped = raw.lstrip(" ")
    ordered = token.markup in {".", ")"}
    marker_length = len(token.info) + 1 if ordered else 1
    return stripped[marker_length:].strip(), len(raw) - len(stripped), ordered


class _BodyReader:
    """Walk the token stream once and collect structure."""

    def __init__(self, concept: Concept) -> None:
        self.concept = concept
        self.first_line = concept.body_first_line
        self.slugs: dict[str, int] = {}
        self.section_headings: list[Heading] = []
        self.section_items: list[list[ListItem]] = []
        self.section_paragraphs: list[list[Paragraph]] = []
        self.section_content: list[bool] = []
        self.in_footnotes = False
        self.stack: list[_ItemBuilder] = []
        self.current_h2: str | None = None

    def line(self, token: Token, extra: int = 0) -> int:
        start = token.map[0] if token.map else 0
        return self.first_line + start + extra

    def heading(self, level: int, text: str, line: int) -> None:
        base = github_slug(text)
        count = self.slugs.get(base, 0)
        self.slugs[base] = count + 1
        heading = Heading(level, text, line, base if count == 0 else f"{base}-{count}")
        self.concept.headings.append(heading)
        if level == SECTION_LEVEL:
            self.current_h2 = text
            self.section_headings.append(heading)
            self.section_items.append([])
            self.section_paragraphs.append([])
            self.section_content.append(False)

    def inline(self, token: Token) -> None:
        concept = self.concept
        breaks = 0
        link_stack: list[tuple[Token, int]] = []
        text_parts: list[str] = []
        for child in token.children or []:
            line = self.line(token, breaks)
            if child.type in {"softbreak", "hardbreak"}:
                breaks += 1
            elif child.type == "link_open":
                link_stack.append((child, line))
                text_parts.append("")
            elif child.type == "text" and link_stack:
                text_parts[-1] += child.content
            elif child.type == "link_close" and link_stack:
                opened, opened_line = link_stack.pop()
                href = str(opened.attrGet("href") or "")
                concept.links.append(Link(href, text_parts.pop(), opened_line, "link", self.current_h2))
            elif child.type == "image":
                href = str(child.attrGet("src") or "")
                concept.links.append(Link(href, child.content, line, "image", self.current_h2))
            elif child.type == "html_inline":
                concept.html.append(HtmlSpan(child.content, line, block=False))
            elif child.type == "footnote_ref":
                concept.footnote_refs.append(Footnote(str(child.meta["label"]), line))

    def note_block(self, token: Token) -> None:
        """Record top-level content under the current section."""
        if self.in_footnotes or token.level != 0 or not self.section_content:
            return
        if token.type == "html_block" and token.content.lstrip().startswith("<!--"):
            return
        self.section_content[-1] = True
        if token.type == "paragraph_open" and token.map:
            start, end = token.map
            text = "\n".join(self.concept.body_lines[start:end]).strip()
            self.section_paragraphs[-1].append(Paragraph(text, self.first_line + start))

    def on_heading(self, tokens: list[Token], index: int) -> None:
        token = tokens[index]
        self.heading(int(token.tag[1:]), _inline_text(tokens[index + 1]), self.line(token))

    def on_html_block(self, tokens: list[Token], index: int) -> None:
        token = tokens[index]
        self.concept.html.append(HtmlSpan(token.content.rstrip("\n"), self.line(token), block=True))

    def on_footnote_open(self, tokens: list[Token], index: int) -> None:
        label = str(tokens[index].meta["label"])
        self.concept.footnote_defs.append(Footnote(label, self.line(tokens[index + 1])))

    def on_item_open(self, tokens: list[Token], index: int) -> None:
        token = tokens[index]
        text, indent, ordered = _item_source(token, self.concept.body_lines)
        self.stack.append(_ItemBuilder(text, self.line(token), indent, ordered))

    def on_item_close(self, tokens: list[Token], index: int) -> None:
        item = self.stack.pop().freeze()
        if self.stack:
            self.stack[-1].children.append(item)
        elif self.section_items:
            self.section_items[-1].append(item)

    def run(self, tokens: list[Token]) -> None:
        handlers = {
            "heading_open": self.on_heading,
            "html_block": self.on_html_block,
            "footnote_open": self.on_footnote_open,
            "list_item_open": self.on_item_open,
            "list_item_close": self.on_item_close,
        }
        for index, token in enumerate(tokens):
            kind = token.type
            if kind in BLOCK_KINDS:
                self.note_block(token)
            if kind == "inline":
                self.inline(token)
            elif kind in {"footnote_block_open", "footnote_block_close"}:
                self.in_footnotes = kind == "footnote_block_open"
            elif kind in handlers:
                handlers[kind](tokens, index)

    def finish(self) -> None:
        last_line = self.first_line + len(self.concept.body_lines) - 1
        headings = self.section_headings
        for position, heading in enumerate(headings):
            end = headings[position + 1].line - 1 if position + 1 < len(headings) else last_line
            section = Section(
                heading,
                end,
                tuple(self.section_items[position]),
                tuple(self.section_paragraphs[position]),
                self.section_content[position],
            )
            self.concept.sections.append(section)
        for span in self.concept.html:
            parser = _AnchorParser()
            parser.feed(span.text)
            self.concept.anchors.extend(Anchor(anchor_id, span.line) for anchor_id in parser.ids)


def _markdown() -> MarkdownIt:
    return MarkdownIt("commonmark").use(footnote_plugin)


def _split(lines: list[str]) -> tuple[list[str] | None, int, str | None]:
    """Split off the frontmatter block.

    Returns:
        The frontmatter lines (None if absent), the 1-based first body line, and a problem message.
    """
    if not lines or lines[0].rstrip() != DELIMITER:
        return None, 1, "frontmatter must open with '---' on line 1"
    for index in range(1, len(lines)):
        if lines[index].rstrip() == DELIMITER:
            return lines[1:index], index + 2, None
    return None, 1, "frontmatter block is not closed with '---'"


def _read_frontmatter(concept: Concept, source: str) -> None:
    try:
        value, lines = parse_yaml(source)
    except YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 2 if mark is not None else 1
        concept.findings.append(Finding.make("OKF102", concept.path, line, f"frontmatter is not valid YAML: {exc}"))
        return
    if not isinstance(value, dict):
        concept.findings.append(Finding.make("OKF103", concept.path, 2, "frontmatter must be a YAML mapping"))
        return
    concept.frontmatter = value
    concept.key_lines = {key: line + 2 for key, line in lines.items()}


def parse_concept(text: str, path: str = "<memory>") -> Concept:
    """Parse the text of a concept file.

    Frontmatter problems are recorded in ``Concept.findings``; the body is parsed either way.

    Args:
        text: File contents (CRLF is accepted).
        path: Path used in findings.

    Returns:
        The parsed concept.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    concept = Concept(path=path)
    front, concept.body_first_line, problem = _split(lines)
    if problem:
        concept.findings.append(Finding.make("OKF101", path, 1, problem))
    if front is not None:
        _read_frontmatter(concept, "\n".join(front))
    concept.body_lines = lines[concept.body_first_line - 1 :]
    reader = _BodyReader(concept)
    reader.run(_markdown().parse("\n".join(concept.body_lines)))
    reader.finish()
    return concept


def load_concept(file: Path, display: str | None = None) -> Concept:
    """Read and parse a concept file from disk.

    Args:
        file: Path to the file.
        display: Path to show in findings; defaults to ``file`` as given.

    Returns:
        The parsed concept. A file that is not valid UTF-8 yields an OKF101 finding.
    """
    shown = display if display is not None else str(file)
    try:
        text = file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        concept = Concept(path=shown)
        concept.findings.append(Finding.make("OKF101", shown, 1, "file is not valid UTF-8"))
        return concept
    return parse_concept(text, shown)
