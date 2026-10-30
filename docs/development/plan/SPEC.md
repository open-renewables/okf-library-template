# SPEC: build phase P1, core tooling

Status: **Approved by the owner on 2026-10-31:** the plan, the defaults for OD-1 to OD-10, and proposed entries PP-1 to PP-6 as drafted (ADR text is shown for review when each is written). Nothing is built. Drafted 2026-10-30 on branch `docs/p1-plan` (not committed). Effort is indicative, in person-days **[Inf]**.

## Requirement and sources

| Document | Role | Status |
| --- | --- | --- |
| [SRS](<../requirements/OKF Library Template - Software Requirements Spec.md>) | The requirement. Front matter `status: accepted` | Accepted |
| [SDD](<../architecture/OKF Library Template - Software Design Document.md>) §14 (P1 row), §7 C-03 and C-04, §8 I-01 to I-09, I-16, I-17, §9 W-04 | Defines the phase, the module, the scripts and the interfaces | Fixed for P1 |
| [DDR](<../adr/OKF Library Template - Design Decision Record.md>) | QA-33, QA-34, QA-41, QA-44, QA-45, QA-52 to QA-57, QA-62 to QA-65, QA-71 to QA-73 | Frozen series |
| [ADR-002](../adr/ADR-002-provider-neutral-skills.md), [ADR-005](../adr/ADR-005-relative-links-only.md), [ADR-006](../adr/ADR-006-mpl-licence-exceptions.md) | Provider-neutral repository; relative links only; MPL-2.0 exceptions | Accepted |
| P0 outcomes (SDD §15, V-01 to V-13) | Inputs listed under "P0 follow-ups" below | Applied 2026-10-30 |

**Abbreviations.** P1: build phase 1, "Core tooling" (SDD §14). FR/NFR: SRS requirements. AD-, QA-, DR-, ADR-: decision IDs, cited as written. I-nn, C-nn, W-nn, V-nn: SDD interface, component, workflow and verification items. OKFnnn: validation finding codes (I-09). PP-n: a proposed entry for the owner (`plan.md`).

P1 is one phase of the SRS, so the SRS is not set to `Done` when P1 ends.

## Goal

Build the profile tooling to the SDD, locally runnable and tested, so that SDD §14's P1 exit is met: **all finding codes tested; v0.1.0 (alpha).** The tooling holds no domain rule (FR2.1); the template's example profile and bundle exercise it.

## Scope

| Area | Delivered in P1 | SDD / SRS source |
| --- | --- | --- |
| Project set-up | `pyproject.toml` (groups `validate`, `dev`; poe tasks `install`, `check`, `test`, `ci-validate`; ruff, mypy, pytest, coverage settings), `uv.lock`, `.python-version`, `.gitattributes`, `.pre-commit-config.yaml` | AD-03, AD-04, AD-20, I-16, I-17; §6 |
| Module `scripts/okfprofile/` | `config`, `document`, `vocab`, `checks`, `changes`, `registry`, `indexes`, `codeowners`, `report`, and the pure part of `revision` (line grammar and tier derivation, no platform calls) | C-03; I-08 |
| Vendored validator | okf-skills at `a8b96420…` under `scripts/vendor/okf-skills/` with both licence texts; run by check 1 | AD-08; V-08 |
| Scripts | `validate_profile.py`, `new_concept.py`, `renumber.py`, `build_indexes.py` | C-04 |
| Profile | `profile/profile.yaml`, meta-schemas, `types/okf-base.schema.json`, type schemas, `formats/` for the example types | I-02 to I-05 |
| Validation | Checks 1 to 6, change rules (`OKF0xx`), publishing pre-check and the four warning kinds, as pure functions over supplied data | FR2.2, W-04 |
| Example bundle | One example concept per declared type, vocabularies, generated indexes, registry | C-01; FR1.1 |
| Tests and test docs | Fixtures per finding code, golden files, `testing/strategy.md`, `fixtures.md`, `known-gaps.md`; finding-code catalogue | constraints.md; `../testing/README.md` |

### Requirements covered

