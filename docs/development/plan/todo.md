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

- [x] 4. Vendored okf-skills (verbatim, licences, hash record); message-to-`OKF1xx` mapper; frontmatter-first and datetime-offset; schema check (PP-1: ADR-008 drafted, awaiting acceptance)
- [x] 4. Check: failing fixture per code; every pinned message maps; vendored hash equals upstream; PyYAML and ruamel disagreement test
- [x] 5. Check 3: sections, order, placeholders, formats, CI-managed section, two-space nesting, angle-bracket prose
- [x] 5. Check: failing fixture per code; hand-edited, deleted and out-of-grammar revision lines fail

## PR 4: checks 4 to 6 (`tooling/p1-checks-4-6`)

- [x] 6. `vocab`; relative-only links; case-insensitive anchors with lower-case ids; glossary anchor stability; tags; path rules
- [x] 6. Check: failing fixture per code; `%20` and angle-bracket links resolve; upper-case id and changed glossary anchor fail
- [x] 7. `registry`, check 6, `new_concept.py`, `renumber.py`, `--fix-registry`
- [x] 7. Check: failing fixture per code; duplicate `uid` from two local branches cleared by `renumber.py`; `new_concept.py` output passes all checks

## PR 5: indexes, change rules, entry points (`tooling/p1-indexes-changes`)

- [x] 8. `indexes` with relative links (PP-2 decided); revision line parser and tier derivation; `build_indexes.py --check`
- [x] 8. Check: golden indexes; golden tiers for every I-08 case; second run is a no-op; stale index fails check 5
- [x] 9. `changes`, `--tooling-from`, `codeowners`, publishing pre-check, four warning kinds, base-diff rules
- [x] 9. Check: FR2.5 and FR2.6 fixtures; two-folder change records two owner statuses; pre-check branch fixtures; warnings do not fail
- [x] 10. Thin scripts, `ci-validate` task
- [x] 10. Check: `--help`, `--json`, exit codes tested; local and `ci-validate` JSON identical

## PR 6: example bundle, content only (`concept/p1-example-bundle`)

- [x] 11. One example per declared type (OD-1), vocabularies, glossary entries, generated indexes, registry, passing fixtures
- [x] 11. Check: no error on `knowledge/`; `build_indexes.py --check` clean; passing fixture per type

## PR 7: exit (`tooling/p1-exit`)

- [x] 12. `.pre-commit-config.yaml` (local hooks); 600-concept timing
- [x] 12. Check: hooks refuse a bad commit in Git Bash and PowerShell; time recorded
- [x] 13. `testing/strategy.md`, `fixtures.md`, `known-gaps.md`; finding catalogue finished
- [x] 13. Check: every code has a catalogue row and fixture path (test fails otherwise); links resolve
- [x] 14. Full gate on 3.11, 3.12 and 3.14; coverage figure; P2 to P4 estimate revised (proposal, below)

## Exit

