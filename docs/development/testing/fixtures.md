# Fixture catalogue

What each fixture folder under `tests/library/fixtures/` proves. [finding-codes.md](../architecture/finding-codes.md) gives the meaning of each code; this file explains how a fixture is built. The runner is `tests/library/test_fixtures.py`.

## Layout

```
tests/library/fixtures/
├── pass/<name>/      must validate with no error
└── fail/<code>/      must raise exactly the finding code in the folder name
```

Each folder is a miniature repository: `knowledge/` is the bundle under test and the other entries below are what the runner overlays on the real `profile/`.

## Conventions the runner understands

| Entry in the fixture | Effect |
| --- | --- |
| `knowledge/...` | The bundle under test, copied to a scratch folder |
| `profile/...` | Overlay on the library's `profile/`. Almost every fixture holds `profile/uid-registry.yaml` for its concepts. A fixture may also replace `profile.yaml`, a schema or a format to exercise a rule the template profile does not use |
| `base/knowledge/...`, `base/profile/...` | The repository at the base commit, also overlaid on the real `profile/`. Needed by rules that compare with the base: revision history only grows (`OKF315`), explicit anchors stay (`OKF411`), `uid` unchanged and present, path moves (`OKF605` to `OKF607`) |
| `change.json` | A change proposal read by `ChangeContext.from_file`: `paths`, `labels`, `author`, `head_sha`, `reviews` (each `login`, `approved`, `commit_id`), `agent_markers`, `revision_bot`, `reviews_known`. Drives the change rules (`OKF0xx`), the publishing pre-check (`OKF7xx`) and the agent-label warning (`OKF802`) |
| `CODEOWNERS` | Copied to `.github/CODEOWNERS`; gives directory owners to the pre-check and the migration approval |
| `no-indexes` | Empty marker. Without it the runner generates any missing `index.md` first, so a fixture shows an index problem only when it says so (`OKF501` to `OKF504`) |

## Passing fixtures

| Folder | Proves |
| --- | --- |
| `pass/item` | An Item validates |
| `pass/vocabulary` | A Vocabulary concept validates |
| `pass/glossary` | A Glossary concept validates |
| `pass/stable` | A concept made `stable` with an approving review of the current head by another login passes the publishing pre-check |
| `pass/migration` | A `profile-migration` change with a maintainer approval passes the change rules (FR2.6) |
| `pass/approved-move` | A path change against `base/` passes when the change carries the approved-move label (FR1.5) |
| `pass/revision-append` | Appending a revision line against `base/` passes the history-only-grows check (FR3.4) |

`pass/item`, `pass/vocabulary` and `pass/glossary` give each declared type a passing fixture (SPEC done-when 3).

## Failing fixtures

Each `fail/<code>/` is the smallest bundle that breaks one rule. The catalogue gives the rule per code; construction notes by group:

| Codes | Check | Notes |
| --- | --- | --- |
| `OKF001` to `OKF003` | Change rules | `change.json` lists tooling and content paths (`OKF001`), or a migration lacking the maintainer approval (`OKF002`) or the `DECISIONS.md` change (`OKF003`, which also holds `CODEOWNERS`) |
| `OKF101` to `OKF104`, `OKF111` to `OKF117`, `OKF120` | 1 OKF conformance | Frontmatter faults, or text the vendored okf-skills validator reports and the mapper turns into a code. `OKF120` is `okfprofile`'s own offset rule |
| `OKF118`, `OKF119` | 1 | No fixture; unit tests only (see [known-gaps.md](known-gaps.md)) |
| `OKF201` to `OKF205` | 2 Frontmatter schema | Undeclared type, missing field, unknown field, schema violation, undeclared `status` |
| `OKF301` to `OKF314` | 3 Body structure | Title heading, section presence, order, repeats, undeclared sections, placeholders, format items and children, nesting, raw HTML, revision-section grammar |
| `OKF315` | 3 | Has `base/`; the working tree changes existing revision history |
| `OKF401` to `OKF411` | 4 Links, anchors, vocabularies, paths | `OKF411` has `base/` with an explicit anchor that is gone |
| `OKF501` to `OKF504` | 5 Indexes | `OKF501` and `OKF502` carry `no-indexes` so the index fault is not repaired before validation; `OKF504` overlays a lower folder limit in `profile/` |
| `OKF601` to `OKF608` | 6 Identifiers | `OKF605` to `OKF607` have `base/`; `OKF605` has no approved-move label |
| `OKF701` to `OKF703` | Publishing rules | `change.json` with review data; `OKF701` and `OKF702` add `CODEOWNERS` |
| `OKF801` to `OKF804` | Profile warnings | A `profile/` overlay enables the warning where the template profile does not; `OKF802` is driven by `agent_markers` in `change.json` |

The runner collects findings of both levels, so warning codes (`OKF111`, `OKF113`, `OKF116`, `OKF117`, `OKF409`, `OKF504`, `OKF702`, `OKF801` to `OKF804`) pass `test_failing_fixture_raises_exactly_its_code` while never failing a real run.

## Not fixtures

Golden files (`tests/template/golden/`) and the unit-only proofs are described in [strategy.md](strategy.md). `tests/template/test_catalogue.py` checks that every path in the finding-code table exists.
