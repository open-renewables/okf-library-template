"""Check 3: body structure (SDD I-04, I-09 ``OKF3xx``).

Title heading, declared sections (presence, order, repeats, placeholders), section formats with their
children, the four-space nesting rule, raw HTML in prose, and the CI-managed *Revision history* section.
"""

from __future__ import annotations

from okfprofile.config import BodyDecl, FormatDecl, Profile, SectionDecl
from okfprofile.document import Concept, ListItem, Section
from okfprofile.report import Finding
from okfprofile.revision import parse_revision_line

NESTING_SPACES = 4
ALLOWED_TAG = "a"


def _title(body: BodyDecl, concept: Concept, title: object) -> list[Finding]:
    if body.title_heading != "h1_equals_title":
        return []
    h1s = [h for h in concept.headings if h.level == 1]
    line = h1s[0].line if h1s else concept.body_first_line
    if len(h1s) != 1:
        message = f"exactly one H1 heading is required (found {len(h1s)})"
        return [Finding.make("OKF301", concept.path, line, message)]
    if isinstance(title, str) and h1s[0].text != title:
        message = f"the H1 heading '{h1s[0].text}' must equal the title '{title}'"
        return [Finding.make("OKF301", concept.path, line, message)]
    return []


def _presence(body: BodyDecl, concept: Concept) -> list[Finding]:
    findings = []
    declared = {s.heading for s in body.sections}
    for decl in body.sections:
        found = [s for s in concept.sections if s.heading.text == decl.heading]
        if not found and decl.required:
            message = f"required section '{decl.heading}' is missing"
            findings.append(Finding.make("OKF302", concept.path, concept.body_first_line, message))
        findings.extend(
            Finding.make("OKF305", concept.path, s.heading.line, f"section '{decl.heading}' appears more than once")
            for s in found[1:]
        )
    if body.order == "strict":
        findings.extend(
            Finding.make("OKF304", concept.path, s.heading.line, f"section '{s.heading.text}' is not declared")
            for s in concept.sections
            if s.heading.text not in declared
        )
    return findings


def _order(body: BodyDecl, concept: Concept) -> list[Finding]:
    if body.order != "strict":
        return []
    rank = {s.heading: i for i, s in enumerate(body.sections)}
    findings = []
    highest = -1
    for section in concept.sections:
        position = rank.get(section.heading.text)
        if position is None:
            continue
        if position < highest:
            message = f"section '{section.heading.text}' is out of order; declared order: " + ", ".join(rank)
            findings.append(Finding.make("OKF303", concept.path, section.heading.line, message))
        highest = max(highest, position)
    return findings


def _html(concept: Concept) -> list[Finding]:
    findings = []
    for span in concept.html:
        text = span.text.lstrip()
        if text.startswith("<!--"):
            continue
        name = text.removeprefix("<").removeprefix("/").split(maxsplit=1)[0].rstrip(">/").lower() if text else ""
        if name != ALLOWED_TAG:
            message = f"raw HTML '{text[:30]}' in prose: write it as a code span or escape the angle brackets"
            findings.append(Finding.make("OKF313", concept.path, span.line, message))
    return findings


def _revision_history(concept: Concept, section: Section) -> list[Finding]:
    findings = [
        Finding.make("OKF314", concept.path, p.line, "the revision history holds CI-written lines only, not prose")
        for p in section.paragraphs
    ]
    for item in section.items:
        if parse_revision_line(item.text) is None or item.children:
            message = "not a valid revision line (SDD I-08); this section is maintained by CI and is not edited by hand"
            findings.append(Finding.make("OKF314", concept.path, item.line, message))
    if section.has_content and not section.items and not section.paragraphs:
        message = "the revision history holds CI-written list lines only"
        findings.append(Finding.make("OKF314", concept.path, section.heading.line, message))
    return findings


