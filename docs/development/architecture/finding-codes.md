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
| OKF101 | error | 1 | Frontmatter missing, not opening on line 1, not closed, or the file is not valid UTF-8 | Unit tests in `tests/template/test_document.py`; library fixture added with check 1 (P1 step 4) |
| OKF102 | error | 1 | Frontmatter is not valid YAML, including a duplicate key | as OKF101 |
| OKF103 | error | 1 | Frontmatter is not a mapping | as OKF101 |

Codes for the remaining checks are added with the step that implements each check (`../plan/plan.md`, P1 steps 4 to 9), together with their failing fixtures under `tests/library/fixtures/fail/<code>/`.

## Reading rules

- **YAML.** Frontmatter is YAML 1.2 with the timestamp type disabled: `no` and dates stay strings; numbers and `true`/`false` keep their types. Findings carry the 1-based file line of the offending key, or the line where the parser stopped.
- **Levels.** `error` blocks; `warning` never fails a run. The `low` and `medium` priority of a profile warning (I-02) is separate from the level.