| Requirement | In P1 | Left for |
| --- | --- | --- |
| FR1.1 to FR1.5, FR1.7 | Bundle, `uid` format, registry, checks 1 and 6, move rule (the approved-move label is an input) | P2: label and base-branch plumbing in `validate.yml` |
| FR1.6 | `renumber.py` and its test | P2: push-to-`main` failure and issue (FR2.4) |
| FR2.1, FR2.2, FR2.3, FR2.5 to FR2.9 | All six checks, findings with code, level, file, line; base-tooling mode; mixed-change rule; unknown-field option; local run | — |
| FR2.4 | — | P2 |
| FR2.10 | Glossary anchor check (`OKF4xx`) | P3: site anchor view |
| FR2.11 | Tasks run locally; parity test with a CI-style invocation | P2: CI calls the tasks |
| FR3.4, FR3.7, FR3.9, FR3.10 | Revision-section check, tier derivation with golden files, status values, citation rule | — |
| FR3.1 to FR3.3, FR3.5, FR3.6, FR3.8, FR3.11 | Pure per-concept inference rules where they are platform-free (owner status by `codeowners`) | P2: revision writer, adapters, `verified` writing, stale report |
| FR4.1 to FR4.3 | Generator, tier on each line, freshness check | — |
| FR5.2, FR5.4 | Agent-label warning (inputs supplied), per-concept ownership | P2: PR template, issue forms |
| FR6, FR7, FR8 | — | P2, P3 |
| NFR2, NFR6 (local part) | No platform call in core modules; hash-locked set is P2 | P2 |

## Out of scope (P2 to P4)

- **P2:** `write_revision.py`; `okfprofile.platforms` (`github`, `git_local`); `stale_report.py`; `release.py`; `build_bundle.py`; `init_library.py`; `setup_repo.py`; `.github/` (workflows, CODEOWNERS file, issue forms, PR template, Dependabot); the GitHub App; `requirements/*.txt`; pip-audit, gitleaks, `scan.py` (default, see OD-2); instantiation self-test (W-10); licence-check automation; `tests/template/instantiation/`.
- **P3:** `mkdocs.yml`, `site.yml`, docs tasks; `AGENTS.md` library content, both skills (ADR-002), `GOVERNANCE.md`, `release.yml`.
- **P4:** pilot library, timing by a second person (FR6.1), agent run (FR7.2).
- Any change to a requirement or a decision. Anything that would change one is a proposed entry (`plan.md`, "Proposed entries"); nothing is written to `adr/`, the SDD, the SRS or `constraints.md` until the owner approves it.
- Provider-specific files: no `.claude/`, no product plugin manifest (ADR-002). The tooling and this plan assume no particular agent product.

## P0 follow-ups that land in P1

| Source | Follow-up | Where in `plan.md` |
| --- | --- | --- |
| V-08 | okf-skills emits strings without codes or line numbers and only two rules are errors. Map messages to `OKF1xx` by section marker and text prefix, tested against the pinned messages; or patch the vendored copy (default: map, patch not used; PP-4) | Step 4 |
| V-08 | Run the script without `--strict`, apply the profile's own levels; suppress the "recommended `generated` absent" and "cross-link not found" warnings (check 4 owns links); `%20` link false warning is not reported | Step 4 |
| V-08 | The script tolerates offset-less datetimes and accepts `ci:` actors: the datetime-offset rule stays in `okfprofile` (AD-08) | Step 4 |
| V-02 | Flag two-space nesting in sections whose format has children (I-04); four-space nesting only | Step 5 |
| V-01 | Compare anchor ids case-insensitively and require lower-case explicit ids; a duplicate explicit and automatic id is expected, not an error | Step 6 |
| V-13 | `.gitattributes` (`* text=auto eol=lf`) and `.python-version` (3.12) in the skeleton; CI and docs never call bare `poe` (exits 1) | Step 1 |
| ADR-005 | Validator rejects root-relative links; `new_concept.py` and the index generator emit relative links; the root-relative code path is not written | Steps 6, 7, 8 |
| ADR-006 | Licence check of the lock against the allowlist; the two MPL-2.0 exceptions cover site stacks, so a dev-group appearance of `pathspec` needs PP-3 | Step 1 |
| ADR-002 | No copy or symlink path for skills; nothing provider-specific is committed | Whole phase |

