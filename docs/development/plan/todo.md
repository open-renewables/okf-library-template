# Todo: build phase P4

Checklist for `plan.md`; scope and done-when in `SPEC.md`. Tick an item when its check in `plan.md` has passed and the evidence (command and result, or run URL) is noted in the Outcomes table. **NEEDS YOU** marks a decision, person, account, machine or setting from the owner. Nothing is committed, pushed, merged or tagged without the owner's instruction. When a pull request or session closes, note its agent time and owner time in the Outcomes table (plan, rule 9).

## Before any step

- [x] Owner reviews `SPEC.md`, `plan.md` and `todo.md` (approved 2026-11-19)
- [x] **NEEDS YOU (decision):** owner answers OD-1 to OD-24 or accepts the defaults (OD-9, OD-22 to OD-24 answered 2026-11-17; the rest on their defaults with the approval of 2026-11-19); OD-2 (pilot location and visibility), OD-4 (primary type), OD-9 (library-build test; second person optional), OD-13 (default generator) and OD-15 (immutability) are the ones that change work
- [ ] **NEEDS YOU (decision):** owner approves or rejects PP-1 to PP-14 as they apply (PP-5, PP-7, PP-11, PP-12, PP-13 only if they fire)
- [x] **NEEDS YOU (decision):** owner confirms the amended estimate with PR V (RFC-002; approved with the amendment, 2026-11-19): agent about 59–87 h, owner about 16–23 h, 11–16 days; RFC-002's own figure, on the SDD §14 baseline, is about 39–55 agent hours
- [x] **NEEDS YOU (decision):** owner confirms the effort units and the bottom-up figures (scope kept, 2026-11-19; the SDD row changes only through PP-9) in `plan.md` "Effort" (agent about 46–69 h, owner about 14–20 h, 9–13 days with user-documentation option B morphed into each library's guide against the SDD row 26–37, 9–10, 6–9), or chooses the trim
- [ ] **NEEDS YOU (decision):** owner shares the real-life scenario mapping for step 8a (path or document) and where its library will live (OD-9); a second person is optional

## PR D: Dependabot #24 to #28

- [x] 1. Each pull request's diff read: they change only `requirements/*.txt`, not `uv.lock`, and no CI ran on them, so OD-12's replacement applies (G41)
- [x] **NEEDS YOU (person):** `@dependabot rebase` on each, or approve the `tooling/p4-deps` replacement (OD-12); merge; close superseded ones (replacement #48 merged 2026-11-19; #24 to #28 closed)
- [x] 1. Check: `poe licences` and `poe audit` zero findings; `poe export --check` passes; `validate` export unchanged; CI green on three systems; none of #24 to #28 left open
- [x] PR D closed: agent about 1 h, owner about 0.25 h (merged as #48)

## PR 1: folder-scope header (`tooling/p4-index-header`)

- [x] **NEEDS YOU (decision):** FR4.3 wording (yours) and the SDD I-07 text shown for PP-1 (approved 2026-11-19 with ADR-012)
- [x] 2. `indexes.py` keeps a `description` header, writes it on the parent folder line; check 5 compares the body only; header findings coded (`OKF505`, `OKF506`; `OKF121` in check 1, ADR-012); fixtures; `author-concept` and `AGENTS.md` lines. Template folders carry **no** header (a header gives every library an `OKF121` warning), so golden files are unchanged
- [x] 2. Check: fixtures and goldens pass; body edit under a valid header fails `OKF502`, header edit does not; `poe check` clean; `check-skills` passes; coverage 98.13 %. Not tested: a header kept across instantiation (the code reads headers from the tree)
- [x] PP-1 applied (SRS FR4.3, owner's wording approved 2026-11-19; SDD I-07; DDR row)
- [ ] PR 1 closed: agent __ h, owner __ h

## PR 2: authoring aids (`tooling/p4-authoring`)

- [x] 3. `new_concept.py --set key=value`; "Rename the primary type" procedure in `runbook-instantiate-library.md` with a scripted test (plus `rename_type.py`, owner-approved in PP-8)
- [x] 3. Check: `--set` tests (declared, undeclared refused, list, Vocabulary with `namespace` validates); rename test passes on a copy, template unchanged; `poe check`, `poe test`
- [x] PP-8 approved and applied (SDD C-04, W-01 step 3) (approved 2026-11-19; SDD §6, C-04, W-01 step 3; DDR row)
- [x] PR 2 closed: agent about 6 h including the review fixes, owner about 0.5 h (merged as #50)

## PR 3: test readiness (`docs/p4-test-readiness`)

- [x] 4. AT statuses refreshed (no `pending P2` or `pending P3`); MTP §11 decisions written (OD-10, OD-11); parameter files for `scratch-local`, `scratch-github`, `pilot`; `runs/README.md` with run-sheet and report skeletons; traceability matrix refreshed (ADR-010, ADR-011, P3 cases)
- [x] 4. Check: grep for `pending P2|pending P3` empty; matrix and case file agree both ways; no secret in parameter files; MTP §7 entry criteria listed with state below
- [x] PR 3 closed: agent about 2 h, owner about 0.25 h (merged as #51)

## PR U: user documentation (`tooling/p4-user-guide`)

- [x] **NEEDS YOU (decision):** option A, B or C (OD-22) and location (OD-23) (decided 2026-11-17: option B in `docs/guide/`)
- [x] OD-24 decided 2026-11-17: morph, copy or remove is the user's choice during `init_library` (answers key `guide: morph | copy | remove`)
- [ ] **NEEDS YOU (decision):** PP-14 approved when its text is shown
- [ ] 4a. Guide written (option B: getting started, maintaining, customising the profile, reference); five runbooks and `finding-codes.md` moved with `git mv`, links re-pointed; `init_library` keeps the guide and removes only `docs/development/`; generated README and `AGENTS.md` link to it; drafted as a library guide with `template-only` and platform markers and placeholders; `init_library` asks morph, copy or remove (`guide: morph | copy | remove`), morphs it and adds the conventions stub on `morph`, removes it and its links on `remove`, records the choice in DR-01
- [ ] 4a. Check: guide present in both instantiated trees; every link resolves, none into `docs/development/`; every command exists; `morph`: no template-only or wrong-platform block, unresolved placeholder or stray "the template" wording left, conventions stub present; `copy`: guide equals the template's apart from the markers; `remove`: no `docs/` left, no link to the guide, warning printed; `poe check`, `poe test`, `poe selftest` pass
- [ ] **NEEDS YOU (person):** close reading of the guide
- [ ] PP-14 applied (SDD §6; DDR row)
- [ ] PR U closed: agent __ h, owner __ h

## PR V: OKF v0.3 (`tooling/p4-okf-v03`, RFC-002)

- [x] **NEEDS YOU (decision):** D1 to D7 (decided 2026-11-19, RFC-002 "Decision"; OD-26)
- [x] **NEEDS YOU (decision):** owner reviews this plan amendment before step 4b starts (approved 2026-11-19)
- [x] **NEEDS YOU (decision):** ADR-013 and the PP-15 SDD text approved when shown (approved 2026-11-20, with the `constraints.md` row and the v0.3 citation convention); one pull request with the `profile-migration` label (OD-25 default)
- [ ] **NEEDS YOU (decision):** PP-16 SRS wording (yours)
- [x] 4b.1 OKF project validator vendored at `527e81a` with its licence; check 1 mapped by code; `I203`, `W115` and check-2-owned `W120` dropped; `OKF120` kept; `test_conformance.py` rebuilt with a code-coverage test
- [x] 4b.2 `profile.yaml` pin (`okf_version: "0.3"`, `okf_spec_commit: 527e81a`); `okf-base.schema.json` (`superseded_by`; `parameters` require `name` and `type`)
- [x] 4b.3 Root header keeps every key; `OKF506` allows `title`, `license`, extension keys on the root; `OKF121` from `E004`, root no longer counted; `init_library` writes `title` and `license`; W-10 assertion
- [x] 4b.4 Check 4 path fields by v0.3 §6.2 (own folder; leading `/` the bundle root), with fixtures (`OKF412`)
- [x] 4b.5 I-08: written `verified[].at` never earlier than `generated.at`; golden case
- [x] 4b.6 ADR-013; SDD (PP-15) and DDR row; `AGENTS.md`, `README.md`, both skills, `VENDORED.md`, licence and `NOTICE`, finding-code catalogue, `constraints.md` pins, G42 (SDD edits applied with PP-15, awaiting approval)
- [ ] 4b. Check: vendored hash tested; every emitted code in the table; `OKF1xx`, `E004`, root-metadata, §6.2 and I-08 fixtures pass; self-test finds `title` and `license`; template bundle has no finding; `poe check` and `poe test` on 3.11 and 3.14 and CI on three systems; no current "v0.2" in `AGENTS.md`, `README.md` or the skills
- [x] PP-15 applied (2026-11-20); PP-16 still with the owner
- [ ] PR V closed: agent __ h, owner __ h

## RC: `v0.9.0`

- [ ] 5. Tag message drafted (below)
- [ ] **NEEDS YOU (person):** push annotated tag `v0.9.0` on `main`
- [ ] 5. Check: `release.yml` four jobs green; archive verified (`sha256sum -c`, tar digest, `RELEASE`); next `stale-report.yml` reports no gap

## Pilot: instantiation and authoring (pilot repository)

- [ ] **NEEDS YOU (decision):** pilot name and visibility (OD-2), primary type and sections (OD-4), licences if not the defaults
- [ ] 6. Pilot created `git-local` from the `v0.9.0` archive; primary type renamed by the procedure; vocabularies and glossary ready; `DECISIONS.md` entries; each step timed
- [ ] 6. Check: `poe check` and `poe test` pass; no `Item` or `ITM` left; DR-01 and the rename entry present; rename time recorded (G23)
- [ ] **NEEDS YOU (person):** sources supplied or approved; each concept reviewed; `stable` ones chosen
- [ ] 7. About 20 concepts with `author-concept`; scope headers per folder; vocabulary values and glossary entries; trailers and `poe revision` per change; `v0.1.0` and `v0.2.0` local releases; D1 and D2 occurrences counted
- [ ] 7. Check: `poe check` clean; all four tiers in the indexes; both releases rebuild to their digests; `author-concept` used without edits (AT-FR7.1-02) or each edit a defect; site strict with both generators
- [ ] **NEEDS YOU (decision):** OD-7 (warning kind) from the D1 and D2 count; PP-7 if built

## Library-build test (V-06, FR6.1)

- [ ] 8a. Scenario mapped by the agent: each need tied to a W-01 step, a profile setting or a known gap, before the run
- [ ] **NEEDS YOU (person):** owner builds the scenario's library from `v0.9.0` and the run sheet, timing each step to the first merged validated concept
- [ ] 8a. Findings classified (defect with severity, runbook correction, known gap, PP-12); owner's row in the runbook timing table; corrections merged
- [ ] Optional 8b. **NEEDS YOU (person, account):** a second person with a sandbox account runs `github` (private scratch repository, no App) and `git-local` without help; times and stopping points recorded
- [ ] 8. Check: 8a at most 30 minutes with every step timed; FR6.1 `pass` if 8b ran within 30 minutes, otherwise `partial` accepted by the owner with PP-4 and PP-13 decided; scratch repositories archived

## Pilot on the platform

- [ ] **NEEDS YOU (account, setting):** pilot repository created, sandbox App installed; a second account added as collaborator and code owner of one folder only if one exists
- [ ] 9a. W-12 with both tags; archives uploaded only on matching digests; a wrong digest refused on a scratch copy (G32)
- [ ] 9b. W-11 (if public): promoted, App token used by the next revision run (G32)
- [ ] 9c. Only with a second account: it approves a change in its folder and merges one owner pull request without approval; lines match I-08 (G35, AT-FR3.5-01). Otherwise AT-FR3.5-01 `partial`, G35 open
- [ ] 9d. Issue form submitted without git (by the owner in the browser by default) and turned into a merged concept (FR5.3, AT-FR5.3-01)
- [ ] 9e. Glossary anchors on github.com: plain, non-ASCII, parenthesised (G3, V-01, AT-FR2.10-02); PP-11 if one fails
- [ ] 9f. Six FR8.2 checks on the pilot bundle with both generators (ADR-001 criterion)
- [ ] 9g. Pilot `v0.3.0` released through `release.yml` (OD-19)
- [ ] 9. Check: each sub-step recorded with its run URL; G32, G35, G3 closed or narrowed

## Traced agent run (FR7.2)

- [ ] **NEEDS YOU (person):** eight questions chosen; reviewer named
- [ ] 10. Fresh agent with the pilot `v0.3.0` archive only; citations traced; draft concept reported as unverified (AT-FR7.2-01, -02); optional second runtime (OD-16)
- [ ] 10. Check: 100 % of citations trace; no unreviewed content called reviewed; out-of-bundle question answered "not covered"; misses fixed and rerun

## PR 4: Master Test Plan run (`docs/p4-mtp-run`, fix branches)

- [ ] MTP §7 entry criteria met (template build complete, `v0.9.0` tagged, statuses cleared, parameter files reviewed, sandbox repositories exist, token in its environment variable)
- [ ] 11. Phase 1 smoke on all three targets
- [ ] 11. Phase 2 full local (E-LOCAL, Windows; macOS and Linux from CI)
- [ ] **NEEDS YOU (person):** run phase 3 live cases with the agent preparing each (OD-10)
- [ ] 11. Phase 3 live on E-GH, including AT-FR2.5-03 early (OD-17; PP-5 if it passes the required check)
- [ ] 11. Phase 4 release and rehearsals (FR7.3, FR7.4, V-12, FR6.4 merge of `v0.9.0` into a clone made at `v0.5.0`)
- [ ] 11. Phase 5 linked to steps 8 to 10
- [ ] 11. Defects logged with severity; S1 and S2 fixed in `tooling/p4-fix-<slug>` and rerun; S3 and S4 fixed or in `known-gaps.md`
- [ ] **NEEDS YOU (decision):** accept or reject each `partial`; record any S2 deviation
- [ ] 11. Check: every FR and NFR criterion has a result; no open S1 or S2; matrix carries results; new gaps listed (PE-AT-4)
- [ ] PR 4 and fix pull requests closed: agent __ h, owner __ h

## PR 5: verification closure (`docs/p4-verification`)

- [ ] 12. V-01 to V-13 each closed with evidence (V-07 parts not applicable, OD-14); SDD §13 rows marked with case IDs; `known-gaps.md`, `strategy.md` "What P4 adds", MTP status line updated; P4 actuals
- [ ] **NEEDS YOU (decision):** approve PP-2 and PP-3; decide PP-4 (your SRS wording); PP-9 (effort row)
- [ ] 12. Check: SDD §14 gate items each with evidence below; no V-item open; `test_runbooks.py` and `poe check` pass
- [ ] PR 5 closed: agent __ h, owner __ h

## PR 6: hardening (`tooling/p4-v1`)

- [ ] **NEEDS YOU (decision):** default site generator (OD-13)
- [ ] 13a. Site-generator ADR (ADR-014 unless that number is taken first) drafted with the step 9 (f) evidence, Zensical release history and the Material audit record (PP-10)
- [ ] 13b. `pyproject.toml` and the template profile at `1.0.0`; a test that they agree (OD-18)
- [ ] 13c. README stable; known gaps a library owner should know
- [ ] 13d. `v1.0.0` tag message drafted (below)
- [ ] **NEEDS YOU (account):** archive `p3-scratch-github`, `p0-spikes` and the P4 scratch repositories; delete the sandbox App key and uninstall it when no rehearsal needs it (OD-20)
- [ ] 13f. Full gate on 3.11 and 3.14 and CI on three systems on the PR 6 head; coverage figure
- [ ] PR 6 closed: agent __ h, owner __ h

## Exit

- [ ] SPEC "Done when" 1 to 12 met, evidence in the Outcomes table
- [ ] **NEEDS YOU (setting):** immutable releases on for `open-renewables/okf-library-template` (OD-15)
- [ ] **NEEDS YOU (person):** push annotated tag `v1.0.0` on the PR 6 merge commit
- [ ] 14. `release.yml` published a release not marked pre-release; download verified; an asset deletion refused; "Done when" 13 ticked
- [ ] Proposed entries decided and, where approved, applied; conditional ones closed as "not needed" or decided
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p4-pilot-hardening/` and re-point links
- [ ] **NEEDS YOU (decision):** set the SRS status to `Done` (OD-21); the agent does not change it
- [ ] Pilot repository archived after `v1.0.0` (OD-2)

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any. Include agent and owner hours per pull request and session.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |
| 1 | PR D merged as #48. Dependabot #24 to #28 changed only `requirements/*.txt` and no CI ran on them (G41); replaced by `uv lock --upgrade-package` for five dev packages and `poe export`. `nodeenv` 1.12.0 licence re-read, unchanged; its `constraints.md` row moved to 1.12.0 with the owner's approval. `poe licences` 0 findings, `poe audit` clean, 820 passed before the version test fix | [Test] | |
| 2 | PR 1. Folder-scope header built (ADR-010). Found: OKF v0.2 §8 and §12 allow no frontmatter on a folder index, and §11 makes that conformance; OKF v0.3 (2026-11-18, new repository; the pinned one deprecated) allows root `title`, `description`, `license` but still no folder frontmatter. Owner kept the YAML header for Obsidian and site generators (Option A); ADR-012 replaces okf-skills' per-index `OKF117` with one `OKF121` per bundle; `OKF505`, `OKF506` for unusable headers; G42. 829 passed, coverage 98.13 %. OKF v0.3 assessment handed to the parent session | [Test] | PP-1, ADR-012 |
| 3 | PR 2 merged as #50. `new_concept.py --set key=value` (declared keys only; scalars or lists) and `rename_type.py` (`poe rename-type`), which renames a type and its `uid` prefix in the profile, the schema file, the bundle, the registry and `tests/library/` and rebuilds the indexes; tested by renaming `Item` to `Risk`/`RSK` in a copy (every library fixture still raises its own code). Review on 2026-11-19 found ten points; three fixed before merge (binary files skipped and every change worked out before writing; other types' schema names untouched; rename before the first commit, because check 6 reports a renamed `uid` as OKF606 and OKF607, with a warning when the registry is committed); seven left open (whole-word rename of other text, quoted values, no release-tag guard, three reuse items). PP-8 applied; G23 narrowed. 854 passed | [Test] | PP-8 |
| 4 | PR 3 merged as #51. 53 acceptance cases moved from `pending P2` to `ready`, 7 to `ready for P4`; AT-FR4.3-02 and AT-FR8.1-02 added; MTP §11 records OD-AT1 to OD-AT5 as decided; `testing/runs/` with the entry criteria and three planned parameter files | [Doc] | |

### MTP §7 entry criteria

| Criterion | State |
| --- | --- |
| Template build complete (P3 merged, `v0.5.0` tagged) | Met 2026-11-15 |
| `poe check` and `poe test` pass on the tag under test | On `v0.9.0`, step 5 |
| Every case's `pending` status cleared or recorded `blocked` | Step 4 |
| Parameter file filled and reviewed | Step 4 |
| Sandbox repositories exist (E-GH); token in its environment variable | Steps 8, 9, 11 |

### SDD §14 v1.0.0 gate

| Gate item | Evidence |
| --- | --- |
| V-01 to V-13 closed, outcomes recorded in the DDR | Step 12, PP-2 |
| FR1 to FR8 verified as in SDD §13 | Step 11 results; step 12 |
| CI passes | Step 13f; `v1.0.0` run |
| A second person instantiates a library in under 30 minutes | Step 8: the owner's scenario build (8a) with PP-13 or an owner-recorded deviation; met as written only if 8b ran |
| An agent's outputs trace to `uid`s and a release tag | Step 10 |
| No open error-level defect (S1, S2) | Step 11 |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | P3 PP-13 approved 2026-11-14; text approved 2026-11-19 and applied in PR 1 | SRS FR4.3; SDD I-07; DDR change-log row 2026-11-19; ADR-012 |
| PP-2 | Proposed | |
| PP-3 | Proposed | |
| PP-4 | Owner's wording | |
| PP-5 | Conditional (AT-FR2.5-03) | |
| PP-6 | Optional, owner edit | |
| PP-7 | Conditional (OD-7) | |
| PP-8 | Proposed, with PR 2 | |
| PP-9 | Proposed now and at exit | |
| PP-10 | Proposed (ADR-014, the next free number) | |
| PP-15 | Approved and applied 2026-11-20 with PR V | ADR-013; SDD AD-08, I-01 to I-03, I-07 to I-09, §15; DDR change-log row |
| PP-16 | Owner's SRS wording, with PR V (RFC-002 §4) | |
| PP-11 | Conditional (step 9 e) | |
| PP-12 | Conditional (step 8) | |
| PP-13 | Conditional (no step 8b) | |
| PP-14 | Proposed (option B chosen 2026-11-17) | |

## Draft: message of the annotated tag `v0.9.0`

To be completed in step 5.

## Draft: message of the annotated tag `v1.0.0`

To be completed in step 13d.
