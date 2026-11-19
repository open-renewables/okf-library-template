# SPEC: build phase P4, pilot and hardening

Status: **Approved by the owner on 2026-11-19:** the plan as drafted, with OD-9, OD-22, OD-23 and OD-24 answered explicitly and the other open decisions on their defaults. Proposed entries are approved one by one when their text is shown. Nothing is built. Drafted on branch `claude/p4-plan-70c902` (not committed). Effort is in agent hours, owner hours and calendar days, as for P2 and P3 **[Inf]** (`plan.md`, "Effort").

## Requirement and sources

| Document | Role | Status |
| --- | --- | --- |
| [SRS](<../requirements/OKF Library Template - Software Requirements Spec.md>) | The requirement; "Next steps" and the template v1.0.0 gate. Front matter `status: accepted` | Accepted |
| [SDD](<../architecture/OKF Library Template - Software Design Document.md>) §13 (traceability), §14 (P4 row, carried verification items, v1.0.0 gate), §15 (V-01 to V-13), C-07, I-02, I-07, W-01, W-11, W-12 | Defines the phase and its gate | Fixed for P4 |
| [DDR](<../adr/OKF Library Template - Design Decision Record.md>) | QA-30 (template first), QA-45 (effort), QA-52 (merging template tags), QA-58 to QA-61 (git-local, W-12) | Frozen series; change-log rows still added |
| [ADR-001 to ADR-011](../adr/README.md) | Notably ADR-001 (Zensical switch criterion, judged on the pilot bundle), ADR-002 (provider-neutral skills), ADR-010 (folder-scope header, built in P4), ADR-011 (generator per library; default revisited before v1.0.0) | Accepted |
| [P3 close-out](archive/2026-11-p3-site-release-skills/todo.md) | Carried items: P3 PP-13 (approved, applied when the header is built), sandbox clean-up, the P4 estimate (P3 PP-15, applied to SDD §14) | Applied |
| [Master Test Plan](../testing/master-test-plan.md), [acceptance cases](../testing/acceptance-test-cases.md), [traceability matrix](../testing/traceability-matrix.md), [parameter file](../testing/library-under-test.yaml) | The acceptance level, run at P4; open decisions OD-AT1 to OD-AT5 and PE-AT-1 to PE-AT-5 | Draft; decided in this plan |
| [Known gaps](../testing/known-gaps.md) | G3, G23, G32, G35, G38, G39 open or carried to P4 | Current |
| [`runbook-instantiate-library.md`](../operations/runbook-instantiate-library.md) | The V-06 run sheet | Current |

**Abbreviations.** P4: build phase 4, "Pilot and hardening" (SDD §14). FR/NFR: SRS requirements. AD-, QA-, DR-, ADR-: decision IDs, cited as written. I-nn, C-nn, W-nn, V-nn: SDD items. G-n: known gap. AT-: acceptance case. MTP: Master Test Plan. LUT: library under test. RC: release candidate. PP-n: a proposed entry for the owner in this plan; "P3 PP-n" is an entry of the archived P3 plan. OD-n: an open decision with a default (`plan.md`). OD-ATn and PE-AT-n: the MTP's own open decisions and proposed entries.

P4 is the last phase of the SRS. The SRS is set to `Done` by the owner after `v1.0.0` ships (`../AGENTS.md`, Flow 6); this plan only proposes it.

## Goal

Meet the SDD §14 P4 exit and the template v1.0.0 gate: a pilot library built from the template holds about 20 real concepts; CI passes; a library is created and a first validated concept merged in under 30 minutes, timed against the owner's mapped-out real-life scenario (default) or, optionally, by a second person (FR6.1, V-06; OD-9); an agent using a pilot release produces answers a reviewer can trace to `uid`s and a release tag (FR7.2); V-01 to V-13 are closed; FR1 to FR8 are verified as in SDD §13; no S1 or S2 defect is open; and the owner tags `v1.0.0` (stable) as an immutable release.

## Scope

