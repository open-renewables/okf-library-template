# Site rendering: where the site differs from the validator

Closes known gap G2 (build phase P3, 2026-11-12). The validator reads Markdown with markdown-it-py (CommonMark and footnotes); the site renders with Python-Markdown (MkDocs and Zensical). V-02 proved four-space nesting identical. This page lists the other constructs compared, with the fixture `tests/template/fixtures/site/knowledge/group-b/constructs.md` and the test `test_the_markdown_divergences_between_the_validator_and_the_site_are_the_recorded_ones`.

Both site builders give the same HTML for every construct below (MkDocs 1.6.1 with Material 9.7.7 and Zensical 0.1.1).

## Agreement

| Construct | Validator and site |
| --- | --- |
| Table | Both read a pipe table as a table (the validator's profile parser does not enable tables, so a profile format never reads a table as items) |
| Inline HTML next to Markdown | Both keep `<span class="x">` and read the emphasis and code beside it |
| Ordered list with a nested bullet (four-space indent) | Both nest it |
| Footnote reference and definition | Both resolve; the site links back |
| Angle brackets, braces, explicit anchors, relative links, colon-namespaced tags, reserved keys | The six FR8.2 checks in `test_site.py` |

## Divergences

| # | Construct | Validator (CommonMark) | Site (Python-Markdown) | Effect |
| --- | --- | --- | --- | --- |
| D1 | A list that follows a paragraph with no blank line between | Starts a list | Keeps the lines as paragraph text, with a literal `- ` | A profile section parsed as items (for example *Checks*) is validated as a list but renders as text. GitHub renders a list |
| D2 | A list inside a footnote definition | Reads it as a nested list | Folds it into the footnote's paragraph | Footnote text with a list renders flat |

## Consequence

Write a blank line before every list, and keep a footnote definition to one paragraph. Nothing enforces either today: the validator accepts D1 and D2. A new warning kind would need an SDD edit (I-02 warning kinds), so it is proposed in the P3 plan as PP-9 for the owner, not built.
