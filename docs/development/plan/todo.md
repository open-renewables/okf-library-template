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
- [x] **NEEDS YOU (decision):** confirm the Zensical 0.1.1 and Material 9.7.7 pins in review (OD-3) (confirmed 2026-11-14; Zensical stays exact-pinned and moves only through a reviewed pull request)
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
- [x] **NEEDS YOU (decision):** read RFC-001 and decide before P4 (OD-4) (decided 2026-11-14: option D, ADR-010)
- [ ] PR 3 closed: agent h ___, owner h ___

## PR 4: release workflow (`tooling/p3-release`)

- [x] PP-3 and PP-4 approved 2026-11-11 (text shown when written)
- [x] 10. `release.yml` (`gate`, `build`, `rebuild`, `publish`); `RELEASE` file in the archive; `use-bundle` and tolerance of a missing `CITATION.cff` confirmed; golden digest regenerated
- [x] 10. Check: static tests; archive contents equal I-12 plus `RELEASE`; scripted file-tools-only navigation (NFR1); equal tar digest twice and from a scratch clone; deleted line fails the gate, restored passes (AT-FR7.4-01)
- [x] **NEEDS YOU (setting):** immutable releases on in `p3-scratch-github` for S3b (no API call, G26)
- [x] 11. S3b: `v0.0.1` Release with archive, checksum, manifest, notes, pre-release mark; asset edit refused; rebuild job green; missing line fails `v0.0.2` and no Release exists; restored line passes (AT-FR7.3-03)
- [x] **NEEDS YOU (person):** choose five questions for the `use-bundle` run; optionally run the prompts on a second runtime (OD-13)
- [x] 11. Smoke runs: `use-bundle` from the archive and `AGENTS.md` only on five questions; `author-concept` drafts a concept that validates and is labelled agent-drafted; each labelled **[Test]**, one provider; skills corrected and rerun if they miss (PP-10 if the release flow conflicts with immutability)
- [ ] PR 4 closed: agent h ___, owner h ___

## PR 5: exit (`tooling/p3-exit`)