| Area | Delivered in P4 | Source |
| --- | --- | --- |
| Folder-scope header | `build_indexes.py` keeps a `description` header on a folder `index.md` and writes it on the parent's folder line; check 5 treats the header as input; fixtures, golden files; `author-concept` guidance; P3 PP-13 applied (SRS FR4.3 wording by the owner, SDD I-07 and I-02) | ADR-010; G6; FR4.1, FR4.3 |
| Authoring aids | `new_concept.py --set key=value` (a Vocabulary's `namespace`); a documented primary-type rename procedure, run on the pilot (G23); the PP-9 warning kind decided on pilot content (P3 OD) | G23; SDD I-01, I-02 |
| Dependencies | Dependabot pull requests #24 to #28 merged or replaced | NFR6 |
| Test readiness | AT case statuses refreshed (most still say `pending P2 PRn`); MTP open decisions answered; the parameter file filled for each run | MTP §7 entry criteria |
| User documentation | A library user guide (option B, decided 2026-11-17, OD-22): getting started, maintaining a library, customising the profile, reference; the five operational runbooks and `finding-codes.md` moved out of the template-only `docs/development/` so libraries keep them (in `docs/guide/`, decided 2026-11-17, OD-23; PP-14). Drafted as a library guide; during `init_library` the user chooses to **morph** it into the new library's own guide (template-only and wrong-platform text stripped, placeholders rewritten, a conventions stub added) **copy** it unchanged, or **remove** it (OD-24). Added 2026-11-17 | SDD §6; W-01, W-11, W-12; NFR7 |
| OKF v0.3 | Added 2026-11-19 by RFC-002 (owner decisions D1 to D7): the profile pins OKF v0.3 at `527e81a`; check 1 uses the OKF project's validator, vendored and mapped by code (amends AD-08); root index metadata (`title`, `license`) written and kept; check 4 resolves path fields by v0.3 §6.2; the I-08 `verified` currency rule; ADR-013; the SRS wording is the owner's (PP-16) | RFC-002; FR1.2; AD-08 |
| Release candidate | `v0.9.0` pre-release on the template, the version the pilot and the timing use (OD-8) | MTP §7 `template_tag` |
| Pilot library | Instantiated from `v0.9.0`, primary type renamed, about 20 RE solar PV risks with folder-scope headers, vocabulary values and glossary entries; started `git-local` with two local releases, moved to GitHub by W-12, promoted by W-11 | SDD §14 P4 row; §13 FR6 ("W-12 rehearsed on the pilot"); G32 |
| Platform cases on the pilot | A contribution through an issue form (FR5.3); a second directory owner approves and merges, only if a second account exists (G35, OD-9); glossary anchors scroll on GitHub (G3, V-01); the six FR8.2 checks on the pilot bundle with both generators (ADR-001 criterion) | FR2.10, FR3.5, FR5.3, FR8.2 |
| Library-build test | Default: the owner builds a library for a mapped-out real-life scenario from the W-01 run sheet, timed per step, recording where the template and the sheet fall short of the scenario. Optional: a second person runs W-01 on scratch libraries, `github` then `git-local`, without help | FR6.1; V-06; AT-FR6.1-01, -02 |
| Traced agent run | `use-bundle` on the pilot's release archive; every citation traced; an Unverified concept reported as unverified | FR7.2; AT-FR7.2-01, -02 |
| Acceptance run | MTP phases 1 to 5 by hand, evidence in `../testing/runs/`; defects triaged by severity and fixed or recorded | MTP §6, §7, §9 |
| Verification closure | V-01 to V-13 closed and recorded; SDD §13 rows verified | SDD §14 gate; §15 |
| Hardening | Default site generator decided (ADR-014, the next free number); immutable releases on the template; version fields set to `1.0.0`; README and release notes; sandbox clean-up | ADR-011; P3 OD-9; P3 carried |
| Exit | `v1.0.0` tagged by the owner; `release.yml` publishes an immutable release; verified by download | SDD §14 |

### Requirements covered

| Requirement | In P4 | Left after v1.0.0 |
| --- | --- | --- |
| FR1 to FR3 | Re-run end to end in the pilot and scratch libraries (MTP phases 2 to 4); the two approval cases that need a second account run live only if one exists (G35) | Without a second account: G35 stays a known gap, AT-FR3.5-01 `partial` |
| FR4.1 to FR4.3 | Folder-scope header (ADR-010) with the FR4.3 exception worded by the owner | — |
| FR5.3 | Pilot contribution from an issue form to a merged concept | — |
| FR6.1 | Timed library build against the owner's real-life scenario; second-person timing if the owner arranges it | Without a second person, "a person new to the template … timed by a second person" is not met as written: an owner-accepted `partial` and the FR6.1 wording in PP-4 |
| FR6.6 | W-12 on the pilot with several tags (G32) | — |
| FR7.1, FR7.2 | Both skills on the pilot without edits; traced run | A second runtime (G38) unless the owner runs one |
| FR8.2 | Six checks on the pilot bundle, both generators | — |
| NFR1 to NFR7 | Acceptance cases in the MTP run | — |

## Out of scope

- Domain content beyond the pilot's 20 concepts; the RE risk library itself (built from `v1.0.0` or later, QA-30). Pilot content may be carried into it later by the owner.
- Adapters for other hosting platforms; pre-filled per-page issue links (QA-37); `format_item_consistency`, `linked_set_drift`, `citation_index` (QA-45); Copier (AD-10).
- The MTP automation harness and scratch-library generator (MTP §8): cases run by hand in P4 (OD-11).
- Upstream engagement (SRS "Next steps": an OKF issue and contributing the validator): after `v1.0.0`, the owner's call.
- Any change to a requirement or decision without an approved proposed entry; requirement statuses (the owner's).
- A public site for the template (FR8.5); the pilot may deploy one only if it reaches its own `v1.0.0`, which is not planned (OD-2).

## Carried into P4

| Source | Item | Where in `plan.md` |
| --- | --- | --- |
| SDD §14 P4 row | Instantiate a pilot; about 20 concepts with scope notes, vocabulary values and glossary entries; second person times W-01 (optional here; the owner's scenario build by default); agent run; the folder-scope header | Steps 2, 6 to 10 |
| SDD §14 carried items | V-06 (step 8; PP-13 if closed by the owner's build); V-07 private-repository immutability and Cloudflare: "only if a library wants a private preview or release; otherwise none" (step 12) | Steps 8, 12 |
| SDD §14 v1.0.0 gate | V-01 to V-13 closed; FR1 to FR8 verified; pilot gate; no open error-level defect | Steps 11, 12, 14 |
| ADR-001, ADR-011 | Zensical criterion on the pilot bundle; default generator revisited before `v1.0.0` | Steps 9, 13 |
| ADR-010, P3 PP-13 | Build the header; apply the SRS FR4.3 and SDD I-07, I-02 wording | Step 2 |
| P3 OD (PP-9) | Whether a warning kind for the two Python-Markdown divergences is worth building, judged on real content | Step 3 |
| P3 OD-9 | Immutable releases on the template before `v1.0.0` | Step 13 |
| P3 carried | Archive `p3-scratch-github` and `p0-spikes`; delete the sandbox App's key and uninstall it | Step 13 (OD-20) |
| G3, G23, G32, G35, G38 | Anchor scroll on GitHub; primary-type rename; W-12 with several tags; second approver; second runtime | Steps 3, 9, 10 |
| MTP | OD-AT1 to OD-AT5; PE-AT-1 to PE-AT-5; case statuses | Step 4; PP-3 to PP-6 |
| Dependabot | Open pull requests #24 to #28 (dev-group bumps, opened 2026-11-07) | Step 1 |
| Owner review 2026-11-17 | No user documentation step: `init_library` removes all of `docs/`, so libraries lose the operational runbooks (instantiate, promote, move, revision recovery, leak removal) and the finding-code reference; no human guide to customising the profile | Step 4a |
| Found while planning | `pyproject.toml` says `version = "0.1.0a0"` and the template profile says `template_version: 0.1.0`, both behind `v0.5.0` | Step 13 |

G1, G2, G4, G5, G9 to G22, G24 to G31, G33, G34, G36, G37, G39, G40 are unchanged unless a step says so; G39 is restated in the release notes.

## Quality bar and conventions

- `../constraints.md` applies in full and is not weakened; a limit P4 cannot meet is a proposed entry.
- `../conventions.md` governs: one change per pull request; tooling and content in separate pull requests (in the pilot too); branch `<kind>/<slug>`; British English.
- `../testing/`: tests use no network; a behaviour that cannot be tested goes to `known-gaps.md`; MTP defects use its S1 to S4 severities.
- Destructive and live-platform cases run only on scratch libraries in `open-renewables-sandbox` (MTP §1); the pilot gets destructive cases only before it is promoted, and the read-only subset after (OD-AT4).
- Provider-neutral: no `.claude/` or product file committed (ADR-002).

## Done when

1. `uv run poe check` and `uv run poe test` pass locally on Python 3.11 and 3.14 and in CI on three systems on the `v1.0.0` commit, with `constraints.md` changed only by an approved entry.
2. The folder-scope header is built and tested (ADR-010); P3 PP-13 is applied with the owner's FR4.3 wording.
3. `new_concept.py --set` exists; the primary-type rename procedure is documented and was followed on the pilot; G23 is closed or narrowed.
4. Dependabot pull requests #24 to #28 are merged or closed with a replacement; the template pins OKF v0.3 and validates with the OKF project's validator before `v0.9.0` (RFC-002, ADR-013); the user documentation of the chosen option (OD-22) is in place, is kept in an instantiated library, morphed, copied or removed as the user chose at `init_library` (OD-24), with all three answers tested, no template-only text or unresolved placeholder after a morph, and every link and command resolving, and was followed in step 8a.
5. The pilot, instantiated from `v0.9.0`, holds about 20 concepts of its primary type, each folder with a scope header, with vocabulary values and glossary entries; `poe check` passes; at least five concepts are owner-reviewed (`full-review`), some are agent-drafted and Machine-confirmed, and at least one is `draft` and Unverified, so every tier appears in its indexes.
6. The pilot moved from `git-local` to GitHub by W-12 with at least two tags, each archive matching its tag-message digest; revision after the move used the App token (G32).
7. Live on the pilot: an issue-form contribution merged as a concept (FR5.3); if a second account exists, an approval by a second directory owner and a merge by someone other than the author (G35), otherwise G35 recorded as a known gap at `v1.0.0`; glossary anchors scroll for plain, non-ASCII and parenthesised terms (G3, V-01); the six FR8.2 checks pass on the pilot bundle with both generators.
8. The owner built a library for the mapped-out real-life scenario from `v0.9.0` and the run sheet, created it and merged a first validated concept in under 30 minutes, each step timed; the scenario's needs that the template does not meet are defects or known gaps; the run sheet is corrected where it was unclear (FR6.1, V-06). If a second person was arranged, their `github` and `git-local` times are recorded too and are the FR6.1 evidence.
9. A fresh agent, given the pilot release archive only, answered the reviewer's questions with 100 % of citations traced to `<uid>@<tag>` and status and tier as written, and reported the Unverified concept as unverified (FR7.2).
10. The MTP run is recorded in `../testing/runs/`; every FR1 to FR8 criterion has a case with `pass`, or `partial` accepted by the owner; no S1 or S2 defect is open.
11. V-01 to V-13 are closed and recorded (PP-2); `known-gaps.md` and the testing documents are current; P4 actuals are recorded (PP-9).
12. The default site generator for `v1.0.0` is decided and recorded (ADR-014, the next free number); immutable releases are on for the template; version fields say `1.0.0`; the sandbox is cleaned up.
13. The owner has tagged `v1.0.0`; `release.yml` published an immutable release (not a pre-release); the downloaded archive verifies.

## Interpretations the owner should confirm

1. **The pilot is throwaway** (SRS executive summary): it lives in `open-renewables-sandbox`, is archived after `v1.0.0`, and its concepts may be reused in the RE risk library.
2. **The pilot starts `git-local` and moves to GitHub** (OD-3), because SDD §13 verifies FR6.6 by "W-12 rehearsed on the pilot" and G32 needs several tags. The timed library build is a separate library (the owner's scenario, or scratch libraries for a second person), so the pilot's history is not part of the timed run.
3. **The second person is optional; the owner's real-life scenario build is the default test of the library build process** (OD-9). The owner is not new to the template, so FR6.1 and the SDD §14 gate item ("a second person instantiates a library in under 30 minutes") are met as written only if a second person also runs it. Without one, the owner's timed build is the evidence, recorded as `partial` with the owner's acceptance, and the wording is the owner's to change (PP-4 for FR6.1, PP-13 for SDD §14 and V-06). G35 needs a second GitHub account, not necessarily a second person; without one it stays a known gap.
4. **"V-01 to V-13 closed"** means answered, or carried to "not needed" with the owner's acceptance. V-07's remaining parts (immutability on a private repository, Cloudflare limits) apply "only if a library wants a private preview or release" (SDD §14); none does, so the default is to close them as not applicable (OD-14).
5. **"FR1 to FR8 verified as in SDD §13"** means the traceability matrix shows `pass` for each criterion, or `partial` accepted by the owner (MTP §7). FR6.4 and FR8.5 have no testable criterion (PE-AT-3).
6. **The MTP is run by hand** (no harness), by the agent for scripted cases and by the owner for live ones (OD-AT1, OD-11).
7. **A release candidate `v0.9.0`** is tagged after the tooling and user-documentation pull requests, so the pilot, the timing and the MTP run all name one template version. `v1.0.0` follows on the commit that carries the evidence and any fixes.
8. **The bottom-up estimate exceeds the SDD §14 P4 row** (`plan.md`, "Effort"); the row is not changed unless the owner approves PP-9.

## Exit

"Done when" 1 to 13: pull requests merged by squash, `v1.0.0` pushed by the owner, proposed entries decided; then, on the owner's instruction, the three plan files move to `plan/archive/2026-11-p4-pilot-hardening/` (or the month it ships) and the owner is asked to set the SRS to `Done`.
