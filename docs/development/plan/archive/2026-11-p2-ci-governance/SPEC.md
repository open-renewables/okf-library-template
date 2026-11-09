# SPEC: build phase P2, CI and governance

Status: **Approved by the owner on 2026-11-03:** the plan, the Q&A answers, the defaults for the remaining open decisions and proposed entries PP-1 to PP-9 as drafted (OD-12, the GitHub login, is still to be supplied at step 7). Nothing is built. Drafted 2026-11-03 on branch `claude/p2-plan-7e5114` (not committed). Effort is in agent hours and owner hours, not person-days **[Inf]** (`plan.md`).

## Requirement and sources

| Document | Role | Status |
| --- | --- | --- |
| [SRS](<../../../requirements/OKF Library Template - Software Requirements Spec.md>) | The requirement. Front matter `status: accepted` | Accepted |
| [SDD](<../../../architecture/OKF Library Template - Software Design Document.md>) §14 (P2 row), §7 C-03 to C-06 and C-09, §8 I-02, I-08 to I-11, I-15, I-16, §9 W-01 to W-07, W-10 to W-12, §10, §11 | Defines the phase, the adapters, the workflows and the security baseline | Fixed for P2 |
| [DDR](<../../../adr/OKF Library Template - Design Decision Record.md>) | QA-17, QA-32 to QA-34, QA-39, QA-43, QA-47, QA-52, QA-56 to QA-63, QA-65, QA-74 | Frozen series |
| [ADR-001 to ADR-008](../../../adr/README.md) | Notably ADR-002 (provider-neutral), ADR-004 (archive content hash), ADR-005 (relative links), ADR-006 and ADR-007 (licences), ADR-008 (vendored code) | Accepted |
| P0 outcomes (SDD §15) and P1 close-out ([archived plan](../2026-11-p1-core-tooling/todo.md)) | Inputs listed under "Carried into P2" below | Applied |

**Abbreviations.** P2: build phase 2, "CI and governance" (SDD §14). FR/NFR: SRS requirements. AD-, QA-, DR-, ADR-: decision IDs, cited as written. I-nn, C-nn, W-nn, V-nn: SDD interface, component, workflow and verification items. OKFnnn: finding codes (`../architecture/finding-codes.md`). G-n: known gap (`../testing/known-gaps.md`). PP-n: a proposed entry for the owner; OD-n: an open decision with a default (`plan.md`).

P2 is one phase of the SRS, so the SRS is not set to `Done` when P2 ends.

## Goal

Add the platform layer to the P1 tooling so that SDD §14's P2 exit is met: **each approval and tier case is recorded correctly in a scratch library, including a dropped run.** The template then runs its own CI on GitHub, instantiates itself in both modes, and a library can run on GitHub or on git and Python alone (FR6.5, FR6.6). Core modules still make no platform call; platform behaviour sits in adapters (AD-19).

## Scope

| Area | Delivered in P2 | SDD / SRS source |
| --- | --- | --- |
| V-05 closure | App "always" bypass on a protected `main` (5a); approval, stale approval and review `commit_id` API shape (5c); commit-to-pull-request lookup lag. Run in the sandbox; responses kept as test fixtures | §14 carried items; V-05 |
| Platform adapters | `okfprofile.platforms`: shared data model, `github` (REST over the standard library, no client library), `git_local` (commits and trailers) | C-03; AD-19; I-08 |
| Revision writer | `write_revision.py`: catch-up since the last bot commit, approval and currency inference, per-concept owner status, line insertion at the end of the section, affected indexes regenerated, optional `verified` writing, `--check-since`; `OKF9xx` codes | FR3.1 to FR3.8; W-05; AD-11, AD-12 |
| Stale report | `stale_report.py` and the weekly job's report content | FR3.11; W-06 |
| Intake and governance files | `.github/CODEOWNERS`, `pull_request_template.md`, `ISSUE_TEMPLATE/` (three forms and `config.yml`), `dependabot.yml`, label set | FR5.1, FR5.3, FR5.4; C-09; I-10, I-11, I-15 |
| Bundle and release | `build_bundle.py` (reproducible archive, checksum, manifest), `release.py` (gate, validation, build, annotated tag in `git-local`; check-only in `github`) | FR7.3, FR7.4; I-12; W-07; ADR-004 |
| Instantiation | `init_library.py` (questionnaire or answers file, licence files, template-only removal, platform choice), `setup_repo.py` (labels, merge methods, permissions, ruleset, `--dry-run`, `--check`, `--promote`) | FR6.1 to FR6.3; W-01, W-11 |
| Self-test | `tests/template/instantiation/` and the W-10 self-test for `github` and `git-local` | FR6.3, FR6.5; W-10 |
| Workflows | `validate.yml` (base-branch tooling, label and review plumbing, push-to-`main` report), `revision.yml`, `stale-report.yml`, `template-tests.yml`; the GitHub App; `validate` added to the `main` ruleset | FR2.4 to FR2.6; C-05, C-06; W-04, W-05; §10, §11 |
| Security jobs | gitleaks CLI at a pinned version, `scan.py` and its hook, pip-audit, licence check, hash-locked `requirements/*.txt` | NFR6; QA-56, QA-74; `../constraints.md` |
| Matrix | Linux, macOS and Windows on Python 3.11 and 3.14 for the template's own tests, pre-commit hooks included | FR2.11; QA-65; G1, G10 |
| Recovery and rehearsal | Runbooks for W-11, W-12, revision recovery and leak removal; W-12 rehearsal; set-up rerun | NFR7; FR6.6; `../AGENTS.md` |
| Tests and test docs | Recorded API responses, golden revision lines, `OKF9xx` fixtures, instantiation tests, speed gate; updates to `testing/` | `../testing/strategy.md` ("What P2 adds") |

