# Finding codes

Catalogue of the validation finding codes of SDD I-09. The registry in `scripts/okfprofile/codes.py` is the source; this file mirrors it with the fixture that proves each code. A code is stable once defined and is never reused. Ranges follow I-09:

| Range | Check |
| --- | --- |
| `OKF0xx` | Change rules: mixed tooling and content changes; `profile-migration` conditions |
| `OKF1xx` | 1. OKF conformance (okf-skills findings mapped; frontmatter-first; datetime offsets) |
| `OKF2xx` | 2. Frontmatter schema; unknown fields; declared type |
| `OKF3xx` | 3. Body sections, order, placeholders, formats, CI-managed sections |
| `OKF4xx` | 4. Links, anchors, vocabulary membership, path rules |
| `OKF5xx` | 5. Index freshness |
| `OKF6xx` | 6. Identifier and registry integrity |
| `OKF7xx` | Publishing rules (approval, citation) |
| `OKF8xx` | Profile-declared warnings |
| `OKF9xx` | Revision completeness (declared in P2 with the revision writer) |

## Codes defined

| Code | Level | Check | Meaning | Fixture |
| --- | --- | --- | --- | --- |
| OKF101 | error | 1 | Frontmatter block missing, not on line 1, or not closed | `tests/library/fixtures/fail/OKF101/` |
| OKF102 | error | 1 | Frontmatter is not valid YAML | `tests/library/fixtures/fail/OKF102/` |
| OKF103 | error | 1 | Frontmatter is not a mapping | `tests/library/fixtures/fail/OKF103/` |
| OKF104 | error | 1 | Required `type` key missing or empty | `tests/library/fixtures/fail/OKF104/` |
| OKF111 | warning | 1 | Legacy OKF v0.1 construct | `tests/library/fixtures/fail/OKF111/` |
| OKF113 | warning | 1 | Actor does not follow the OKF actor convention | `tests/library/fixtures/fail/OKF113/` |
| OKF116 | warning | 1 | `usage_count` has no window, or a footnote matches no `sources[].id` | `tests/library/fixtures/fail/OKF116/` |
| OKF117 | warning | 1 | Reserved file (`index.md`, `log.md`) breaks OKF section 8, 9 or 12 | `tests/library/fixtures/fail/OKF117/` |
| OKF118 | warning | 1 | Attested Computation contract field is missing or dangling | unit test, `tests/template/test_conformance.py` (see known gaps) |
| OKF119 | warning | 1 | okf-skills reported a message this tool does not map | unit test, `tests/template/test_conformance.py` (see known gaps) |
| OKF120 | error | 1 | Timestamp is not an ISO 8601 datetime with an explicit UTC offset | `tests/library/fixtures/fail/OKF120/` |
| OKF201 | error | 2 | Concept type is not declared in the profile | `tests/library/fixtures/fail/OKF201/` |
| OKF202 | error | 2 | Required frontmatter field missing | `tests/library/fixtures/fail/OKF202/` |
| OKF203 | error | 2 | Unknown frontmatter field (the profile rejects them) | `tests/library/fixtures/fail/OKF203/` |
| OKF204 | error | 2 | Frontmatter value does not satisfy the type schema | `tests/library/fixtures/fail/OKF204/` |
| OKF205 | error | 2 | `status` is not declared in the profile | `tests/library/fixtures/fail/OKF205/` |
| OKF401 | error | 4 | Internal link starts with `/`; internal links are relative | `tests/library/fixtures/fail/OKF401/` |
| OKF402 | error | 4 | Internal link target does not exist in the bundle | `tests/library/fixtures/fail/OKF402/` |
| OKF403 | error | 4 | Link fragment matches no heading or explicit anchor in its target | `tests/library/fixtures/fail/OKF403/` |
| OKF404 | error | 4 | Anchor misuse: upper-case id, `{#id}` syntax, or a repeated explicit id | `tests/library/fixtures/fail/OKF404/` |
| OKF405 | error | 4 | Tag does not match the tag pattern or names an undeclared namespace | `tests/library/fixtures/fail/OKF405/` |
| OKF406 | error | 4 | Tag value is not in its vocabulary | `tests/library/fixtures/fail/OKF406/` |
| OKF407 | error | 4 | Vocabulary concept missing or malformed | `tests/library/fixtures/fail/OKF407/` |
| OKF408 | error | 4 | Path rule violated | `tests/library/fixtures/fail/OKF408/` |
| OKF409 | warning | 4 | Tag value restates a folder name | `tests/library/fixtures/fail/OKF409/` |
| OKF410 | error | 4 | Concept is outside the paths declared for its type | `tests/library/fixtures/fail/OKF410/` |
| OKF411 | error | 4 | Explicit anchor present in the base is gone | `tests/library/fixtures/fail/OKF411/` |
| OKF301 | error | 3 | Title heading missing, repeated, or different from `title` | `tests/library/fixtures/fail/OKF301/` |
| OKF302 | error | 3 | Required body section missing | `tests/library/fixtures/fail/OKF302/` |
| OKF303 | error | 3 | Body section out of the declared order | `tests/library/fixtures/fail/OKF303/` |
| OKF304 | error | 3 | Body section not declared for the type | `tests/library/fixtures/fail/OKF304/` |
| OKF305 | error | 3 | Body section appears more than once | `tests/library/fixtures/fail/OKF305/` |
| OKF306 | error | 3 | Body section is empty and does not hold the placeholder | `tests/library/fixtures/fail/OKF306/` |
| OKF307 | error | 3 | List item does not match its section format | `tests/library/fixtures/fail/OKF307/` |
| OKF308 | error | 3 | List item value is not among the format's allowed values | `tests/library/fixtures/fail/OKF308/` |
| OKF309 | error | 3 | Required child of a format item missing | `tests/library/fixtures/fail/OKF309/` |
| OKF310 | error | 3 | Child of a format item unexpected, repeated or out of order | `tests/library/fixtures/fail/OKF310/` |
| OKF311 | error | 3 | Child value is not among the allowed values | `tests/library/fixtures/fail/OKF311/` |
| OKF312 | error | 3 | Nested list item is not indented four spaces | `tests/library/fixtures/fail/OKF312/` |
| OKF313 | error | 3 | Raw HTML in prose; write it as a code span or escape it | `tests/library/fixtures/fail/OKF313/` |
| OKF314 | error | 3 | CI-managed section holds something other than valid revision lines | `tests/library/fixtures/fail/OKF314/` |
| OKF601 | error | 6 | Concept has no `uid` | `tests/library/fixtures/fail/OKF601/` |
| OKF602 | error | 6 | `uid` is malformed or its prefix does not match the type | `tests/library/fixtures/fail/OKF602/` |
| OKF603 | error | 6 | `uid` is used by more than one concept | `tests/library/fixtures/fail/OKF603/` |
| OKF604 | error | 6 | Concept's `uid` is not in the registry | `tests/library/fixtures/fail/OKF604/` |
| OKF605 | error | 6 | Concept path differs from the registry and the move is not approved | `tests/library/fixtures/fail/OKF605/` |
| OKF606 | error | 6 | A concept's `uid` changed since the base | `tests/library/fixtures/fail/OKF606/` |
| OKF607 | error | 6 | A `uid` present in the base is gone (concept deleted or registry entry removed) | `tests/library/fixtures/fail/OKF607/` |
| OKF608 | error | 6 | Registry entry has no matching concept, or its type differs | `tests/library/fixtures/fail/OKF608/` |

Codes for the change rules (`OKF0xx`), the publishing rules (`OKF7xx`), the profile warnings (`OKF8xx`) and index freshness (`OKF5xx`) are added with the step that implements each (`../plan/plan.md`, P1 steps 8 and 9), together with their failing fixtures. Codes not listed above are unassigned; a retired number is never reused (`OKF110` and `OKF112` were dropped before the first release because the profile schema owns what they covered).

## Reading rules

- **YAML.** Frontmatter is YAML 1.2 with the timestamp type disabled: `no` and dates stay strings; numbers and `true`/`false` keep their types. Findings carry the 1-based file line of the offending key, or the line where the parser stopped.
- **Levels.** `error` blocks; `warning` never fails a run. The `low` and `medium` priority of a profile warning (I-02) is separate from the level.
