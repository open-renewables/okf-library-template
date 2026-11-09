# Todo: build phase P2

Checklist for `plan.md`; scope and done-when in `SPEC.md`. Tick an item when its check in `plan.md` has passed and the evidence (command and result) is noted in the Outcomes table. **NEEDS YOU** marks a decision, person, account, machine or setting from the owner. Nothing is committed, pushed or merged without the owner's instruction. When a pull request closes, note its agent time and owner time in the Outcomes table (plan, rule 9).

## Before any step

- [x] Owner reviews `SPEC.md`, `plan.md` and `todo.md` (approved 2026-11-03)
- [x] **NEEDS YOU (decision):** owner answers OD-1 to OD-12 or accepts the defaults (defaults accepted 2026-11-03; OD-12 login still to supply) (`plan.md`, "Open decisions"); OD-1 to OD-4, OD-9 to OD-11 and PP-2 answered 2026-11-03
- [x] **NEEDS YOU (decision):** owner approves or rejects PP-1 to PP-9 (approved as drafted 2026-11-03; text shown for review when each is written) (`plan.md`, "Proposed entries")
- [x] **NEEDS YOU (decision):** owner confirms the effort basis and units in `plan.md` "Effort"

## S1: V-05 closure (sandbox, `open-renewables-sandbox/p0-spikes`)

- [x] **NEEDS YOU (account, setting):** sandbox GitHub App created, installed, client ID and key stored, on `main` ruleset bypass "always"; no second account (OD-2 decided)
- [x] 1. Run sheet and scripts written (explicit `--repo` on every `gh` call, synthetic content)
- [x] 1. 5a App "always" bypass proven; `GITHUB_TOKEN` refused
- [x] 1. 5c approval, stale approval, review `commit_id`, `merged_by`, commit-to-PR lookup and lag recorded
- [x] 1. Check: result labelled **[Test]**; fixtures committed later in PR 2; contradictions raised as PP-6 before step 5

## PR 1: supply chain and scan (`tooling/p2-supply-chain`)

- [x] 2. `requirements/validate.txt` hash-locked export and drift check; `poe export`, `poe audit`, `poe licences`; pinned tool versions (PP-2, OD-7)
- [x] 2. Check: clean venv from the hashed file runs the validate tests; licence check fails on a GPL and an unrecorded MPL-2.0 package; export is a no-op on an unchanged lock
- [x] 3. `scan.py`, `profile/scan.yaml` and meta-schema (PP-4), pre-commit hook, gitleaks hook if installed, `poe scan`
- [x] 3. Check: planted marker and planted secret-shaped string fail; hook refuses in Git Bash and PowerShell; hook skips with a notice without gitleaks

## PR 2: adapters and revision writer (`tooling/p2-adapters-revision`)

- [x] 4. `okfprofile.platforms`: data model, `github` (standard library REST, retries), `git_local` (trailers, `maintainers`), event-to-`ChangeContext` helper; step 1 fixtures committed
- [x] 4. Check: replay tests for every approval case; lagging lookup retried then resolved by subject; `PR none`; unknown author recorded as non-owner; no core module imports an adapter

- [x] 5. `write_revision.py` with catch-up, inference, insertion, indexes, optional `verified`, `--check-since`; `OKF9xx` codes in the catalogue (PP-3); `poe revision`
- [x] 5. Check: golden lines for every I-08 row and two concepts in one PR; dropped run recovered; second run no-op; hand-edited and deleted lines caught on `main`; `verified` agrees with an OKF reading; failing fixture per `OKF9xx`; `git_local` gives the same lines

## PR 3: stale report and intake files (`tooling/p2-intake`)

- [x] 6. `stale_report.py`, `poe stale`
- [x] 6. Check: fixtures past each limit listed; offset-less `stale_after` rejected; no-revision concept reported Unverified
- [x] **NEEDS YOU (decision):** GitHub login(s) for CODEOWNERS and `maintainers` (OD-12): `richard-gledhill` taken from the owner's `gh` account and merge history; owner to confirm in the PR review
- [x] 7. CODEOWNERS, PR template, three issue forms and `config.yml`, `dependabot.yml`, label list, `poe check-config`
- [x] 7. Check: config check passes and fails on a planted bad form; forms name only listed labels; two-folder path resolves to two owners