### Requirements covered

| Requirement | In P2 | Left for |
| --- | --- | --- |
| FR1.5, FR1.6 | Approved-move label to the move rule in `validate.yml`; duplicate `uid` after concurrent merges reported on `main`, cleared by `renumber.py` | — |
| FR2.4 to FR2.6, FR2.8, FR2.11 | Required check, review rerun, push report as one tracking issue, base-branch tooling, mixed-change label, same tasks locally and in CI | — |
| FR3.1 to FR3.3, FR3.5 to FR3.8, FR3.11 | Writer, adapters, golden files for each approval case, catch-up, stale approval, `verified` mapping, stale report | — |
| FR3.4, FR4.3 on `main` | Hand edits to revision history and indexes caught by the push run | G4 stays partly open (see below) |
| FR5.1, FR5.3, FR5.4 | PR template with the four labels, issue forms, per-concept owner status from live data | Pilot contribution from issue form to concept: P4 |
| FR6.1 | A run sheet for the timing | P4: V-06 platform steps and full timing by a second person |
| FR6.2, FR6.3, FR6.5, FR6.6 | Licence files, template-only removal, self-test both modes, git-local release, W-12 rehearsal | — |
| FR7.3, FR7.4 | Archive, checksum, manifest, release gate | P3: `release.yml`, `use-bundle` in the archive, GitHub Release |
| NFR3, NFR6, NFR7 | Free tiers only; scans, pinned actions, least-privilege permissions, planted secret; set-up rerun and clean install | — |
| FR7.1, FR7.2, FR8.\* | — | P3, P4 |

## Out of scope (P3 and P4)

- **P3:** `mkdocs.yml`, `site.yml`, docs tasks; `release.yml`; `AGENTS.md` library content, `GOVERNANCE.md`, both skills (ADR-002); GitHub Release creation.
- **P4:** pilot library, full timing by a second person (FR6.1), traced agent run (FR7.2), pilot contribution through an issue form.
- Adapters for other hosting platforms (post-v1.0.0, AD-19); pre-filled per-page issue links (QA-37); `format_item_consistency`, `linked_set_drift`, `citation_index` (QA-45).
- Any change to a requirement or decision. Anything that would change one is a proposed entry (`plan.md`); nothing is written to `adr/`, the SDD, the SRS or `constraints.md` until the owner approves it.
- Provider-specific files: no `.claude/`, no product plugin manifest (ADR-002).

## Carried into P2

| Source | Item | Where in `plan.md` |
| --- | --- | --- |
| SDD §14, V-05 | 5a App "always" bypass; 5c approval, stale approval, review `commit_id`; closed **before `revision.yml` is written** | Step 1 |
| P1 OD-2, G7 | `scan.py`, its pre-commit hook, gitleaks, pip-audit | Steps 2, 3, 12 |
| P1 OD-3, G7 | `requirements/*.txt` hash-locked export; licence-check automation | Step 2 |
| P1 SPEC, FR1.5 | Approved-move label and base-ref plumbing into `validate.yml` | Step 12 |
| P1 SPEC interpretation 1, finding-codes | `OKF9xx` declared with `write_revision.py --check-since`, with fixtures | Step 5 |
| G1, G10 | macOS and Linux runs of everything P1 proved on Windows; hooks on those systems | Step 12 |
| G4 | Hand-edit limits: push-to-`main` run and writer; stronger rule only on request | Steps 5, 12 |
| G8 | 600-concept speed gate | Step 12 |
| G9 | Recorded API responses; golden lines for each case, dropped run, catch-up | Steps 1, 4, 5 |
| `../constraints.md` | "Pinned tool versions: to fill at the start of P2" (gitleaks, lychee) | Step 2 (PP-2) |
| `../AGENTS.md` | Runbooks for W-11, W-12 and recovery | Steps 10, 14, 15 |
| V-12 | Archive digest across systems | Steps 8 and 12 |
| V-06 | Carried to P4 by the owner (2026-11-03); run sheet only | Step 15 |

Gaps G2, G3, G5 and G6 are not P2 work and stay open.

## Quality bar and conventions

