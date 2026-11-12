# Todo: build phase P3

Checklist for `plan.md`; scope and done-when in `SPEC.md`. Tick an item when its check in `plan.md` has passed and the evidence (command and result) is noted in the Outcomes table. **NEEDS YOU** marks a decision, person, account, machine or setting from the owner. Nothing is committed, pushed or merged without the owner's instruction. When a pull request closes, note its agent time and owner time in the Outcomes table (plan, rule 9).

## Before any step

- [x] Owner reviews `SPEC.md`, `plan.md` and `todo.md` (approved 2026-11-11)
- [x] **NEEDS YOU (decision):** owner answers OD-1 to OD-15 or accepts the defaults (`plan.md`, "Open decisions"; defaults accepted 2026-11-11); OD-4 (scope notes), OD-5 (archive carries the tag), OD-6 (Pages rehearsal) and OD-9 (`v0.5.0` Release on the template) are the ones that change work
- [x] **NEEDS YOU (decision):** owner approves or rejects PP-1 to PP-6 (approved as drafted 2026-11-11); PP-7 to PP-11 are conditional (`plan.md`, "Proposed entries")
- [x] **NEEDS YOU (decision):** owner confirms the effort units and basis in `plan.md` "Effort" (owner about 7–11 h against the SDD's 2 h)

## PR 1: skills and `AGENTS.md` (`tooling/p3-skills`)

- [x] PP-5 approved 2026-11-11 (text shown when written)
- [x] 1. `scripts/check_skills.py`, `poe check-skills` in `poe check`; `use-bundle` skill
- [x] 1. Check: passes on the real skill and fails on four planted faults; archive lists the skill; no provider file
- [x] 2. `author-concept` skill; `scripts/link_skills.py`, `poe link-skills`; `../testing/skill-evals.md`
- [x] 2. Check: every command in both skills exists; scratch library follows the author sequence and validates; adapter idempotent, refuses a foreign folder, `git status` clean
- [x] 3. `AGENTS.md` library-facing below the template-only markers
- [x] 3. Check: instantiated `AGENTS.md` has no template text or placeholder; its commands exist; `CLAUDE.md` still loads it
- [ ] PR 1 closed: agent h ___, owner h ___

## PR 2: site (`tooling/p3-site`)

- [x] PP-2 (lychee SHA-256) and PP-6 approved 2026-11-11 (text shown when written)
- [ ] **NEEDS YOU (decision):** confirm the Zensical and Material pins in review (OD-3)
- [ ] 4. `site-mkdocs` and `site-zensical` groups, lock, hashed exports, licence check on site groups, audit, lychee SHA-256
- [ ] 4. Check: clean venv from each export installs with hashes; licences zero findings or each decided (PP-8 if not); export no-op; audit clean or decided; `validate` export unchanged
- [ ] 5. `mkdocs.yml`, `build_site.py`, `check_site.py`, tasks, fixture bundle, six-check tests, Zensical expectations, divergence study, build-time record
- [ ] 5. Check: AT-FR8.1-01 and AT-FR8.2-01 to -03 pass on MkDocs; Zensical result recorded per check; one config with both key sets tested (PP-7 if not); divergences listed (PP-9 if a rule is needed); planted broken link fails strict build; time in `performance.md` (PP-11 if over 2 min)
- [ ] 6. `site.yml` (`mkdocs`, `zensical`, `deploy` jobs); `poe site-deploy-check`
- [ ] 6. Check: `check-config` passes; pinned SHA, permissions, tasks-only and Pages-only-in-deploy tests pass
- [ ] **NEEDS YOU (account, setting):** create `p3-scratch-github` (public, App installed) in `open-renewables-sandbox`; enable Pages on it
- [ ] 6. S3a: preview artifact, tag build with `release.json` naming the tag, edit and issue links, no Pages site before v1.0.0, one deploy on `v1.0.0` then Pages disabled (OD-6), Zensical result recorded
- [ ] 7. `init_library.py` rewrites `mkdocs.yml`; `git-local` strips repository links; W-10 step 4 builds the site (G25)
- [ ] 7. Check: both instantiated trees build strict; seeded leftover name fails; `git-local` has no repository link; rerun no-op; self-test within budget
- [ ] PR 2 closed: agent h ___, owner h ___

## PR 3: governance files and housekeeping (`tooling/p3-governance`)

- [ ] 8. `GOVERNANCE.md`, `README.md`, `NOTICE` review (G18)
- [ ] 8. Check: no placeholder in instantiated `GOVERNANCE.md` or `README.md`; `config.yml` link resolves; README commands exist; every path in `NOTICE` exists and every `scripts/vendor/` folder is named; licence map matches the instantiated files
- [ ] 9. `RFC-001-scope-notes.md` (Draft, no build); `.idea/` untracked and ignored (G30)
- [ ] 9. Check: RFC follows `rfcs/README.md`; `git ls-files .idea` empty; no `.idea` warning on instantiation
- [ ] **NEEDS YOU (decision):** read RFC-001 and decide before P4 (OD-4)
- [ ] PR 3 closed: agent h ___, owner h ___

## PR 4: release workflow (`tooling/p3-release`)

- [x] PP-3 and PP-4 approved 2026-11-11 (text shown when written)
- [ ] 10. `release.yml` (`gate`, `build`, `rebuild`, `publish`); `RELEASE` file in the archive; `use-bundle` and tolerance of a missing `CITATION.cff` confirmed; golden digest regenerated
- [ ] 10. Check: static tests; archive contents equal I-12 plus `RELEASE`; scripted file-tools-only navigation (NFR1); equal tar digest twice and from a scratch clone; deleted line fails the gate, restored passes (AT-FR7.4-01)
- [ ] **NEEDS YOU (setting):** immutable releases on in `p3-scratch-github` for S3b (no API call, G26)
- [ ] 11. S3b: `v0.0.1` Release with archive, checksum, manifest, notes, pre-release mark; asset edit refused; rebuild job green; missing line fails `v0.0.2` and no Release exists; restored line passes (AT-FR7.3-03)
- [ ] **NEEDS YOU (person):** choose five questions for the `use-bundle` run; optionally run the prompts on a second runtime (OD-13)
- [ ] 11. Smoke runs: `use-bundle` from the archive and `AGENTS.md` only on five questions; `author-concept` drafts a concept that validates and is labelled agent-drafted; each labelled **[Test]**, one provider; skills corrected and rerun if they miss (PP-10 if the release flow conflicts with immutability)
- [ ] PR 4 closed: agent h ___, owner h ___

## PR 5: exit (`tooling/p3-exit`)

- [ ] 12. Read the scheduled `stale-report.yml` run of 2026-11-09 (run 42629913632) and record it (G27); next scheduled run after PR 3 and PR 4 merge is green and lists the new tag in its gap check
- [ ] **NEEDS YOU (setting):** confirm `p2-w12-target` may be rewritten; disable and re-enable its ruleset during the rehearsal
- [ ] 12. Leak-removal rehearsal on `p2-w12-target`: synthetic secret merged, detected, history rewritten, force-pushed, ruleset restored (`setup_repo.py --check`); effects on `validate`, revision lines, tag and Release recorded; runbook corrected (G33)
- [ ] 13. `testing/` updated (acceptance statuses, matrix, strategy, master test plan line, known gaps: G2, G11, G18, G21, G25, G27, G30, G33 closed or narrowed; new gaps listed)
- [ ] **NEEDS YOU (account):** sandbox repositories and Apps from P2 and P3 archived or deleted
- [ ] 13. Full gate locally on 3.11 and 3.14 and in CI on three systems; coverage figure; P4 estimate proposed from actuals; `v0.5.0` tag message drafted
- [ ] PR 5 closed: agent h ___, owner h ___

## Exit

- [ ] SPEC "Done when" items 1 to 11 met, evidence in the Outcomes table
- [ ] **NEEDS YOU (decision):** owner decides immutability of releases on the template before tagging (OD-9)
- [ ] **NEEDS YOU (person):** owner pushes annotated tag `v0.5.0` (beta) on `main`; `release.yml` runs on it; "Done when" 12 ticked
- [ ] Proposed entries PP-1 to PP-6 decided and, where approved, applied; conditional PP-7 to PP-11 closed as "not needed" or decided
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p3-site-release-skills/` and re-point relative links; the SRS status is not changed

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any. Include agent and owner hours per pull request.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-2 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-3 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-4 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-5 | Approved 2026-11-11 as drafted; applied in PR 1 | SDD §6, C-04, C-08; DDR change-log row 2026-11-12 |
| PP-6 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-7 to PP-11 | Conditional: open until the step that could trigger them closes | |

## Draft: message of the annotated tag `v0.5.0`

To be drafted at step 13 from what shipped.
