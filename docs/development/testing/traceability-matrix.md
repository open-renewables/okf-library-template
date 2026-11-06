# Traceability matrix

Maps every acceptance criterion of the SRS, the verification items of SDD §13 and §15, the P2 "Done when" items and the known gaps to the cases in [acceptance-test-cases.md](acceptance-test-cases.md). The criteria are quoted in short form; the SRS text governs. A "—" in the SRS criterion column is shown as such.

**Flags.** `U` = cannot be tested as written (reason in the last column; a suggested rewording is a proposed entry in [master-test-plan.md](master-test-plan.md), never an edit to the SRS). `P` = partly testable without a second GitHub account (OD-AT1). `R` = review only, no pass/fail from a tool.

## SRS functional requirements

| Req | Criterion (short) | Cases | Flag and note |
| --- | --- | --- | --- |
| FR1.1 | Pinned OKF checker reports no error on the example bundle | AT-FR1.1-01, AT-FR1.1-02 | — |
| FR1.2 | A fixture per rule fails with its own code | AT-FR1.2-01, AT-FR1.2-02 | — |
| FR1.3 | Missing, malformed, duplicated, changed uid fail | AT-FR1.3-01, AT-FR1.3-02, AT-FR1.3-03 | Never-reused and 9,999 cap are not in the criterion; added as cases |
| FR1.4 | Hand edit putting registry out of step fails | AT-FR1.4-01 | — |
| FR1.5 | One fixture per case fails with its own code | AT-FR1.5-01, AT-FR1.5-02 | — |
| FR1.6 | Same-number merge fails on main; renumber clears | AT-FR1.6-01, AT-FR1.6-02 | — |
| FR1.7 | Deleting a concept file fails validation | AT-FR1.7-01 | — |
| FR2.1 | New type by profile only passes; no domain rule in tooling | AT-FR2.1-01, AT-FR2.1-02 | `R` for the second half: "review finds no domain rule" is a judgement; the grep makes it repeatable |
| FR2.2 | Each of six checks has a failing fixture | AT-FR2.2-01, AT-FR2.2-02 | — |
| FR2.3 | Output lists code, level, file, line | AT-FR2.3-01 | "Errors block merge where the platform can enforce" is covered by AT-FR2.4-01 |
| FR2.4 | Failing main commit opens or updates one issue | AT-FR2.4-01, AT-FR2.4-02 | — |
| FR2.5 | Relaxing PR with non-conforming concept fails | AT-FR2.5-01, AT-FR2.5-02, AT-FR2.5-03, AT-FR2.5-04 | AT-FR2.5-03 probes a case the design does not state (the PR's own workflow file) |
| FR2.6 | Mixed PR fails; label without approval fails | AT-FR2.6-01, AT-FR2.6-02 | `P`: the maintainer approval needs a second account for a live run |
| FR2.7 | OKF `verified` passes when unknown fields are rejected | AT-FR2.7-01 | — |
| FR2.8 | Local and CI runs give the same findings | AT-FR2.8-01, AT-FR2.8-02 | — |
| FR2.9 | Tag missing from its vocabulary fails check 4 | AT-FR2.9-01 | — |
| FR2.10 | Glossary anchor link resolves on platform and site; changed anchor fails | AT-FR2.10-01, AT-FR2.10-02 | The platform and site halves are human and need the P3 site; G3 |
| FR2.11 | Each CI job invokes only documented local commands | AT-FR2.11-01, AT-FR2.11-02 | — |
| FR3.1 | Golden files cover each approval case | AT-FR3.1-01, AT-FR3.1-02, AT-FR3.1-03 | `P`: owner-approved and merged-without-approval rest on fixtures |
| FR3.2 | With one run suppressed, next run records both | AT-FR3.2-01, AT-FR3.2-02 | — |
| FR3.3 | Check 5 passes on main after each revision commit | AT-FR3.3-01 | — |
| FR3.4 | Hand edit to the section fails check 3 | AT-FR3.4-01, AT-FR3.4-02 | `U` as written: content alone cannot show authorship (G4). The cases test what is detectable and record the rest |
| FR3.5 | Each approval case recorded correctly in a scratch library | AT-FR3.5-01, AT-FR3.5-02, AT-FR3.5-03 | `P` (OD-AT1) |
| FR3.6 | Approve, change, merge records a stale approval | AT-FR3.6-01 | Live via App-submitted review; no second account needed |
| FR3.7 | Golden files cover each tier case | AT-FR3.7-01, AT-FR3.7-02 | — |
| FR3.8 | An OKF tool's derived tier equals the library's | AT-FR3.8-01 | `U` as written: no OKF reference tool derives a tier; the case uses a reader written from the V-11 rule |
| FR3.9 | Undeclared status fails | AT-FR3.9-01 | — |
| FR3.10 | Stable concept without citation fails | AT-FR3.10-01 | — |
| FR3.11 | Fixture past each limit is reported | AT-FR3.11-01, AT-FR3.11-02 | — |
| FR4.1 | Golden index files match the generator | AT-FR4.1-01 | Golden shapes are unit-level (strategy.md); acceptance checks the library |
| FR4.2 | Golden files show each tier | AT-FR4.2-01 | — |
| FR4.3 | Stale or hand-edited index fails check 5 | AT-FR4.3-01 | — |
| FR5.1 | PR template lists each label | AT-FR5.1-01 | `R` |
| FR5.2 | Agent trailer without label raises warning | AT-FR5.2-01 | — |
| FR5.3 | Pilot contribution from issue form to merged concept | AT-FR5.3-01, AT-FR5.3-02 | Needs a person who does not use git; not a GitHub account question |
| FR5.4 | PR touching two folders records each owner status | AT-FR5.4-01 | — |
| FR5.5 | Instantiated library holds decision record with entry | AT-FR5.5-01 | — |
| FR6.1 | Second person: library and first concept in 30 minutes | AT-FR6.1-01, AT-FR6.1-02 | Needs a second person (OD-AT1); "a second person" is undefined for solo-owner teams |
| FR6.2 | Chosen licences, Apache text and notice present | AT-FR6.2-01, AT-FR6.2-02 | — |
| FR6.3 | Self-test fails if placeholder or template-only file remains | AT-FR6.3-01, AT-FR6.3-02, AT-FR6.3-03 | — |
| FR6.4 | — (constraint on design) | AT-FR6.4-01, AT-FR6.4-02 | `U`: no criterion. Cases test the supported clone-and-merge route (QA-52) and divergence |
| FR6.5 | Git-local library works with no platform API call | AT-FR6.5-01, AT-FR6.5-02 | — |
| FR6.6 | After move, commit ids and lines unchanged; archives match | AT-FR6.6-01, AT-FR6.6-02 | — |
| FR7.1 | Both skills work on the pilot without edits | AT-FR7.1-01, AT-FR7.1-02, AT-FR7.1-03 | Agent runs vary by provider; pass means the stated expectations hold, not identical text |
| FR7.2 | Reviewer traces outputs to uids and a tag | AT-FR7.2-01, AT-FR7.2-02 | `R`: "traces" is judged by a reviewer; the cases set 100 % of citations resolving as the pass line |
| FR7.3 | Archive readable without tooling; checksum verifies | AT-FR7.3-01, AT-FR7.3-02, AT-FR7.3-03 | — |
| FR7.4 | Release with a missing line fails | AT-FR7.4-01 | — |
| FR8.1 | Site build reads the bundle in place | AT-FR8.1-01 | — |
| FR8.2 | Test build passes each of six checks | AT-FR8.2-01, AT-FR8.2-02, AT-FR8.2-03, AT-FR8.2-04 | Check 2 wording follows the owner's rewording of 2026-10-30 (DDR change log) |
| FR8.3 | Site manifest matches latest tag | AT-FR8.3-01 | — |
| FR8.4 | Both links work on a preview build | AT-FR8.4-01 | — |
| FR8.5 | — (governance rule) | AT-FR8.5-01 | `U`: no criterion; the case checks the one observable consequence (no Pages site before v1.0.0) |

## SRS non-functional requirements

| Req | Criterion (short) | Cases | Flag and note |
| --- | --- | --- | --- |
| NFR1 | Release archive usable with file tools only | AT-NFR1-01 | — |
| NFR2 | Review finds no requirement met by only one product | AT-NFR2-01 | `R`: judgement over the SRS text |
| NFR3 | Pilot runs on a free organisation | AT-NFR3-01 | `R`: a billing and plan check |
| NFR4 | Licence files present; dependency check passes allowlist | AT-NFR4-01, AT-FR6.2-01 | — |
| NFR5 | — (authoring rule, enforced by review) | AT-NFR5-01 | `U`, `R`: no criterion and no tool; sample review only |
| NFR6 | Workflow review; planted test secret detected | AT-NFR6-01, AT-NFR6-02, AT-NFR6-03, AT-NFR6-04, AT-NFR6-05 | The vulnerability and hash parts are not in the criterion; added from SDD §10 |
| NFR7 | Set-up rerun restores settings; clean install passes | AT-NFR7-01, AT-NFR7-02, AT-NFR7-03 | — |

## SDD §12 quality attributes (not SRS criteria)

| Item | Target | Cases |
| --- | --- | --- |
| Validation speed | 600 concepts under 10 s locally | AT-SDD12-01 |
| `validate` job | Under 3 minutes | AT-SDD12-02 |
| Self-test time | Budget in performance.md | AT-SDD12-03 |

## SDD §13 and §15 verification items

Most §13 verification phrases repeat the SRS criteria and are covered above. Those that add something, and the items carried past P0:

| Item | What it verifies | Cases |
| --- | --- | --- |
| §13 FR1 | Duplicate-uid push test with `renumber.py` | AT-FR1.6-01, AT-FR1.6-02 |
| §13 FR2 | Base-tooling and mixed-change tests; local and CI parity | AT-FR2.5-01 to -04, AT-FR2.6-01, AT-FR2.8-02 |
| §13 FR3 | Dropped-run catch-up; pilot merges of each approval case; V-11 | AT-FR3.2-01, AT-FR3.1-02, AT-FR3.5-01, AT-FR3.8-01 |
| §13 FR5 | Per-concept owner status test | AT-FR5.4-01 |
| §13 FR6 | Self-test both modes; timed by a second person (V-06); git-local release rebuilt and matched (V-12); W-12 rehearsed on the pilot | AT-FR6.3-01, AT-FR6.1-01, AT-FR7.3-02, AT-FR6.6-01 |
| §13 FR7 | Pilot agent run from the archive traced to uid and tag; release gate test | AT-FR7.2-01, AT-FR7.4-01 |
| §13 FR8 | Six compatibility checks on the pilot bundle (V-03, V-04); edit and issue links | AT-FR8.2-01 to -03, AT-FR8.4-01 |
| §13 NFR6 | Planted secret in CI and by the local hook; pip-audit on a lock change | AT-NFR6-01, AT-NFR6-02, AT-NFR6-03 |
| §13 NFR7 | Catch-up test; `setup_repo.py` rerun; clean install | AT-FR3.2-01, AT-NFR7-01, AT-NFR7-02 |
| V-01 | GitHub scroll to explicit anchors | AT-FR2.10-02 |
| V-05 5a, 5c | App "always" bypass; approval and stale-approval API shapes | Closed in P2 sandbox session S1 (plan step 1); exercised again by AT-FR3.1-02, AT-FR3.6-01 |
| V-06 | Second person times W-01 | AT-FR6.1-01, AT-FR6.1-02 |
| V-07 | Immutable releases (private repository), Cloudflare limits | AT-FR7.3-03; Cloudflare only if a library wants a private preview, otherwise none |
| V-11 | `verified` to tier derivation | AT-FR3.8-01 |
| V-12 | Archive digest across systems | AT-FR7.3-02 |
| V-13 | poe tasks and hooks on three systems | AT-FR2.11-01 |
| V-03, V-04 | Site generator behaviour | AT-FR8.2-01 to -04 |

## P2 "Done when" (`../plan/SPEC.md`)

| # | Item | Cases |
| --- | --- | --- |
| 1 | check and test on 3.11 and 3.14 locally and in CI on three systems | AT-FR2.11-01 |
| 2 | V-05 5a and 5c closed before `revision.yml` | Plan step 1 (not repeated); AT-FR3.6-01 |
| 3 | Every `OKF9xx` code has a failing fixture | AT-FR2.2-01 |
| 4 | Golden files cover each I-08 approval row, catch-up, `verified`, git-local trailers | AT-FR3.1-03, AT-FR3.7-01, AT-FR3.8-01, AT-FR3.5-02 |
| 5 | Scratch GitHub library records each producible case, dropped run, duplicate uid; git-local the same | AT-FR3.1-01, AT-FR3.1-02, AT-FR3.2-01, AT-FR3.2-02, AT-FR1.6-01 |
| 6 | Self-test passes both modes; planted secret and marker caught | AT-FR6.3-03, AT-NFR6-01, AT-NFR6-02 |
| 7 | git-local release rebuilt reproduces digest; equal on three systems; W-12 rehearsal | AT-FR7.3-02, AT-FR6.6-01 |
| 8 | `validate` required on the template ruleset; mixed PR fails; failing main opens one issue | AT-FR2.6-02, AT-FR2.4-02 |
| 9 | `setup_repo.py` rerun restores; clean install passes | AT-NFR7-01, AT-NFR7-02 |
| 10 | Runbooks exist; testing documents updated | Review at the P2 exit (not an acceptance case) |
| 11 | `v0.2.0` tagged; entries decided | Process step, not a test |

## Known gaps (`known-gaps.md`)

| Gap | Closed or narrowed by |
| --- | --- |
| G1, G10 | AT-FR2.11-01 |
| G2 | AT-FR8.2-04 |
| G3 | AT-FR2.10-02 |
| G4 | AT-FR3.4-02 (narrowed; stays open by design) |
| G5, G6 | Not acceptance work: G5 needs a library declaring such a type, G6 an RFC before P3 |
| G7 | AT-NFR6-01, AT-NFR6-02 |
| G8 | AT-SDD12-01, AT-SDD12-02 |
| G9 | AT-FR3.1-01 to -03, AT-FR3.5-01 to -03, AT-FR3.6-01 |
| G11 | AT-NFR4-01 |
| G12 | AT-NFR6-02 |
| G13 | AT-NFR6-03 |