## Quality bar and conventions

- `../constraints.md` applies in full from the first commit that adds code: lock check, ruff rule set, `mypy --strict` on `scripts/okfprofile`, tests on Python 3.11 and 3.14, coverage at least 85 % with branch coverage, every finding code with a failing fixture, zero errors on `knowledge/` and `tests/library/fixtures/pass/`, no network in tests. It is not weakened. The vendored directory needs an exemption, which is PP-1.
- `../conventions.md` governs design (no domain rule in code, platform calls only in adapters, prefer the standard library, a new `validate` dependency needs an ADR), code (Google-style docstrings on the public API, stable finding codes, every script supports `--json`), module layout, tests, docs and git (squash merges, branch `<kind>/<slug>`, one change per pull request).
- `../testing/README.md`: P1 writes `strategy.md`, `fixtures.md` and `known-gaps.md`, and `plan-<feature>.md` only if a feature needs one. Behaviour that cannot be tested in P1 goes to `known-gaps.md`, not skipped.

## Done when

1. `uv run poe check` and `uv run poe test` pass on Python 3.11 and 3.14, with `constraints.md` unchanged except by an approved ADR.
2. Every finding code defined for the checks, change rules, publishing pre-check and warnings built in P1 has a failing fixture that raises exactly that code; the codes are listed in the catalogue.
3. The example bundle validates with zero errors, `build_indexes.py --check` reports no difference, and each declared type has a passing fixture.
4. Golden files cover every revision tier case in I-08 (including the `(self)` qualifier and the owner-approved one-line fix to an agent-drafted concept, which stays Machine-confirmed).
5. A relaxed profile plus a non-conforming concept fails under `--tooling-from` (FR2.5); a mixed tooling-and-content change fails without the migration input (FR2.6).
6. Local and CI-style runs on the same commit give the same findings (FR2.8, FR2.11).
7. `testing/strategy.md`, `fixtures.md` and `known-gaps.md` exist; the finding-code catalogue exists.
8. The owner has tagged `v0.1.0` (alpha); the re-estimate for P2 to P4 is updated from P1 actuals.

## Interpretations the owner should confirm

1. **"All finding codes tested" covers codes P1 implements.** `OKF9xx` (revision completeness) belongs with `write_revision.py --check-since` in P2 and is declared there; every other range is P1.
2. **The pure part of `revision` is P1.** FR4.2 needs the tier on each index line, and the tier comes from the revision lines in the body, so the line grammar and tier derivation (I-08) ship in P1. Reading pull requests or commits and writing lines is P2.
3. **The publishing pre-check is a pure function in P1.** It takes review data as input (W-04); fetching it from a platform is P2.
4. **Local verification is Windows only in P1.** There is no hosted CI until P2. Python 3.11 and 3.14 are run locally with `uv`; macOS and Linux are covered by the P2 matrix, and the gap is recorded in `known-gaps.md` (OD-9).
5. **Mixed-change rule for this phase.** The rule is not enforced until P2, so the plan keeps tooling and content in separate pull requests by discipline (OD-7).
6. **SDD I-07 example links.** The generated-index example uses root-relative links, which ADR-005 rejects. P1 emits relative links and lists the example as a proposed wording fix (PP-2). No decision changes.
7. **Scope notes.** I-07 says a folder line shows "scope from the folder's scope note", but the SDD defines no scope-note type or location. OD-1 asks for a decision; the default builds without one.

## Exit

All of SDD §14's P1 exit conditions, plus: the tooling files and tests above are merged by squash; the owner has tagged `v0.1.0`; proposed entries PP-1 to PP-6 are decided; the P2 to P4 estimate is revised from actuals; then, on the owner's instruction, the three plan files move to `plan/archive/2026-11-p1-core-tooling/` and the SRS status is left unchanged.
