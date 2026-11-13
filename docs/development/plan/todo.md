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
- [ ] **NEEDS YOU (decision):** confirm the Zensical 0.1.1 and Material 9.7.7 pins in review (OD-3)
- [x] 4. `site-mkdocs` and `site-zensical` groups, lock, hashed exports, licence check on site groups, audit, lychee SHA-256
- [x] 4. Check: clean venv from each export installs with hashes; licences zero findings or each decided (PP-8 if not); export no-op; audit clean or decided; `validate` export unchanged
- [x] 5. `mkdocs.yml`, `build_site.py`, `check_site.py`, tasks, fixture bundle, six-check tests, Zensical expectations, divergence study, build-time record
- [x] 5. Check: AT-FR8.1-01 and AT-FR8.2-01 to -03 pass on MkDocs; Zensical result recorded per check; one config with both key sets tested (PP-7 if not); divergences listed (PP-9 if a rule is needed); planted broken link fails strict build; time in `performance.md` (PP-11 if over 2 min)
- [x] 6. `site.yml` (`mkdocs`, `zensical`, `deploy` jobs); `poe site-deploy-check`
- [x] 6. Check: `check-config` passes; pinned SHA, permissions, tasks-only and Pages-only-in-deploy tests pass
- [x] **NEEDS YOU (account, setting):** create `p3-scratch-github` (public, App installed) in `open-renewables-sandbox`; enable Pages on it
- [x] 6. S3a: preview artifact, tag build with `release.json` naming the tag, edit and issue links, no Pages site before v1.0.0, one deploy on `v1.0.0` then Pages disabled (OD-6), Zensical result recorded (done 2026-11-13 in `open-renewables-sandbox/p3-scratch-github`; see Outcomes)
- [x] 7. `init_library.py` rewrites `mkdocs.yml`; `git-local` strips repository links; W-10 step 4 builds the site (G25)
- [x] 7. Check: both instantiated trees build strict; seeded leftover name fails; `git-local` has no repository link; rerun no-op; self-test within budget
- [x] PR 2 closed: agent about 9 h, owner about 1 h (App install, repo creation, review; PR merged as #40)

## PR 3: governance files and housekeeping (`tooling/p3-governance`)

- [x] 8. `GOVERNANCE.md`, `README.md`, `NOTICE` review (G18)
- [x] 8. Check: no placeholder in instantiated `GOVERNANCE.md` or `README.md`; `config.yml` link resolves; README commands exist; every path in `NOTICE` exists and every `scripts/vendor/` folder is named; licence map matches the instantiated files
- [x] 9. `RFC-001-scope-notes.md` (Draft, no build); `.idea/` untracked and ignored (G30)
- [x] 9. Check: RFC follows `rfcs/README.md`; `git ls-files .idea` empty; no `.idea` warning on instantiation
- [ ] **NEEDS YOU (decision):** read RFC-001 and decide before P4 (OD-4)
- [ ] PR 3 closed: agent h ___, owner h ___

## PR 4: release workflow (`tooling/p3-release`)

- [x] PP-3 and PP-4 approved 2026-11-11 (text shown when written)
- [x] 10. `release.yml` (`gate`, `build`, `rebuild`, `publish`); `RELEASE` file in the archive; `use-bundle` and tolerance of a missing `CITATION.cff` confirmed; golden digest regenerated
- [x] 10. Check: static tests; archive contents equal I-12 plus `RELEASE`; scripted file-tools-only navigation (NFR1); equal tar digest twice and from a scratch clone; deleted line fails the gate, restored passes (AT-FR7.4-01)
- [x] **NEEDS YOU (setting):** immutable releases on in `p3-scratch-github` for S3b (no API call, G26)
- [x] 11. S3b: `v0.0.1` Release with archive, checksum, manifest, notes, pre-release mark; asset edit refused; rebuild job green; missing line fails `v0.0.2` and no Release exists; restored line passes (AT-FR7.3-03)
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
| 1 to 3 | PR 1 merged as #39. `check_skills.py` (`poe check-skills`, in `poe check`): six frontmatter fields only, name equals folder, size, links and scripts exist, and no declared type, `uid` prefix or tag namespace in a skill or `AGENTS.md`. `use-bundle` and `author-concept` written; `link_skills.py` (`poe link-skills`) copies into the git-ignored `.claude/skills/`; library-facing `AGENTS.md` (63 lines); `skill-evals.md`. PP-5 applied to SDD §6, C-04, C-08 and the DDR log. `poe test` 727 passed, coverage 98.18 %. Directory-link test skips on Windows; smoke runs are step 11. `AGENTS.md` names `GOVERNANCE.md`, which arrives in PR 3 (G18). Agent about 5 h; owner not logged | [Test] | PP-5 applied |
| 4 to 7 | PR 2 merged as #40. Step 4: groups `site-mkdocs` (mkdocs 1.6.1, mkdocs-material 9.7.7) and `site-zensical` (zensical **0.1.1**, the latest on 2026-11-12, not the 0.0.x of ADR-001), hash-locked exports covered by `poe export` and its check; clean venvs from each export install with `--require-hashes` on Python 3.11 and 3.14; `poe licences` over 62 packages found three metadata cases (`ghp-import`, `jinja2`, `mergedeep`), so **PP-8 fired: ADR-009 (Proposed)** with three resolution rows in `constraints.md`, to be approved; `poe audit` clean over all groups; lychee asset SHA-256 filled (PP-2; the release digest and its `.sha256` asset agree). Steps 5 and 6: `mkdocs.yml` (I-13 baseline); `build_site.py` and `check_site.py` with tasks `docs`, `docs-build`, `docs-zensical`, `docs-linkcheck`, `docs-manifest`, `site-deploy-check`; a fixture bundle and the six FR8.2 checks. **MkDocs and Zensical 0.1.1 both pass all six on the fixture**, with identical pages and HTML on every compared construct; the `/`-rooted-link failure of V-03 is gone with ADR-005. Zensical 0.1.1 reads MkDocs' `validation` and `strict` keys and fails a strict build on a broken link; strict MkDocs rejects Zensical-only keys, so one `mkdocs.yml` works without them (ADR-001's carried issue answered; PP-7 not needed). Site build of 604 concepts: MkDocs 7.7 s, Zensical 4.3 s on this machine (target 120 s; PP-11 not needed). G2 study: two divergences (D1 a list directly after a paragraph, D2 a list inside a footnote definition; `testing/site-divergences.md`); **PP-9 fires** (proposed, nothing built). `site.yml` has jobs `mkdocs`, `zensical` (non-blocking, pinned lychee) and `deploy` (only a stable v1+ tag with `library.site_url`); template-tests install all groups so the site tests and licence check cover the site stack. Step 7: `init_library` rewrites `mkdocs.yml` (name, repository and issue links; repository keys stripped for `git-local`); both instantiated trees build strict (G25). S3a rehearsal ran: see the next row | [Test] | PP-2 and PP-6 (mkdocs part) applied; PP-8 and PP-9 fired; ADR-009 and PP-9 await the owner |
| 6 (S3a) | Rehearsed 2026-11-13 in `open-renewables-sandbox/p3-scratch-github` (public, App `okf-sandbox-revision-bot`): an instantiated library pushed, `setup_repo --promote` applied, a PR gave a preview artifact (`mkdocs` and `zensical` green, `deploy` skipped); tag `v0.0.1` wrote `release.json` naming the tag and commit, had the edit and issue links and did not deploy; with `library.site_url` set, tag `v1.0.0` deployed once, `release.json` live, then Pages disabled. Found: **(1)** enabling Pages leaves the `github-pages` environment open to `main` only, so the tag deploy was refused; `setup_repo --promote` now adds the `v*` tag policy (**PP-12**, approved and applied in PR 2); **(2)** `audit` fails in every instantiated library because it reads `docs/development/constraints.md`, which `init_library` removes (not fixed; known gap for PR 5); **(3)** an empty repository cannot enable CodeQL (promote after the first push). Sandbox left with a `main-protect` ruleset without the `validate` requirement | [Test] | PP-12 applied |
| 8 and 9 | PR 3 built on `tooling/p3-governance`. `GOVERNANCE.md` (roles, one approval, definition of stable, self-approval and `require_non_author_approver`, contribution routes and labels, decisions, releases and what makes a major, staleness and deprecation, security reporting) with `{maintainer}` and `{contact}` filled by `init_library` (PP-6 applied to SDD W-01 step 3; G18 closed in code); template `README.md` rewritten (no "P0" or "planned"; three routes, commands, skills, site, releases, licence map); `NOTICE` reviewed, unchanged (nothing vendored in P3), now tested against the vendored folders; `RFC-001-scope-notes.md` (Draft; recommends an optional profile-declared scope-note type; builds nothing); `.idea/` untracked and ignored, and skipped by the leftover scan (G30). Tests: `test_governance.py` and four instantiated-library tests; `poe check` clean | [Test] | PP-6 applied |
| 10 and S3b | PR 4 built on `tooling/p3-release`. `release.yml`: `gate` (`poe release-gate`: `release.py --from-tag`), `build` (`poe bundle`, `poe bundle-verify`), `rebuild` (clean checkout, `poe bundle-rebuild`), `publish` (only job with `contents: write`; draft, attach, publish; pre-release for v0 or a suffix). Two bugs fixed: `release.py` refused an existing tag, and the gate used the tag itself as the previous release. Archive gains a generated `RELEASE` file (library, tag, commit, commit date); `use-bundle` included, `author-concept` not, missing `CITATION.cff` tolerated; golden digest is tar-level and unchanged. NFR1 scripted navigation and AT-FR7.4-01 pass in tests. SDD I-12, W-07, C-10, W-08 and a DDR row apply PP-3 and PP-4. **S3b live, 2026-11-14, immutable releases on:** `v0.0.3` published as a pre-release with archive, `.sha256`, manifest and notes; `sha256sum -c` OK and the tar digest equals the manifest; deleting an asset is refused ("Cannot delete asset from an immutable release"), deleting the whole Release is allowed (the tag stays); `v0.0.4` on a merge commit without its revision line failed `gate` with `OKF901`, other jobs skipped, no Release; `v0.0.5` on the commit with the line passed all four jobs and published. PP-10 not needed. Smoke runs (step 11) not yet run | [Test] | PP-3 and PP-4 applied |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-2 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-3 | Approved 2026-11-11 as drafted; applied in PR 4 | SDD I-12, W-07, C-10, W-08; DDR change-log row 2026-11-13 |
| PP-4 | Approved 2026-11-11 as drafted; applied in PR 4 | SDD W-07, C-10; DDR change-log row 2026-11-13 |
| PP-5 | Approved 2026-11-11 as drafted; applied in PR 1 | SDD §6, C-04, C-08; DDR change-log row 2026-11-12 |
| PP-6 | Approved 2026-11-11 as drafted; applied in PR 2 (`mkdocs.yml`) and PR 3 (`GOVERNANCE.md`) | SDD W-01 step 3; DDR change-log rows 2026-11-12 and 2026-11-13 |
| PP-7 to PP-11 | Conditional: open until the step that could trigger them closes | |

## Draft: message of the annotated tag `v0.5.0`

To be drafted at step 13 from what shipped.
