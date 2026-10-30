# Todo: build phase P1

Checklist for `plan.md`; scope and done-when in `SPEC.md`. Tick an item when its check in `plan.md` has passed and the evidence (command and result) is noted in the Outcomes table. **NEEDS YOU** marks a decision, person, account, machine or setting from the owner. Nothing is committed, pushed or merged without the owner's instruction.

## Before any step

- [x] Owner reviews `SPEC.md`, `plan.md` and `todo.md`
- [x] **NEEDS YOU (decision):** owner answers OD-1 to OD-10 or accepts the defaults (defaults accepted 2026-10-31) (`plan.md`, "Open decisions")
- [x] **NEEDS YOU (decision):** owner approves or rejects PP-1 to PP-6 (approved as drafted 2026-10-31; ADR text reviewed when written) (`plan.md`, "Proposed entries")
- [x] Merge order with PR [#8](https://github.com/open-renewables/okf-library-template/pull/8) settled (OD-6)

## PR 1: skeleton (`tooling/p1-skeleton`)

- [x] 1. `pyproject.toml`, groups, poe tasks, ruff, mypy, pytest, coverage, `uv.lock`, `.python-version`, `.gitattributes`, smoke test
- [x] 1. Check: fresh-clone `uv sync`; `poe check` and `poe test` pass on 3.11 and 3.14; no `w/crlf` after clone with autocrlf true and false; lock licences on the allowlist (PP-3 if `pathspec` is in `dev`)

## PR 2: core (`tooling/p1-core`)

- [x] 2. `config`, `document`, `report`; finding catalogue started
- [x] 2. Check: reader unit tests (YAML 1.2 strings, CRLF, nesting, footnotes, anchors); JSON and annotation output agree
- [x] 3. Profile, meta-schemas, base and type schemas, formats
- [x] 3. Check: profile validates; one rejecting fixture per schema rule; no domain value in `scripts/`

## PR 3: checks 1 to 3 (`tooling/p1-checks-1-3`)

- [ ] 4. Vendored okf-skills (verbatim, licences, hash record); message-to-`OKF1xx` mapper; frontmatter-first and datetime-offset; schema check (PP-1 decided)
- [ ] 4. Check: failing fixture per code; every pinned message maps; vendored hash equals upstream; PyYAML and ruamel disagreement test
- [ ] 5. Check 3: sections, order, placeholders, formats, CI-managed section, two-space nesting, angle-bracket prose
- [ ] 5. Check: failing fixture per code; hand-edited, deleted and out-of-grammar revision lines fail

## PR 4: checks 4 to 6 (`tooling/p1-checks-4-6`)

- [ ] 6. `vocab`; relative-only links; case-insensitive anchors with lower-case ids; glossary anchor stability; tags; path rules
- [ ] 6. Check: failing fixture per code; `%20` and angle-bracket links resolve; upper-case id and changed glossary anchor fail
- [ ] 7. `registry`, check 6, `new_concept.py`, `renumber.py`, `--fix-registry`
- [ ] 7. Check: failing fixture per code; duplicate `uid` from two local branches cleared by `renumber.py`; `new_concept.py` output passes all checks

## PR 5: indexes, change rules, entry points (`tooling/p1-indexes-changes`)

- [ ] 8. `indexes` with relative links (PP-2 decided); revision line parser and tier derivation; `build_indexes.py --check`
- [ ] 8. Check: golden indexes; golden tiers for every I-08 case; second run is a no-op; stale index fails check 5
- [ ] 9. `changes`, `--tooling-from`, `codeowners`, publishing pre-check, four warning kinds, base-diff rules
- [ ] 9. Check: FR2.5 and FR2.6 fixtures; two-folder change records two owner statuses; pre-check branch fixtures; warnings do not fail
- [ ] 10. Thin scripts, `ci-validate` task
- [ ] 10. Check: `--help`, `--json`, exit codes tested; local and `ci-validate` JSON identical

## PR 6: example bundle, content only (`concept/p1-example-bundle`)

- [ ] 11. One example per declared type (OD-1), vocabularies, glossary entries, generated indexes, registry, passing fixtures
- [ ] 11. Check: no error on `knowledge/`; `build_indexes.py --check` clean; passing fixture per type

## PR 7: exit (`tooling/p1-exit`)

- [ ] 12. `.pre-commit-config.yaml` (local hooks); 600-concept timing
- [ ] 12. Check: hooks refuse a bad commit in Git Bash and PowerShell; time recorded
- [ ] 13. `testing/strategy.md`, `fixtures.md`, `known-gaps.md`; finding catalogue finished
- [ ] 13. Check: every code has a catalogue row and fixture path (test fails otherwise); links resolve
- [ ] 14. Full gate on 3.11 and 3.14; coverage figure; P2 to P4 estimate revised (proposal)

## Exit

- [ ] SPEC "Done when" items 1 to 8 ticked with evidence
- [ ] **NEEDS YOU (person):** owner pushes annotated tag `v0.1.0` (alpha) on `main` (OD-10)
- [ ] Proposed entries PP-1 to PP-6 decided and, where approved, applied as their own ADR or documented edit
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p1-core-tooling/`; the SRS status is not changed

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |
| 1 | Skeleton built, uncommitted on `tooling/p1-skeleton`. `poe check` and `poe test` pass on 3.11.15, 3.12.10, 3.14.0; fresh clone with autocrlf true and false has 0 CRLF files and passes. Matrix needs `UV_PYTHON` and `UV_PROJECT_ENVIRONMENT` set (a bare `uv run --python` fails on Windows). Lock has 36 packages. Licences: `pathspec` 1.1.1 (MPL-2.0, via mypy) is in `dev`; `nodeenv` ("BSD") and `colorama` ("BSD License") have non-SPDX metadata. Windows-only `colorama`/`nodeenv` come from pre-commit, pytest and poethepoet | [Test] | PP-3 raised; non-SPDX pair to resolve with it |
| 2 | `codes`, `report`, `document`, `config` built in `scripts/okfprofile/`. 94 tests pass on 3.11, 3.12, 3.14; coverage 99.75 %; ruff and mypy strict clean. YAML 1.2 needed the timestamp constructor overridden (ruamel resolves dates even in 1.2 mode). `jsonschema` needs `types-jsonschema` in `dev` (Apache-2.0) | [Test] | PP-7 |
| 3 | `profile/profile.yaml` (Item ITM, Vocabulary VOC, Glossary GLS; OD-1), meta-schemas for profile, format and registry, OKF base schema from the pinned spec, three type schemas, `check` format. Loader reports all problems with file and line; 25 mutation tests. The scripts hold no type name, prefix, namespace or format name (tested) | [Test] | PP-7 |
| 4 |  |  |  |
| 5 |  |  |  |
| 6 |  |  |  |
| 7 |  |  |  |
| 8 |  |  |  |
| 9 |  |  |  |
| 10 |  |  |  |
| 11 |  |  |  |
| 12 |  |  |  |
| 13 |  |  |  |
| 14 |  |  |  |
| Actual effort | P1 person-days against 11–16 |  | P2–P4 re-estimate |