- `../constraints.md` applies in full and is not weakened. P2 adds enforcement of its Security rows and the speed row; the **To fill** row is a proposed entry (PP-2). A limit that a P2 job cannot meet is a proposed entry, not a relaxed limit.
- `../conventions.md` governs: platform calls only in adapters, standard library preferred (so no GitHub client library and no new `validate` dependency without an ADR), Google-style docstrings, stable finding codes, every script supports `--json`, one change per pull request, tooling and content in separate pull requests, branch `<kind>/<slug>`.
- `../testing/`: P2 follows "What P2 adds" in `strategy.md`; platform API responses are recorded fixtures with no network in tests; a behaviour that cannot be tested goes to `known-gaps.md`.
- Workflows follow SDD §10: actions pinned by full SHA, read-only default token, per-job permissions, no `pull_request_target`, jobs call only `uv run poe <task>` (AD-20).

## Done when

1. `uv run poe check` and `uv run poe test` pass locally on Python 3.11 and 3.14 and in CI on Linux, macOS and Windows, with `constraints.md` changed only by an approved entry.
2. V-05 5a and 5c are closed with recorded responses, or their contradictions are proposed entries; `revision.yml` was written after that.
3. Every `OKF9xx` code in the catalogue has a failing fixture; the catalogue test passes.
4. Golden files cover every approval row of I-08 (`approved` current and stale, owner and non-owner, `self-approved`, `merged without approval`, `PR none`), catch-up after a dropped run, the `verified` mapping, and the `git-local` trailers.
5. In a scratch GitHub library in the sandbox, live `revision.yml` records each approval case that one owner plus the App can produce (the owner-approved and merged-without-approval cases rest on recorded fixtures, OD-2), including a dropped run recovered by the next run and a duplicate `uid` after concurrent merges (FR1.6); a `git-local` scratch library records the same from local commits (SDD exit).
6. The W-10 self-test passes for `github` and `git-local` on every template pull request; a planted secret is caught by the CI scan and by the local hook (NFR6); a marker is caught by `scan.py`.
7. A `git-local` release rebuilt from its tag reproduces the recorded SHA-256 (tar digest, ADR-004) and the tar digest is equal on all three systems (V-12); the W-12 rehearsal leaves commit identifiers and revision lines unchanged and every earlier archive matching its checksum (FR6.6).
8. `validate` is a required check on the `main` ruleset of `open-renewables/okf-library-template`; a deliberate mixed pull request fails it and a failing commit on `main` opens one tracking issue (rehearsed in the sandbox) (FR2.4, FR2.6).
9. `setup_repo.py` rerun on a scratch repository restores its settings (NFR7); a clean install from the lock file and from `requirements/validate.txt` passes the suite.
10. Runbooks exist for W-11, W-12, revision recovery and leak removal; `testing/` documents are updated (G1, G7 to G10 closed or narrowed, new gaps listed); the V-06 carry to P4 is recorded.
11. The owner has tagged `v0.2.0` (alpha, OD-9); proposed entries are decided; the re-estimate for P3 and P4 is proposed from P2 actuals.

## Interpretations the owner should confirm

1. **`build_bundle.py` is P2.** SDD §14 names `release.py` and reproducible archives in P2 and `build_bundle` in the P3 row with `release.yml`, but `release.py` calls it and the archive must be reproducible in P2 (OD-4, PP-5). The P2 archive has no `use-bundle` skill; the builder includes it once P3 adds it.
2. **`release.yml` and GitHub Releases are P3.** P2 delivers the `git-local` release and the release gate as a command; in `github` mode `release.py` checks only (SDD C-04).
3. **The operating-system matrix lives in `template-tests.yml`.** A library's `validate.yml` runs Linux only on Python 3.11 and 3.14, because hosted macOS and Windows minutes are multiplied on private repositories **[Inf; check against current Actions billing before step 12]** and NFR3 requires free tiers (OD-3, PP-8).
4. **Mixed-change rule bites from step 13.** Until `validate` is a required check, P2 pull requests keep tooling and content apart by discipline. P2 touches only tooling paths and `docs/`, plus revision lines the bot writes after the App exists.
5. **`scan.py` is not a validation finding.** It has its own output and exit code and no `OKF` code; its patterns are configuration (OD-5, PP-4).
6. **Rehearsals are not spikes.** V-05 runs in `open-renewables-sandbox/p0-spikes`. Scratch libraries and the W-12 rehearsal use separate synthetic repositories in `open-renewables-sandbox` (OD-11). Nothing synthetic goes into `open-renewables`; the real workflows run there only by merged pull request.
7. **The template's own `revision.yml` run.** On the template repository `revision.yml` records lines only for concepts a pull request changed; with no `knowledge/` change a run is a no-op.

## Exit

All of SDD §14's P2 exit conditions plus "Done when" 1 to 11: pull requests merged by squash, tag `v0.2.0` pushed by the owner, proposed entries decided, then, on the owner's instruction, the three plan files move to `plan/archive/2026-11-p2-ci-governance/` and the SRS status is left unchanged.