- [x] SPEC "Done when" items 1 to 8 met (evidence table below): items 1 to 7 at PR 7 ([#17](https://github.com/open-renewables/okf-library-template/pull/17), merged as `10e2d3a`); item 8 by the tag and the re-estimate proposal
- [x] **NEEDS YOU (person):** owner pushed annotated tag `v0.1.0` (alpha) on `main` (OD-10): tag object `88e9ab0` points at `10e2d3a`, present on `origin` (`git ls-remote --tags origin v0.1.0`), message "v0.1.0 (alpha): P1 core tooling"
- [x] Proposed entries PP-1 to PP-6 decided and, where approved, applied (status table below). PP-7 (raised in step 3) is not part of that line and is still open
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p1-core-tooling/`; the SRS status is not changed

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |
| 1 | Skeleton built, uncommitted on `tooling/p1-skeleton`. `poe check` and `poe test` pass on 3.11.15, 3.12.10, 3.14.0; fresh clone with autocrlf true and false has 0 CRLF files and passes. Matrix needs `UV_PYTHON` and `UV_PROJECT_ENVIRONMENT` set (a bare `uv run --python` fails on Windows). Lock has 36 packages. Licences: `pathspec` 1.1.1 (MPL-2.0, via mypy) is in `dev`; `nodeenv` ("BSD") and `colorama` ("BSD License") have non-SPDX metadata. Windows-only `colorama`/`nodeenv` come from pre-commit, pytest and poethepoet | [Test] | PP-3 raised; non-SPDX pair to resolve with it |
| 2 | `codes`, `report`, `document`, `config` built in `scripts/okfprofile/`. 94 tests pass on 3.11, 3.12, 3.14; coverage 99.75 %; ruff and mypy strict clean. YAML 1.2 needed the timestamp constructor overridden (ruamel resolves dates even in 1.2 mode). `jsonschema` needs `types-jsonschema` in `dev` (Apache-2.0) | [Test] | PP-7 |
| 3 | `profile/profile.yaml` (Item ITM, Vocabulary VOC, Glossary GLS; OD-1), meta-schemas for profile, format and registry, OKF base schema from the pinned spec, three type schemas, `check` format. Loader reports all problems with file and line; 25 mutation tests. The scripts hold no type name, prefix, namespace or format name (tested) | [Test] | PP-7 |
| 4 | okf-skills vendored verbatim at `a8b96420` (blob hash recorded and tested; MIT and spec-notice texts carried). A test reads every message string out of the vendored source with `ast` and fails on any that the mapper cannot place, so a re-pin is caught. Of the 36 message sites in the file, 19 map to nine codes and 17 are dropped because check 2 or check 4 owns them. Check 2 de-duplicates repeated required-field errors. Datetime rule is `OKF120`; check 2 skips the same keys. 28 fail fixtures and 3 pass fixtures run through `validate_bundle` and each fail fixture raises exactly its code; `OKF118` and `OKF119` are proven by unit tests only (the template profile has no Attested Computation type, and the pinned script never emits an unknown message) | [Test] | PP-1 (ADR-008) |
| 5 | Check 3 covers title heading, section presence, order, repeats and undeclared sections, placeholders, formats with children and enums, four-space nesting, raw HTML and the CI-managed revision history. The revision-line grammar (`revision.py`) moved here from step 8 because the revision-history check needs it; tier derivation stays in step 8. Reader extended with per-section paragraphs and content flag. 197 tests, 99.6 % coverage on 3.11, 3.12, 3.14 | [Test] | none |
| 6 | Check 4 in `checks/links.py`, `checks/tags.py` and `vocab.py`: root-relative links (ADR-005), missing targets, fragments compared without regard to case, `{#id}` and upper-case ids, tag shape and vocabulary membership, four path-rule kinds, type `paths`. Explicit anchors present in the base must remain (`OKF411`). Reader gained `Concept.top_items`. Check 2 no longer reports tag-pattern or `uid` errors (check 4 and check 6 own them). `OKF404` does not try to tie an explicit id to a particular heading: the SDD does not say where the anchor sits relative to its heading | [Test] | none |
| 7 | `registry.py` (canonical YAML, next number never reused, cap at 9,999, `apply_moves`, `renumber`), check 6 (`OKF601` to `OKF608`; a duplicated `uid` suppresses the registry findings for it), `scaffold.py` (`create_concept`, `renumber_concept`, CRLF-safe). The command-line wrappers `new_concept.py` and `renumber.py` are step 10. Two local-branch clash exercised without git: both concepts take `ITM-0001`, `OKF603` fires, `renumber_concept` moves the later one to `ITM-0002` and validation is clean. 47 fail and 4 pass fixtures; fixtures with `base/` and an `approved-move` marker cover the checks that compare against the base. 263 tests, 99.7 % coverage on 3.11, 3.12, 3.14 | [Test] | none |
| 8 | `indexes.py` writes one `index.md` per folder with relative links, status and tier on each concept line, root index with `okf_version`; `revision.py` holds the I-08 tier rules and `history.py` reads a concept's lines. 16 golden tier cases and 4 golden index files. Folder lines carry the folder title only (OD-1: the SDD defines no scope note). Check 5 gives `OKF501` to `OKF504`; the harness generates missing indexes unless a fixture says `no-indexes`. The SDD I-07 example links are now relative (PP-2 applied, DDR change-log row added) | [Test] | PP-2 |
| 9 | `changes.py` (mixed-change rule, migration conditions, `ChangeContext`), `codeowners.py` (last match wins, per-file owners), publishing pre-check (`OKF701` to `OKF703`, review data supplied, skipped when none is known), four profile warnings (`OKF801` to `OKF804`), history-only-grows check (`OKF315`, matches a moved concept by `uid`). `--tooling-from` stages the base's `scripts/` and `profile/`, copies this tree's bundle and registry, and runs the base's own `validate_profile.py`. Fixtures can carry `change.json` and `CODEOWNERS` | [Test] | none |
| 10 | `cli.py` plus four thin scripts; `poe check` now runs `validate_profile.py` and `build_indexes.py --check`; `poe ci-validate` runs `--tooling-from` and `--base`. FR2.5 test uses a real scratch git repository: with a relaxed profile and a non-conforming concept the plain run passes and the `--tooling-from HEAD` run fails with `OKF203`. A local run and a `--tooling-from HEAD --base HEAD` run give identical JSON. `tests/template/test_cli.py` runs the commands in process against scratch repositories | [Test] | none |
| 11 | Example bundle built with `new_concept.py` then filled: `example-item` (Item, with `Checks` children at four spaces, footnote citation, relative links), `vocab/group` and `vocab/category`, `glossary` (term with lower-case `<a id>`); indexes by `build_indexes.py`; registry by the tool. `validate_profile.py` 0 errors, 0 warnings; vendored okf-skills reports conformant (FR1.1; 7 recommended-field warnings only, `tags` and `generated`); `build_indexes.py --check` clean; `poe check` and `poe test` pass (349 tests, 98.95 %). No new fixtures: `tests/library/fixtures/pass/` already covers all three types | [Test] | none |
| 12 | `.pre-commit-config.yaml` with four `repo: local` hooks run through `uv run`: `ruff check --fix`, `ruff format` (both with `--force-exclude`, so the vendored folder is skipped), `validate_profile.py --changed`, `build_indexes.py --check`; no `scan.py` hook (OD-2). In a scratch clone outside the repo: Git Bash and PowerShell both refused a commit with an undeclared `status` (`OKF205`, plus `OKF502` for the stale index), ruff fixed and refused a badly formatted Python file, and clean commits passed. 600 generated Items (604 concept files): `validate_profile.py` 2.05–2.28 s, `build_indexes.py --check` 1.23–1.27 s, wall-clock including `uv run` start-up, one Windows machine; target under 10 s (`testing/performance.md`). The generator ran 246 s because `create_concept` reloads the bundle per concept; scaffolder cost only | [Test] | none |
| 13 | `testing/strategy.md`, `fixtures.md`, `known-gaps.md` (G1–G10) and `performance.md` written; `finding-codes.md` already complete from earlier steps. New `tests/template/test_catalogue.py` (3 tests): every code in `codes.py` has a catalogue row and no row is unknown (64 codes), every listed fixture or test path exists, relative links in `testing/` resolve. It caught a missing `performance.md` link on its first run | [Test] | none |
| 14 | Full gate on Python 3.11.15, 3.12.10, 3.14.0 with `UV_PYTHON` and `UV_PROJECT_ENVIRONMENT=.venv-<ver>`: `poe check` clean (ruff, mypy strict on 28 files, mypy on 22, `validate_profile.py` 0 errors, indexes clean) and `poe test` 352 passed, coverage 98.95 % (floor 85 %), on each. `constraints.md` unchanged. Done-when 1–7: (1) above; (2) 64 codes catalogued, `test_failing_fixture_raises_exactly_its_code` covers 62 fail folders, `OKF118`/`OKF119` by unit test (known gap G5); (3) example bundle 0 errors, indexes clean, `pass/item`, `pass/vocabulary`, `pass/glossary`; (4) `tiers.json` golden (16 cases) and 4 golden indexes; (5) FR2.5 scratch-repo test and `OKF001` plus `pass/migration`; (6) `test_cli.py` parity test; (7) the three testing files and the catalogue. Item 8: tag and re-estimate below | [Test] | none |
| Actual effort | Seven pull requests merged between 2026-10-31 and 2026-11-03 (#11 to #17) after the P0 outcomes of 2026-10-30. Person-days were not logged by any session; the owner states the figure against the plan's 10.25–15 (SDD 11–16) | [Inf] | P2–P4 re-estimate below |

### Status of proposed entries (checked 2026-11-03 against `main` at `10e2d3a`)

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Decided and applied | `adr/ADR-008-vendored-code-lint-exemption.md` Accepted (owner, 2026-10-31); `constraints.md` line 24 excludes `scripts/vendor/` from ruff |
| PP-2 | Decided and applied | SDD I-07 example links relative; DDR change-log row dated 2026-10-31 |
| PP-3 | Decided and applied | `adr/ADR-007-dev-group-licence-resolutions.md` Accepted (owner, 2026-10-31) |
| PP-4 | Applied | `architecture/finding-codes.md` assigns and mirrors all 64 codes; checked by `test_catalogue.py` |
| PP-5 | Not triggered | The owner accepted the OD-2 and OD-3 defaults; `scan.py` and the `requirements/` export are P2 and are listed as known gaps G7 |
| PP-6 | Applied | Line grammar plus base-diff (`OKF314`, `OKF315`); limits recorded in `testing/known-gaps.md` G4 and, as a note, in `architecture/finding-codes.md` (Reading rules). No stronger rule was asked for |
| PP-7 | **Open** | Raised in step 3; the SDD I-02 to I-04 wording additions and a DDR change-log row are not applied. Needs the owner's decision |

### P2 to P4 re-estimate (proposal; the SDD is not edited)

SDD §14 carries P2 9.5–14.5, P3 5–7, P4 5–8 (19.5–29.5 together). P1 ran as seven pull requests and the step ranges in `plan.md` held; days actually spent were not logged by the session that did steps 12 to 14, so the "Actual effort" cell is for the owner to fill. Proposed changes from what P1 found:

| Phase | SDD range | Proposed | Why |
| --- | --- | --- | --- |
| P2 CI and governance | 9.5–14.5 | 10.5–16 | Adds work P1 deferred or exposed: `scan.py`, its hook and gitleaks (OD-2); `requirements/*.txt` export (OD-3); approved-move label and base-ref plumbing into `validate.yml` (FR1.5); `OKF9xx` and its fixtures; macOS and Linux runs of everything P1 proved on Windows only (known gaps G1, G10); recorded API responses as fixtures (G9); 600-concept speed gate (G8) |
| P3 Site, release, skills | 5–7 | 5.5–7.5 | Python-Markdown divergence checks beyond nesting (G2), an RFC on scope notes (G6) and an anchor-placement rule (G3) |
| P4 Pilot and hardening | 5–8 | 5–8 | No new information |
| Total | 19.5–29.5 | 21–31.5 | |

Risk: P2 includes the GitHub App, the ruleset and the three-way approval inference, none of which P1 exercised; the V-05 carried items must be closed first.

### Draft `v0.1.0` tag message (owner tags on `main` after PR 7 merges; not tagged)

```
okf-library-template v0.1.0 (alpha)

Build phase P1: core profile tooling.

- okfprofile: reader, six checks, change rules, publishing pre-check, profile warnings,
  registry, generated indexes, revision-tier derivation (64 finding codes).
- Scripts: validate_profile, new_concept, renumber, build_indexes; poe tasks check, test, ci-validate.
- Example profile (Item, Vocabulary, Glossary) and example bundle; vendored okf-skills validator at a8b96420.
- Local pre-commit hooks. Gate: poe check and poe test on Python 3.11, 3.12, 3.14; 352 tests, 98.95 % coverage.

Not in this release: CI, platform adapters, revision writer, releases, site, skills (P2 to P3).
Verified on Windows only; see docs/development/testing/known-gaps.md.
```

Command for the owner: `git tag -a v0.1.0 -F <message-file> && git push origin v0.1.0`.