- [ ] 12. Read the scheduled `stale-report.yml` run of 2026-11-09 (run 42629913632) and record it (G27); next scheduled run after PR 3 and PR 4 merge is green and lists the new tag in its gap check
- [x] **NEEDS YOU (setting):** confirm `p2-w12-target` may be rewritten; disable and re-enable its ruleset during the rehearsal
- [x] 12. Leak-removal rehearsal on `p2-w12-target`: synthetic secret merged, detected, history rewritten, force-pushed, ruleset restored (`setup_repo.py --check`); effects on `validate`, revision lines, tag and Release recorded; runbook corrected (G33)
- [ ] 13. `testing/` updated (acceptance statuses, matrix, strategy, master test plan line, known gaps: G2, G11, G18, G21, G25, G27, G30, G33 closed or narrowed; new gaps listed)
- [ ] **NEEDS YOU (account):** sandbox repositories and Apps from P2 and P3 archived or deleted (decided 2026-11-14: after `v0.5.0` is verified, archive `p3-scratch-github` and `p0-spikes`, delete the App's private key and uninstall it; the P2 repositories are already gone)
- [x] 13. Full gate locally on 3.11 and 3.14 and in CI on three systems; coverage figure; P4 estimate proposed from actuals; `v0.5.0` tag message drafted (gate: 799 passed on each Python before the generator work, 808 after; estimate and tag message below)
- [x] 14. Site generator choice (with `poe site-switch`, added 2026-11-15): profile key `site.generator`; `init_library` question and answers key; tasks and `site.yml` follow the profile (MkDocs default); ADR-011; README; SDD wording (PP-14)
- [x] 14. Check: key tests (default, both values, invalid refused); self-test builds the site strict for each generator on both platforms; workflow tests; `poe check` and `poe test` pass; live sandbox run with `zensical` chosen
- [ ] PR 5 closed: agent h ___, owner h ___

## Exit

- [ ] SPEC "Done when" items 1 to 12 met, evidence in the Outcomes table
- [x] **NEEDS YOU (decision):** owner decides immutability of releases on the template before tagging (OD-9) (decided 2026-11-14: off for v0.5.0, on before v1.0.0)
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
| 12 (a) and 13 (part) | Scheduled run 42629913632 of 2026-11-09 (Monday 13:56 UTC): success; `stale_report.py --check-since v0.2.0` printed `0 stale, 0 with no revision, 0 change(s) without a line`; `poe audit` found none; it created issue #37 "Review report" (open). Later scheduled run: Monday 2026-11-16, not yet. `testing/` updated: acceptance statuses (FR7.3-03, FR8.3, FR8.5 and FR7.4 cases ready or passed), `strategy.md` "What P3 adds", traceability row for G37 to G40, known gaps G2, G11, G18, G21, G25, G27 and G30 closed or narrowed, new gaps G37 audit fails in instantiated libraries, G38 one provider, G39 whole immutable Release can be deleted, G40 template not yet released | [Test] | |
| 12 (b) | Leak-removal rehearsal run 2026-11-14 on `p3-scratch-github` (`p2-w12-target` and `p2-scratch-github` no longer exist in the sandbox organisation). A labelled fake (`profile/deploy-notes.txt`: a marker and a generic key) was merged by pull request; `scan.py` flagged the marker on the pull request and on `main` (`scan` job red), and the gitleaks step after it did not run; tag `v0.0.6` on the leak published an immutable Release whose archive held the file (rebuilt and confirmed); the Release was deleted (allowed, tag kept); `git filter-repo --invert-paths` on a mirror clone changed every commit id and all six tags, because GitHub's signed web merges lose their signature, and left `v0.0.5` and `v0.0.6` on one commit. The force-push to the protected `main`, the tag pushes and `validate` after the rewrite were **not run**: the auto-mode classifier refused to disable the ruleset and force-push. **Owner decision 2026-11-14: skip them and close G33**; the runbook records what was seen and what stays untested | [Test] (partial) | |
| 13 (gate) | Full gate on 2026-11-14 with a clean environment per Python: `poe check` clean and `poe test` 799 passed, 4 skipped, coverage 98.18 % on 3.11 and 98.19 % on 3.14. CI on three systems is the `template-tests` matrix on each pull request | [Test] | |
| 11 (smoke) | 2026-11-14, one provider, fresh subagent per skill, scratch library `p3-scratch-github`. `use-bundle` from the unpacked `v0.0.5` archive and `AGENTS.md` only, on five owner-approved questions: all answers matched the files; indexes read one level at a time, section by heading, tags from `vocab/`, status and tier as written, out-of-scope answered "not covered", `<uid>@v0.0.5` cited from `RELEASE`. `author-concept` in a clone drafted ITM-0002; validate 0 errors, `poe check` and `poe test` pass; the pull request carries `agent-drafted`. Four unclear points in the skill corrected (registry file in the commit, optional section placeholder, description in the commit body, label versus trailer). Details in `testing/skill-evals.md` | [Test], one provider (G38) | |
| Owner decisions | 2026-11-14 Q&A: **ADR-009 approved** as drafted (Accepted). **PP-9:** an authoring rule now (SDD I-01, `AGENTS.md`, `author-concept`); a warning kind is reconsidered in P4 on real content. **RFC-001:** the owner chose none of A, B or C as written but "C combined with a YAML header in the `index.md` file": no scope-note type, a `description` in a YAML header on each folder's `index.md`, kept by the generator; recorded as option D in RFC-001 (Accepted) and **ADR-010**; built in P4 (about 2 to 3 agent hours); it needs the SRS FR4.3 wording and SDD I-07 and I-02 text, proposed as PP-13. **OD-9:** immutable releases off for `v0.5.0`, on before `v1.0.0` | | |
| 14 | Site generator choice, requested 2026-11-14 (plan step 14, PP-14, ADR-011). Profile key `site.generator` (`mkdocs` default, `zensical`; schema, loader `Profile.site_generator`, optional); `init_library` asks for it (answers key `site_generator`) and writes it, the README names it; `build_site.py` takes `primary` (default), `alt`, `--serve`, `--print-generator`; tasks `docs`, `docs-build` use the library's generator, `docs-zensical` becomes `docs-alt` (output `site-alt/`), new `site-generator`; `site.yml` jobs `primary` (installs only the chosen group, blocking) and `alternate` (non-blocking, both groups, lychee). Tests: generator resolution, default outputs, invalid value refused, command line, serve needs the group, questionnaire and answers, workflow rules, and the W-10 self-test instantiates MkDocs on `github` and Zensical on `git-local` and builds each site strict. `poe check` clean; 808 passed, 4 skipped, coverage 98.15 %. **Live, 2026-11-14, sandbox PR #12:** with `site.generator: zensical` the `primary` job installed `site-zensical` and built with Zensical, `alternate` built MkDocs and compared pages, both green, `deploy` skipped. ADR-011 (Accepted) amends ADR-001 and AD-13; SDD §1, C-07, I-02, I-16, W-01, W-08 and a DDR row apply PP-14. Default stays MkDocs; revisit before v1.0.0 | [Test] | PP-14 applied |
| G37 | Fixed 2026-11-15 at the owner's request, before the `v0.5.0` tag: `audit.py` reads `constraints.md` where it exists, else `profile/audit-ignore.txt` (advisory IDs; none means no exceptions); `test_supply.py` covers both and the W-10 self-test runs `audit_command` and `audit.py --print-command` in each instantiated library. The scratch library's `audit` job had failed on the missing file in S3a. Stale-report issue #37 (the 2026-11-09 run) read and recorded in step 12 | [Test] | |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Approved 2026-11-11 as drafted; applied in PR 5 | SDD §1 and §14 (P3 actuals); DDR change-log row 2026-11-14 |
| PP-2 | Approved 2026-11-11 as drafted; applied when its step lands | |
| PP-3 | Approved 2026-11-11 as drafted; applied in PR 4 | SDD I-12, W-07, C-10, W-08; DDR change-log row 2026-11-13 |
| PP-4 | Approved 2026-11-11 as drafted; applied in PR 4 | SDD W-07, C-10; DDR change-log row 2026-11-13 |
| PP-5 | Approved 2026-11-11 as drafted; applied in PR 1 | SDD §6, C-04, C-08; DDR change-log row 2026-11-12 |
| PP-6 | Approved 2026-11-11 as drafted; applied in PR 2 (`mkdocs.yml`) and PR 3 (`GOVERNANCE.md`) | SDD W-01 step 3; DDR change-log rows 2026-11-12 and 2026-11-13 |
| PP-7 | Not needed: strict MkDocs rejects Zensical-only keys and Zensical reads MkDocs' keys, so one `mkdocs.yml` works | Step 5 outcome |
| PP-8 | Fired in step 4; ADR-009 approved 2026-11-14 | ADR-009 (Accepted); three rows in `constraints.md` |
| PP-9 | Fired in step 5; decided 2026-11-14: an authoring rule now, a warning kind reconsidered in P4 | SDD I-01 bullet; `AGENTS.md`; `author-concept`; G2 |
| PP-10 | Not needed: the draft-then-publish flow and `gh release create` work with immutable releases | S3b |
| PP-11 | Not needed: 604 concepts build in 7.7 s (MkDocs) and 4.3 s (Zensical) | `performance.md` |
| PP-12 | Approved and applied 2026-11-13 | SDD W-11 step 3; runbook; DDR row |
| PP-15 | Approved 2026-11-14 and applied in PR 5: the P4 estimate (agent 26–37 h, owner 9–10 h, 6–9 days) | SDD §14 P4 row; DDR change-log row 2026-11-14 |
| PP-14 | Added 2026-11-14 at the owner's request; approved with it and applied in PR 5 | ADR-011; SDD §1, C-07, I-02, I-16, W-01, W-08; DDR change-log row |
| PP-13 | Approved 2026-11-14, **applied when P4 builds the index header** (ADR-010): SRS FR4.3 wording (yours), SDD I-07 and I-02 text, `author-concept` guidance | P4 |

## Draft: message of the annotated tag `v0.5.0`

## Proposed P4 estimate (from P3 actuals, 2026-11-14)

**P3 actuals [Inf]** (not time-logged; reconstructed from pull requests and sessions): agent about 36 hours (plan 0 about 4, PR 1 about 5, PR 2 about 9, PR 3 about 3, PR 4 about 5, PR 5 about 10 including both rehearsals, the smoke runs and the generator choice added on 2026-11-14), owner about 7 hours (the Q&As, the sandbox repository, App and immutability settings, the merges and reviews), and 4 calendar days from the plan merge (2026-11-11) to the last pull request. Plan was 32–50 agent hours, 7–11 owner hours and 5–8 days, so P3 landed inside it, as P2 did (54 against 53–83).

**P4 estimate [Inf]**, same units and the same assumptions as the P3 plan (one pull request per sitting, review within a working day, no second runtime):

| Item | Agent (h) | Owner (h) | Owner content |
| --- | --- | --- | --- |
| Instantiate the pilot, run the W-01 sheet, platform steps | 2 | 1.5 | Create the repository, App and settings; brief a second person |
| Index scope-note header (ADR-010): `build_indexes.py`, check 5, fixtures, golden files; SRS FR4.3 and SDD I-07, I-02 wording (PP-13) | 3 | 0.5 | Approve PP-13 |
| About 20 concepts with scope notes, vocabulary values and glossary entries, drafted with `author-concept` | 8–12 | 3–4 | Review each concept; mark the whole-concept reviews `full-review` |
| Traced agent run from the archive (FR7.2) and the Master Test Plan run (AT cases) | 6–9 | 1.5 | Choose questions; read the trace |
| G37 (`audit` in instantiated libraries) and the PP-9 warning decision, built if chosen | 2–4 | 0.5 | Decide |
| W-12 rehearsal on the pilot (carried) | 2–3 | 0.5 | Confirm the move |
| Hardening for v1.0.0: default generator, immutable releases on, release notes, the v1.0.0 gate, tag | 3–4 | 1.5 | Decide, tag |
| **Total** | **26–37** | **9–10** | |

Calendar time 6–9 days. Against the SDD §14 P4 row (5–8 person-days, owner about 6 hours) the agent effort is in range; the owner figure is higher because 20 concepts need a human review for the tier to mean anything. The largest uncertainty is the concept authoring (volume and review rounds), as the P1 core build was in P1. Proposed as PP-15 for the SDD §14 P4 row; not applied until the owner approves.

## Draft: message of the annotated tag `v0.5.0`

To be pushed by the owner as an annotated tag on `main` after the last P3 pull request merges. Edit the counts to the final run before tagging.

```
okf-library-template v0.5.0 (beta)

A template for building validated, agent-ready knowledge libraries on the
Open Knowledge Format (OKF) v0.2. Beta: build phases P0 to P3 are done and
rehearsed; the pilot library (P4) and v1.0.0 follow. Not for citing as stable.

What is in it
- Profile tooling (okfprofile): six validation checks, generated indexes,
  uid registry, revision history and trust tiers, base-branch validation
- init_library for platform github and git-local; setup_repo; an instantiation
  self-test that builds each library and its site
- CI: validate, revision writer, stale report, site (MkDocs or Zensical, chosen
  at init, switchable later with poe site-switch; MkDocs is the default),
  release (gate, build, rebuild, publish)
- Agent skills use-bundle and author-concept, AGENTS.md, GOVERNANCE.md, runbooks

How it was checked
- uv run poe check and poe test on Python 3.11 and 3.14: 821 tests,
  coverage 98.1 %; CI on Linux, macOS and Windows
- Live rehearsals in sandbox libraries: release from a tag (immutable
  pre-release, gate refuses a missing revision line), Pages deploy from v1.0.0
  with a site URL, a Zensical-primary site build, a leak removal up to the
  force-push, two agent smoke runs (one provider)

Known gaps (docs/development/testing/known-gaps.md)
- G38 the skills were tried on one provider; G39 a whole immutable Release can
  still be deleted; G40 this is the template's first release.yml run
- Scope notes (ADR-010), a warning for the two Python-Markdown divergences
  (PP-9) and the pilot are P4

Verify a download: sha256sum -c <archive>.sha256; the RELEASE file inside the
archive names this tag and its commit. This release is a pre-release; its
assets are not yet immutable (immutable releases are switched on before v1.0.0).
```