## PR 4: bundle and release (`tooling/p2-release`)

- [x] 8. `build_bundle.py` (reproducible, ADR-004), `release.py`, `poe bundle`, `poe release` (PP-5)
- [x] 8. Check: equal tar digest on two builds and from a tag in a scratch clone; missing revision line fails release; checksum verifies; golden digest stored for the matrix

## PR 5: instantiation (`tooling/p2-instantiate`)

- [x] 9. `init_library.py` (questionnaire, `--answers`, licences, template-only removal, idempotent)
- [x] 9. Check: no placeholder, template-only file or `docs/` left; licence files, Apache 2.0 text and `NOTICE` present; rerun is a no-op; result validates
- [x] 10. `setup_repo.py` with `--dry-run`, `--check`, `--promote`; `runbook-promote-library.md`
- [x] 10. Check: dry run against recorded responses lists exactly the needed changes; sandbox run sets everything and a second run changes nothing; deleted label and setting restored; `--promote` reaches the W-11 end state
- [x] 11. `tests/template/instantiation/`, W-10 self-test, `poe selftest`
- [x] 11. Check: both modes pass; seeded leftover placeholder and template-only file fail; `git-local` run makes no platform call; rebuilt archive digest matches

## S2: sandbox rehearsal of workflows

- [ ] Scratch sandbox repository with ruleset and App; step 12 and 14 drafts run on every trigger

## PR 6: CI, security jobs and revision CI (`tooling/p2-ci`)

- [ ] **NEEDS YOU (decision):** confirm current hosted-runner minute multipliers for private repositories before the matrix is fixed (OD-3, PP-8)
- [x] 12. `validate.yml`, `template-tests.yml`, gitleaks job, pip-audit, licence check, hooks on three systems, speed gate, `check-config`; actions pinned by SHA (written; not yet run on GitHub)
- [ ] 12. Check: local and CI findings equal (FR2.8); FR2.5, FR2.6, FR1.5, FR1.6 and FR2.4 scenarios in the sandbox; planted secret and marker caught (NFR6); six matrix jobs and three hook jobs green (G1, G10); digest equal on three systems (V-12); speed gate result recorded (G8); pinned-SHA test passes
- [ ] **NEEDS YOU (setting):** after `validate` is green on `main`, add it as a required check on the `open-renewables/okf-library-template` ruleset (step 13)
- [ ] 13. Check: throwaway mixed pull request fails and is not mergeable; next normal pull request shows the check as required; runbook click path updated

- [ ] **NEEDS YOU (account, setting):** organisation App created and installed on the template repository only; client ID variable, private key secret, ruleset bypass "always"
- [x] 14. `revision.yml`, `stale-report.yml`, `runbook-revision-writer-recovery.md` (written; not yet run on GitHub)
- [ ] 14. Check: sandbox: one bot commit, no retrigger, dropped run recovered, bot commit passes `validate`, weekly issue created then updated; `setup_repo.py --check` passes; template: first knowledge-touching PR produces a bot commit and `main` stays green

## PR 7: rehearsals and exit (`tooling/p2-exit`)

