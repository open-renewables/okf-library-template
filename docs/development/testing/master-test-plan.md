# Master Test Plan

Status: **Draft for owner review (2026-11-07).** Template-only: nothing here ships to libraries and `tests/library/` and SDD §6 are unchanged. The plan is run at build phase P4 against scratch libraries and the pilot library, after the template build is complete. After P4 it may optionally be run again during beta testing against real libraries built from the template, using the read-only subset only (section 6).

Provider-neutral (ADR-002): cases are commands and expected results that a person or any agent can run. Terms: AT = acceptance test (an `AT-<requirement>-nn` case); LUT = library under test; the abbreviations of the SRS and SDD apply.

## 1. Objective

Use the finished template to test all of its functionality, end to end, in a library built from it. [strategy.md](strategy.md) proves the tooling with unit tests, fixtures and golden files in the template repository; this plan is the **acceptance level above that**: does a library instantiated from the template meet every SRS criterion, on every supported system and platform mode, as a user would run it. It also gathers the P3 and P4 checks that `strategy.md` already assigns to those phases (site compatibility, second-person timing, traced agent run) in one place.

Two kinds of target, with different rights:

| Target | Rights | Where |
| --- | --- | --- |
| **Scratch library** (synthetic) | Destructive, negative and live-platform tests | Local `git-local` repository; GitHub repository in `open-renewables-sandbox`, never in `open-renewables` |
| **Real library** (the pilot, later others) | Read-only, non-destructive subset: cases marked `RO`, run on a temporary copy where they write | Its own repository; no live-platform changes |

## 2. Scope

In scope: SRS FR1 to FR8 and NFR1 to NFR7 (59 requirements), the SDD §12 speed targets, the SDD §13 and §15 verification items, the P2 "Done when" items, and the known gaps G1 to G13, each traced in [traceability-matrix.md](traceability-matrix.md) to cases in [acceptance-test-cases.md](acceptance-test-cases.md).

Out of scope:

- Unit, fixture and golden-file tests (strategy.md; they run in `uv run poe test`).
- Library domain content and domain rules (each library's own concern).
- Adapters for hosting platforms other than GitHub (post-v1.0.0, AD-19).
- The automation harness and scratch-library generator: described in section 8, built after P2 PR 6.
- Anything in `open-renewables` beyond read-only checks on the template repository's own settings.

## 3. Levels and where this plan sits

| Level | Document | Run |
| --- | --- | --- |
| Unit, fixture, golden, parity, catalogue | [strategy.md](strategy.md), [fixtures.md](fixtures.md) | Every change: `uv run poe check`, `uv run poe test` |
| Template CI | `template-tests.yml` (P2 PR 6) | Every template PR: matrix, self-test (W-10), scans |
| **Acceptance** | **This plan** | **P4; optionally after P4 during beta testing against real libraries (read-only subset); before each template release after v1.0.0** |
| P2 rehearsals | `../plan/archive/2026-11-p2-ci-governance/plan.md` steps 1, 12, 14, 15 | During P2, in the sandbox |

The acceptance level does not re-implement lower levels. Where a requirement already has a fixture or golden file, the case runs that test selection (`[T]` steps) and adds the end-to-end check on a library. Where a P2 rehearsal defines a scenario (S1, S2, step 15), the case adopts it by link and adds only the expected result and evidence.

## 4. Environments

| Environment | Purpose | Notes |
| --- | --- | --- |
| E-LOCAL: scratch library, `platform: git-local` | Scripted and destructive cases without a platform | Built by the generator (section 8); network can be blocked |
| E-GH: scratch library, `platform: github`, repository in `open-renewables-sandbox` | Live platform cases | Sandbox App and token; free-tier limits (NFR3); deleted or archived after the run |
| E-REAL: pilot or another real library | `RO` subset | `destructive_allowed: false` in the parameter file; the harness refuses `D` cases |
| Systems | Windows 11, macOS, Linux | CI matrix gives the evidence for FR2.11 and V-13; human cases are run on the owner's machine (Windows) unless OD-AT5 says otherwise |
| Python | 3.11 and 3.14 | Own `UV_PROJECT_ENVIRONMENT` per version on Windows (strategy.md) |

## 5. Test data

| Data | Source |
| --- | --- |
| Seeded scratch library | Generator output: `init_library` answers file (both platforms), one concept per declared type, the template's example vocabulary, a base commit; seeded from `profile.yaml`, so types, prefixes and namespaces are never hard-coded |
| 600-concept bundle | Generated as in [performance.md](performance.md), Method, but without calling `create_concept` 600 times (the generator writes files and registry entries directly) |
| Known-good and known-bad sets | `tests/library/fixtures/pass/` and `fail/<code>/` ([fixtures.md](fixtures.md)); cases copy a fixture into a scratch library rather than restating it |
| Approval-case history | Sandbox PRs made by the owner and the App (plan step 15); recorded API responses under `tests/template/fixtures/` for the cases one owner cannot produce (plan OD-2) |
| Second account | Open (OD-AT1) |
| Planted secrets and markers | Built at run time from the patterns in `profile/scan.yaml`; never a real secret and never committed |

## 6. Run phases

| Phase | What | Where | When |
| --- | --- | --- | --- |
| 1 Smoke | `ready` cases marked `RO` plus `uv run poe check` and `test` | E-LOCAL, then E-REAL | Start of any run; stop on a failure |
| 2 Full local | All scripted and review cases | E-LOCAL on each system and Python version | After smoke |
| 3 Live platform | All `live` cases | E-GH | After full local; owner or delegate present (OD-AT1) |
| 4 Release and rehearsal | FR7.3 to FR7.4, FR6.4 upgrade, FR6.6 W-12, V-12 cross-system digests | E-LOCAL, E-GH | After phase 3 |
| 5 Human and agent | FR6.1 timing, FR5.3 pilot contribution, FR7.1 to FR7.2 agent runs, FR2.10 and FR8.4 platform checks | Pilot library | Last: needs the pilot and a second person |

A real library gets phase 1 and the `RO` agent runs of phase 5 only. This also applies to optional beta-testing runs after P4: each real library is run with `kind: real` and `destructive_allowed: false` in its parameter file, and results go in its own run folder.

## 7. Entry and exit criteria

Entry for a full run: the template build is complete (P3 merged, v0.5.0 tagged); `uv run poe check` and `uv run poe test` pass on the tag; every case's `pending` status is cleared or the case is recorded `blocked`; the parameter file is filled in and reviewed; sandbox repositories exist (E-GH) and the sandbox token is in the named environment variable.

Exit, tied to the SDD §14 v1.0.0 gate:

| Criterion | Evidence |
| --- | --- |
| CI passes on the release candidate (matrix, self-test, scans) | AT-FR2.11-01, AT-FR6.3-03, AT-NFR6-02 |
| A second person instantiates a library in under 30 minutes (FR6.1) | AT-FR6.1-01 |
| An agent run produces outputs traceable to `uid`s and a release tag (FR7.2) | AT-FR7.2-01 |
| FR1 to FR8 verified as in SDD §13 | The matrix: every criterion has at least one case with result `pass`, or `partial` where OD-AT1 says so, with the owner's acceptance of each `partial` |
| V-01 to V-13 closed | Matrix section "SDD §13 and §15 verification items" |
| No open error-level defect | Section 9 |

The owner decides whether the exit criteria are met. A `blocked` or `skipped` case is not a pass.

## 8. Harness and generator (described, not built)

A later step, after P2 PR 6, builds them under `tests/template/acceptance/` and a poe task. They must:

- Read the parameter file and `profile.yaml`; select cases by `kind`, `mode`, system and phase; refuse `D` cases when `destructive_allowed` is false.
- Generate a seeded scratch library for each platform mode from an answers file, and the 600-concept bundle, deterministically (fixed seed, fixed commit dates).
- Create sandbox repositories only in `open-renewables-sandbox` (explicit repository on every `gh` call) and clean them up; never touch `open-renewables`.
- Run each scripted case's commands, compare exit codes and finding codes (not message text), write `logs/<ID>.txt` and a results row, and fill the run sheet. Human and live cases print their steps and collect the result.
- Run offline when `network: blocked` and fail on any attempted connection.
- Use no provider-specific file (ADR-002).

Until it exists, a person or an agent runs the cases by hand from the case file.

## 9. Evidence and defects

**Evidence.** One folder per run: `testing/runs/YYYY-MM-DD-<library>/` holding the filled `library-under-test.yaml`, `run-sheet.md`, `results-report.md`, and `logs/` and `findings/` when `commit_logs` is true. By default the folder keeps the sheet, report and findings summaries; raw logs stay outside the repository and the report records where (OD-AT3). A scratch library is deleted or archived after the run; its repository name is recorded.

**Defects.** A failure becomes a defect with a severity:

| Severity | Meaning | Treatment |
| --- | --- | --- |
| S1 | Wrong result that weakens a control (validation bypass, wrong approval or tier recorded, data loss) | Fix before v1.0.0 |
| S2 | A requirement criterion fails | Fix before v1.0.0, or the owner records a deviation |
| S3 | Behaviour differs from the SDD without failing a criterion | Fix, or list as a known gap |
| S4 | Wording, cosmetic | Backlog |

"No open error-level defect" for v1.0.0 means no open S1 or S2. A defect that is deferred, or a behaviour that cannot be tested, is added to [known-gaps.md](known-gaps.md), the single list of gaps; the results report cites the gap id. A fix follows the normal flow (tooling PR, `poe check`, `poe test`); the failed case is rerun and its result updated.

## 10. Roles

| Role | Does |
| --- | --- |
| Owner (maintainer) | Approves this plan and the parameter file; creates sandbox repositories, the App and secrets; runs or delegates live cases; decides on `partial`, deviations and the exit criteria |
| Agent runner | Runs scripted and review cases, fills run sheets and reports, proposes defects; does not commit, push or merge without the owner's instruction |
| Second person | Times FR6.1 from the run sheet without help; a person, not necessarily a second GitHub account |
| Reviewer | Judges `review` and `human` cases (traceability, content style); not the author of the case under judgement where there is a choice |

## 11. Open decisions

| ID | Question | Default stated (not decided) |
| --- | --- | --- |
| OD-AT1 | Who runs the live (platform) tests, and does a second GitHub account exist? | The owner runs phase 3 in the sandbox; the agent runs phases 1, 2 and 4 and prepares phase 3. No second account: cases needing one (FR2.6-02, FR3.5-01) run on their stated fallback (sandbox App-submitted reviews, recorded fixtures) and the result is `partial`. The second person for FR6.1 is someone other than the owner who has not built the template |
| OD-AT2 | Where does the harness live and when is it built? | `tests/template/acceptance/` with a poe task, after P2 PR 6 (template-only, so removed with `tests/template/`) |
| OD-AT3 | Are raw logs committed? | No: committed sheet, report and findings summaries only; raw logs recorded by location |
| OD-AT4 | Which real library gets the read-only subset? | The pilot library, after phase 5 |
| OD-AT5 | Are macOS and Linux human runs needed, or is CI matrix evidence enough? | CI matrix evidence is enough for FR2.11 and V-13; human cases run on one system |

## 12. Proposed entries

Nothing below is written until the owner approves its text. Documents named are not edited by this plan.

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| PE-AT-1 | A new ID scheme, `AT-<requirement>-nn` | Abbreviation lists: add "AT: acceptance test case" to the vault abbreviations note (owner only; this session cannot edit it) and, if wanted, to `../conventions.md` | Owner edit; a DDR change-log row |
| PE-AT-2 | SDD §13 and §14 do not mention this plan | SDD §13 verification column ("see the acceptance matrix") and the P4 row ("run the Master Test Plan") | SDD edit with a DDR change-log row |
| PE-AT-3 | SRS criteria that cannot be tested as written: FR3.4 (authorship), FR3.8 (no OKF tool derives a tier), FR6.4, FR8.5 and NFR5 (no criterion), FR6.1 ("a second person" undefined for a solo owner) | SRS wording; the owner owns requirements | Owner decision; suggested rewording: FR3.4 "a hand edit that breaks the line grammar or removes a line fails; authorship is not tested"; FR3.8 "a reader implementing the V-11 rule derives the same tier" |
| PE-AT-4 | New gaps found while planning (see section 13) | `known-gaps.md` rows G14 and G15 | Add when P4 confirms them; this PR leaves the list unchanged |
| PE-AT-5 | AT-FR2.5-03: on `pull_request`, GitHub runs the workflow file from the PR head, so a PR could edit `validate.yml` itself. If the case shows the required check passing, the design needs a control | SDD AD-18 or C-05, or a new ADR (for example CODEOWNERS plus required review on `.github/`, or running the check from a `workflow_run` on the base) | ADR |

## 13. Review of overlaps with existing documents

| Overlap found | Resolution |
| --- | --- |
| The P2 rehearsals (plan steps 1, 12, 14, 15; S1, S2) already define scratch-library, dropped-run, duplicate-uid and W-12 scenarios | Cases adopt them by link (AT-FR1.6-01, AT-FR3.1-02, AT-FR3.2-02, AT-FR6.6-01); this plan adds expected results, evidence and the P4 re-run, not new scenarios |
| `strategy.md` "What P2 adds" lists the instantiation test, recorded responses and speed gate; its P3 and P4 note lists site checks, timing and the agent run | Those stay in `strategy.md` as lower-level tests; the acceptance cases run them (`[T]` steps) and take the P3 and P4 items as cases. A cross-link is added there |
| `known-gaps.md` G1 to G13 name what closes each gap | The matrix maps each gap to the case that closes or narrows it; known-gaps stays the single list; no row is copied |
| `fixtures.md` catalogues what each fixture proves | Cases cite fixture folders and finding codes; none restates a fixture |
| `performance.md` records the 600-concept timing and says the gate is P2 | AT-SDD12-01 re-times it as a gate and reuses its method; the file is unchanged |
| P2 "Done when" 1 to 11 overlap with the acceptance exit | The matrix maps items 1 to 9 to cases; 10 and 11 are process steps, not tests |
| Two candidate gaps not yet in known-gaps: an acceptance run cannot show the owner-approved and merged-without-approval cases live without a second account (partly plan OD-2 and the P2 risk table); a workflow edited by its own PR (PE-AT-5) | Left for the owner as PE-AT-4 and PE-AT-5 |