def _children(concept: Concept, fmt: FormatDecl, item: ListItem) -> list[Finding]:
    findings = []
    declared = [c.label for c in fmt.children]
    seen: list[str] = []
    for child in item.children:
        label, _, value = child.text.partition(":")
        label, value = label.strip(), value.strip()
        decl = next((c for c in fmt.children if c.label == label), None)
        if decl is None or label in seen:
            reason = "repeated" if label in seen else "unexpected"
            message = f"{reason} child '{label}'; expected: {', '.join(declared)}"
            findings.append(Finding.make("OKF310", concept.path, child.line, message))
            continue
        if seen and declared.index(label) < declared.index(seen[-1]):
            findings.append(Finding.make("OKF310", concept.path, child.line, f"child '{label}' is out of order"))
        seen.append(label)
        if decl.enum is not None and value not in decl.enum:
            message = f"'{value}' is not one of {', '.join(decl.enum)}"
            findings.append(Finding.make("OKF311", concept.path, child.line, message))
    findings.extend(
        Finding.make("OKF309", concept.path, item.line, f"required child '{c.label}' is missing")
        for c in fmt.children
        if c.required and c.label not in seen
    )
    return findings


def _nesting(concept: Concept, item: ListItem) -> list[Finding]:
    findings = []
    for child in item.children:
        if child.indent - item.indent != NESTING_SPACES:
            message = "nested list items are indented four spaces (two spaces render differently on the site)"
            findings.append(Finding.make("OKF312", concept.path, child.line, message))
        findings.extend(_nesting(concept, child))
    return findings


def _item(concept: Concept, fmt: FormatDecl, item: ListItem) -> list[Finding]:
    match = fmt.pattern.match(item.text)
    if match is None:
        message = f"list item does not match the '{fmt.name}' format: {item.text[:60]}"
        return [Finding.make("OKF307", concept.path, item.line, message)]
    findings = []
    for group, allowed in fmt.enums.items():
        value = match.group(group)
        if value not in allowed:
            message = f"'{value}' is not one of {', '.join(allowed)}"
            findings.append(Finding.make("OKF308", concept.path, item.line, message))
    if fmt.children:
        findings.extend(_children(concept, fmt, item))
    return findings


def _format(concept: Concept, fmt: FormatDecl, section: Section) -> list[Finding]:
    findings = []
    for item in section.items:
        findings.extend(_item(concept, fmt, item))
        if fmt.children:
            findings.extend(_nesting(concept, item))
    return findings


def _section(profile: Profile, body: BodyDecl, concept: Concept, decl: SectionDecl) -> list[Finding]:
    section = concept.section(decl.heading)
    if section is None:
        return []
    if decl.managed_by_ci:
        return _revision_history(concept, section)
    findings = []
    if not section.has_content:
        message = f"section '{decl.heading}' is empty; write content or the placeholder {body.empty_placeholder}"
        findings.append(Finding.make("OKF306", concept.path, section.heading.line, message))
    if decl.format:
        findings.extend(_format(concept, profile.formats[decl.format], section))
    return findings


def check_body(profile: Profile, concept: Concept) -> list[Finding]:
    """Run check 3 on one concept.

    A concept without parsed frontmatter, of an undeclared type, or of a type with no body declaration is
    left to the other checks.

    Args:
        profile: The loaded profile.
        concept: The parsed concept.

    Returns:
        Findings for the title heading, sections, formats, nesting, raw HTML and the revision history.
    """
    frontmatter = concept.frontmatter
    declared = profile.type_named(str(frontmatter.get("type"))) if frontmatter else None
    if frontmatter is None or declared is None or declared.body is None:
        return []
    body = declared.body
    findings = _title(body, concept, frontmatter.get("title"))
    findings.extend(_presence(body, concept))
    findings.extend(_order(body, concept))
    for decl in body.sections:
        findings.extend(_section(profile, body, concept, decl))
    findings.extend(_html(concept))
    return findings