- [x] **NEEDS YOU (account):** three synthetic repositories in `open-renewables-sandbox` (OD-11) (done 2026-11-09; the App is installed on all three)
- [x] 15. GitHub scratch library: each approval case live, dropped run, duplicate `uid` (sandbox `p2-scratch-github`; the two cases that need a second account are fixtures, G35)
- [x] 15. `git-local` scratch library: same cases from local commits and trailers; `poe release`
- [x] 15. W-12 rehearsal and `runbook-move-git-local-to-platform.md`; `runbook-remove-leaked-content.md` (was named `runbook-leak-removal.md`; the promote runbook already linked the longer name); `runbook-instantiate-library.md` run sheet
- [x] V-06 carry to P4 recorded (OD-10 decided, PP-9); run sheet for the P4 timing written (the timing table is in `runbook-instantiate-library.md`)
- [x] 15. Check: golden line per case; commit identifiers and lines unchanged after W-12 and archives match; runbooks name only existing commands (`test_runbooks.py`)
- [x] 16. Full gate locally and in CI; `testing/` updated; P3 and P4 estimate proposed from actuals; `v0.2.0` tag message drafted (below)
- [ ] Sandbox repositories and Apps cleaned up or archived (OD-11)

## Exit

- [ ] SPEC "Done when" items 1 to 11 met, evidence in the Outcomes table
- [ ] **NEEDS YOU (person):** owner pushes annotated tag `v0.2.0` (alpha) on `main` (OD-9)
- [x] Proposed entries PP-1 to PP-11 decided and, where approved, applied (2026-11-09)
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p2-ci-governance/` and re-point relative links; the SRS status is not changed

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any. Include agent and owner hours per pull request.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |
| 1 | 5a: App push to protected `main` accepted by the "always" bypass, `GITHUB_TOKEN` push refused (GH013). 5c: a stale approval keeps `commit_id` of the approved head and still satisfies the rule; an unapproved owner merge is `blocked` and passes by the Admin bypass, `merged_by` = author. Lookup: closed-list and subject hit at the first poll (about 4 s), `commits/{sha}/pulls` up to 8.4 s. Org policy refuses "Actions can approve pull requests", so the owner opened the PRs and the App approved. Findings: `persist-credentials: false` for `revision.yml`; bot commits have no author login (use the trailer); client ID needs capital `I`. No contradiction with AD-11, AD-12, W-05, SDD §11. Notes: `side-session-notes/.../p2-s1-result.md` | [Test] | none (PP-6 not triggered) |
| 2 to 3 | PR 1 built and merged as #20. `requirements/validate.txt` and `dev.txt` exported from `uv.lock` with hashes (`poe export`; `export_requirements.py --check` is a `poe check` step); a clean venv from each with `--require-hashes` validates the bundle and passes `tests/library`. `poe licences`: 36 locked packages checked, 0 findings (allowlist, ADR-006/007 exceptions and metadata resolutions parsed from `constraints.md`). `poe audit`: 0 findings. gitleaks v8.30.1 and its `linux_x64` SHA-256, and lychee-v0.24.2, filled in `constraints.md` (PP-2). `scan.py` with `profile/scan.yaml` and its meta-schema (PP-4); hook refuses a planted marker (Git Bash) and a planted secret (PowerShell, redacted) and passes clean commits; gitleaks hook skips with a notice when not installed. `poe check` clean, `poe test` 403 passed, coverage 98.77 %. New gaps G11 to G13 | [Test] | PP-2, PP-4 applied |
| 4 | PR 2 built, uncommitted on `tooling/p2-adapters-revision`. `okfprofile.platforms`: data model, `commits` (first-parent history, trailers, UTC dates), `github` (standard-library REST behind an injectable transport; lookup order closed list, `(#n)` subject, `commits/{sha}/pulls`; 30 s retry budget only for a commit whose subject names a PR) and `git_local` (maintainers map, `Approved-by`, `Full-Review`, `Agent-Drafted`). Replayed from responses recorded in the sandbox (`tests/template/fixtures/github/`, 48 KB). Found by the tests: a 404 on the closed list must not stop the lookup; bot logins need `[bot]` stripped to fit the grammar. `git-local` takes the author as the merger (G16) | [Test] | none |
| 5 | `write_revision.py` (`poe revision`): catch-up since the last `Revision-Bot` commit or `--since`, W-05 inference per concept file (14 table rows), line insertion before footnotes with CRLF kept, indexes refreshed, optional `verified` (G15), `--commit` with the trailer, `--check-since` raising `OKF901` (PP-3: code, catalogue row, unit test). Scratch-repository tests: order, second run no-op, dropped run recovered, dry run, `validate_main` clean afterwards. A read-only dry run against the real template history resolved PR #16 live (four lines, `self-approved (non-owner)` because CODEOWNERS arrives in PR 3). 469 tests pass, coverage 98.3 %. New gaps G14 to G16; G4 and G9 narrowed | [Test] | PP-3 applied |
| 6 to 7 | PR 3 built, uncommitted on `tooling/p2-intake`. `stale_report.py` (`poe stale`): earlier of `stale_after` and the default interval after the latest revision line; ISO durations of years, months, weeks and days with calendar clamping; offset-less or unreadable `stale_after` ignored; a concept with no revision is listed as unverified, and is stale only by its own date; deprecated concepts left out (to confirm); Markdown body for one issue (marker line), JSON, `--check-since` adds the OKF901 list; exit 0 whatever it finds. `.github/`: CODEOWNERS, `labels.yml` (9 labels), PR template, three issue forms, `config.yml`, `dependabot.yml` (actions, uv). `poe check-config` (uvx check-jsonschema, built-in schemas) passes on all files and fails on a planted bad form (run by hand, G17). Found by the tests: label colour `5319e7` reads as a number in YAML 1.2, so colours are quoted. `poe check` clean, new tests pass | [Test] | none |
| 8 | PR 4 built, uncommitted on `tooling/p2-release`. `build_bundle.py` (`poe bundle <tag>`): files read from git at a commit (one `git cat-file --batch`), sorted by path, mode 0644/0755, owner 0 with empty names, mtime = commit time, GNU tar, gzip with no name or timestamp; checksum in `sha256sum` format; manifest (tag, commit, profile and OKF versions, platform, counts by type, status and tier, tar and `.tar.gz` digests, Python and zlib versions). `--verify` compares the tar digest, and the `.tar.gz` digest only for the same Python and zlib (ADR-004); `--rebuild-check` rebuilds from a ref. `release.py` (`poe release <tag>`): semver tag, clean tree, new tag, revision-line gate from the previous release (FR7.4), validation, archive into `dist/`, annotated tag whose message records the tar digest (`git-local`); `github` mode checks only; `--dry-run`, `--sign`. Tests: golden tar digest of fixed content (the V-12 anchor for the PR 6 matrix), rebuild from a clone at the tag reproduces the digest, a missing line fails a release and leaves no tag. New gaps G19 to G22 | [Test] | none |
| 9 to 11 | PR 5 built, uncommitted on `tooling/p2-instantiate`. `init_library.py` (`poe init`): answers file or questionnaire; rewrites profile (name, platform, maintainers, `revision_token: github-token`), project name and licence in `pyproject.toml` and `uv.lock` (the lock still passes `uv lock --locked`), `LICENSE` (Apache kept, MIT written, or a proprietary notice), `LICENSE-template`, `LICENSE-content`, README, CITATION.cff, `DECISIONS.md` DR-01, CODEOWNERS, the issue-chooser link; removes `CLAUDE.md`, `docs/`, `tests/template/` (and the coverage gate with it) and, for `git-local`, the platform files; indexes regenerated; rerun changes nothing; leftover template names are reported. `setup_repo.py` (`poe setup-repo`): merge methods, read-only workflow token, dependency alerts, labels from `labels.yml`, `main-protect` ruleset (App bypass, `validate` check once the workflow exists), secret scanning, `--dry-run`, `--check` (including the client-ID capital `I` from S1), `--promote`; compares with the live state first, so a rerun restores deletions; tested against an in-memory GitHub. W-10 self-test: both platforms, 17 checks, library tests pass without the template tests, `git-local` release with every platform call forbidden. `runbook-promote-to-public.md` written. Found by the tests: the root index carries the library title, so indexes must be rebuilt at instantiation. New gaps G23 to G26; live `setup_repo` run on the sandbox repositories still to do | [Test] | PP-10 |
| 12 to 13 | PR 6 built, uncommitted on `tooling/p2-ci`; checks 12 and 13 wait for the sandbox rehearsal and the owner's setting. `ci_validate.py` (`poe ci-validate-event`): a pull request is validated with the base branch's tooling plus its labels (`approved-move`, `profile-migration`), the latest review of each reviewer with its commit, and agent markers from trailers and the description; a push to `main` is validated whole and compared with the commit before it with the change rules off (new `--merged` flag), so a removed revision line fails with `OKF315` (G4); a manual run is a plain validation. `report_issue.py` (`poe report-issue`) keeps one issue per label. `validate.yml`: jobs `validate` (the required check), `check` (3.11 and 3.14), `scan` (`scan.py` and pinned gitleaks), `audit` (when `uv.lock` changes), `report` (opens or closes the `validation-failure` issue). `template-tests.yml`: tests on three systems and two Pythons, hooks on three systems, licences, the speed job, `check-config`. 604 concepts validate in 1.5 s here (limit 10 s). `setup_repo.py --ruleset-name main` converges the template's existing ruleset. Tests prove: FR1.5, FR2.5, FR2.6 through the CI entry point, pinned SHAs, least privilege, tasks only. All four workflows pass `check-config` (it caught two YAML errors). New gaps G27 to G29 | [Test] | none |
| 14 | `revision.yml`: a `mode` job reads `rules.revision_token`; `revision-app` (contents read, App token) or `revision-token` (contents write) records, then pushes with three rebase retries; checkout does not persist credentials (S1 finding); runs skip `Revision-Bot: true` commits; one run at a time. `stale-report.yml`: weekly, stale concepts, `--check-since` against the latest tag, pip-audit appended, one issue labelled `stale`. `runbook-revision-writer-recovery.md`. Live proof pending | [Test] | none |
| 15 to 16 | S2 live in the sandbox (details: shared notes `p2-s2-result.md`). `p2-scratch-github`: self-approved, approved by the App (non-owner), stale approval, `agent-drafted`, `full-review` (index shows `human-reviewed (self)`), a dropped run recovered by the next one (both lines written), a duplicate `uid` (the second PR conflicted; `renumber.py` gave ITM-0003); a deliberate mixed PR failed with `OKF001`; a failing commit on `main` opened one issue and the next green run closed it; `setup_repo.py` restored a deleted label and a merge setting. `p2-scratch-local` content: trailer cases correct, `poe release v0.0.1` ran; moved to `p2-w12-target`: HEAD and the annotated tag object unchanged, platform switched in one tooling PR, archive rebuilt in a fresh clone with both digests equal to the tag message, uploaded as a Release, earlier lines still `commit <sha7>`. Template: the App, `APP_CLIENT_ID` and `APP_PRIVATE_KEY` set; `revision` pushes through the App; `validate` is a required check on ruleset `main`. **Two defects found and fixed:** a revision commit failed `validate` with `OKF315` because the push path never passed the `Revision-Bot` flag, so every bot commit opened and closed a `validation-failure` issue (PR 7: `change_from_push` is now used, `ChangeContext.merged` replaces dropping the context); and the template's example concepts carried the template's history into libraries (PR #33, `reset_history`). Also: full Creative Commons texts vendored (G24 closed); runbooks for W-12, W-01 with the V-06 timing table and leak removal (not rehearsed, G33); `test_runbooks.py` checks every task, script, flag and runbook name they cite. New gaps G32 to G36 | [Test] | none |
| Actual effort | Agent hours per PR, from session length (not measured): PR 1 about 6, PR 2 about 9, PR 3 about 5, PR 4 about 6, PR 5 about 9, PR 6 about 10, PR 7 about 9 (with fixes #33); about 54 in total against 53 to 83 planned. Owner hours: about 8 (App and sandbox set-up, 7 merges, answers), against 14 to 20 planned. Calendar: 2026-11-03 to 2026-11-09, 7 days against 7 to 12 | [Inf] | P3 and P4 re-estimate below |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Approved 2026-11-03; applied 2026-11-09 with the P2 actuals | SDD §1 and §14; DDR change-log row 2026-11-09 |
| PP-2 | Decided 2026-11-03: fill, no ADR | Applied in PR 1: `constraints.md` table; DDR change-log row |
| PP-3 | Approved 2026-11-03 | Applied in PR 2: `OKF901` in `codes.py` and the catalogue |
| PP-4 | Approved 2026-11-03 | Applied in PR 1: SDD §6 and C-04 wording; DDR change-log row |
| PP-5 | Approved 2026-11-03; applied 2026-11-09 | SDD §14 P2 and P3 rows |
| PP-6 | Not needed: S1 confirmed AD-11, AD-12, W-05 and SDD §11 | `p2-s1-result.md`; closed 2026-11-09 |
| PP-7 | Not needed: 604 concepts validate in 1.5 s and the CI speed job passed | Closed 2026-11-09 |
| PP-8 | Approved 2026-11-03; applied 2026-11-09 | SDD C-05 |
| PP-9 | Approved 2026-11-03; applied 2026-11-09 | SDD §14 and §15 V-06 |
| PP-10 | Approved and applied 2026-11-09 | SDD §6 template-only paragraph and W-01 step 3 |
| PP-11 | Approved and applied 2026-11-09 | SDD §6 layout tree and template-only paragraph, W-01 step 3 |

## P3 and P4 estimate, proposed from P2 actuals [Inf]

P2 landed at the low end of its range (about 54 agent hours against 53 to 83; owner about 8 against 14 to 20), because the platform behaviour had been settled in S1 and the owner's steps were few and well guided. Two things cost more than planned: the first live runs found two defects that the unit tests could not (the `OKF315` push path, the example history), and every owner step needed a guided run sheet. Proposal, for the owner to decide (an SDD §14 edit, so a proposed entry, not applied):

| Phase | SDD §14 | Proposed | Why |
| --- | --- | --- | --- |
| P3 Site, release, skills | 5 to 7 days | 5 to 7 days, owner about 2 hours | `site.yml` and `release.yml` repeat the pattern of P2 (workflow, task, static check, sandbox run); the skills and the site generator are new; leak-removal rehearsal (G33) and the first scheduled `stale-report.yml` run are added |
| P4 Pilot and hardening | 5 to 8 days | 5 to 8 days, owner about 6 hours | Unchanged. Adds: V-06 timing by a second person with `runbook-instantiate-library.md`, the primary-type rename (G23), a second sandbox account for the two approval cases that are fixtures (G35), W-12 with several tags (G32) |

Risks to the estimate: the Zensical and MkDocs decision (ADR-001) and the skills' behaviour on a second runtime have no spike behind them; GitHub dropped events twice in the sandbox (G34), which can cost an hour each time in a live rehearsal.

## Draft: message of the annotated tag `v0.2.0`

The owner pushes the tag after the exit checks: `git tag -a v0.2.0 -F <file with this text> <commit on main>` then `git push origin v0.2.0`.

```text
OKF library template v0.2.0 (alpha)

Build phase P2: CI and governance.

- Platform adapters (github, git-local) and the revision writer with catch-up,
  approval inference, trust tiers and the optional verified field.
- Stale report, release archive (reproducible, tar digest canonical) and the
  release command for git-local libraries.
- init_library and setup_repo, the instantiation self-test for both platforms,
  full Creative Commons legal texts, and a clean revision history for each
  new library.
- Workflows: validate (required check), template-tests, revision, stale-report;
  scans, licence and vulnerability checks, speed gate.
- Runbooks: create the template repository, promote to public, move a
  git-local library to a platform, instantiate a library, recover the revision
  history, remove leaked content.

Verified live in the sandbox: each approval case that one owner and an App can
produce, a dropped run recovered, a duplicate uid, W-12 with archives rebuilt
from the tag. Known gaps: docs/development/testing/known-gaps.md (G1 to G36).
Not yet: site build, release workflow, skills (P3); pilot library and timing
by a second person (P4).
```
