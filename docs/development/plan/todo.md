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

- [ ] 4. `okfprofile.platforms`: data model, `github` (standard library REST, retries), `git_local` (trailers, `maintainers`), event-to-`ChangeContext` helper; step 1 fixtures committed
- [ ] 4. Check: replay tests for every approval case; lagging lookup retried then resolved by subject; `PR none`; unknown author recorded as non-owner; no core module imports an adapter

- [ ] 5. `write_revision.py` with catch-up, inference, insertion, indexes, optional `verified`, `--check-since`; `OKF9xx` codes in the catalogue (PP-3); `poe revision`
- [ ] 5. Check: golden lines for every I-08 row and two concepts in one PR; dropped run recovered; second run no-op; hand-edited and deleted lines caught on `main`; `verified` agrees with an OKF reading; failing fixture per `OKF9xx`; `git_local` gives the same lines

## PR 3: stale report and intake files (`tooling/p2-intake`)

- [ ] 6. `stale_report.py`, `poe stale`
- [ ] 6. Check: fixtures past each limit listed; offset-less `stale_after` rejected; no-revision concept reported Unverified
- [ ] **NEEDS YOU (decision):** GitHub login(s) for CODEOWNERS and `maintainers` (OD-12)
- [ ] 7. CODEOWNERS, PR template, three issue forms and `config.yml`, `dependabot.yml`, label list, `poe check-config`
- [ ] 7. Check: config check passes and fails on a planted bad form; forms name only listed labels; two-folder path resolves to two owners

## PR 4: bundle and release (`tooling/p2-release`)

- [ ] 8. `build_bundle.py` (reproducible, ADR-004), `release.py`, `poe bundle`, `poe release` (PP-5)
- [ ] 8. Check: equal tar digest on two builds and from a tag in a scratch clone; missing revision line fails release; checksum verifies; golden digest stored for the matrix

## PR 5: instantiation (`tooling/p2-instantiate`)

- [ ] 9. `init_library.py` (questionnaire, `--answers`, licences, template-only removal, idempotent)
- [ ] 9. Check: no placeholder, template-only file or `docs/` left; licence files, Apache 2.0 text and `NOTICE` present; rerun is a no-op; result validates
- [ ] 10. `setup_repo.py` with `--dry-run`, `--check`, `--promote`; `runbook-promote-library.md`
- [ ] 10. Check: dry run against recorded responses lists exactly the needed changes; sandbox run sets everything and a second run changes nothing; deleted label and setting restored; `--promote` reaches the W-11 end state
- [ ] 11. `tests/template/instantiation/`, W-10 self-test, `poe selftest`
- [ ] 11. Check: both modes pass; seeded leftover placeholder and template-only file fail; `git-local` run makes no platform call; rebuilt archive digest matches

## S2: sandbox rehearsal of workflows

- [ ] Scratch sandbox repository with ruleset and App; step 12 and 14 drafts run on every trigger

## PR 6: CI, security jobs and revision CI (`tooling/p2-ci`)

- [ ] **NEEDS YOU (decision):** confirm current hosted-runner minute multipliers for private repositories before the matrix is fixed (OD-3, PP-8)
- [ ] 12. `validate.yml`, `template-tests.yml`, gitleaks job, pip-audit, licence check, hooks on three systems, speed gate, `check-config`; actions pinned by SHA
- [ ] 12. Check: local and CI findings equal (FR2.8); FR2.5, FR2.6, FR1.5, FR1.6 and FR2.4 scenarios in the sandbox; planted secret and marker caught (NFR6); six matrix jobs and three hook jobs green (G1, G10); digest equal on three systems (V-12); speed gate result recorded (G8); pinned-SHA test passes
- [ ] **NEEDS YOU (setting):** after `validate` is green on `main`, add it as a required check on the `open-renewables/okf-library-template` ruleset (step 13)
- [ ] 13. Check: throwaway mixed pull request fails and is not mergeable; next normal pull request shows the check as required; runbook click path updated

- [ ] **NEEDS YOU (account, setting):** organisation App created and installed on the template repository only; client ID variable, private key secret, ruleset bypass "always"
- [ ] 14. `revision.yml`, `stale-report.yml`, `runbook-recover-revision-history.md`
- [ ] 14. Check: sandbox: one bot commit, no retrigger, dropped run recovered, bot commit passes `validate`, weekly issue created then updated; `setup_repo.py --check` passes; template: first knowledge-touching PR produces a bot commit and `main` stays green

## PR 7: rehearsals and exit (`tooling/p2-exit`)

- [ ] **NEEDS YOU (account):** three synthetic repositories in `open-renewables-sandbox` (OD-11)
- [ ] 15. GitHub scratch library: each approval case live, dropped run, duplicate `uid`
- [ ] 15. `git-local` scratch library: same cases from local commits and trailers; `poe release`
- [ ] 15. W-12 rehearsal and `runbook-move-git-local-to-platform.md`; `runbook-leak-removal.md`; `runbook-instantiate-library.md` run sheet
- [ ] V-06 carry to P4 recorded (OD-10 decided, PP-9); run sheet for the P4 timing written
- [ ] 15. Check: golden line per case; commit identifiers and lines unchanged after W-12 and archives match; runbooks name only existing commands
- [ ] 16. Full gate locally and in CI; `testing/` updated; P3 and P4 estimate proposed from actuals; `v0.2.0` tag message drafted
- [ ] Sandbox repositories and Apps cleaned up or archived (OD-11)

## Exit

- [ ] SPEC "Done when" items 1 to 11 met, evidence in the Outcomes table
- [ ] **NEEDS YOU (person):** owner pushes annotated tag `v0.2.0` (alpha) on `main` (OD-9)
- [ ] Proposed entries PP-1 to PP-9 decided and, where approved, applied
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-11-p2-ci-governance/` and re-point relative links; the SRS status is not changed

## Outcomes

One line per step when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any. Include agent and owner hours per pull request.

| Step | Outcome | Label | Entry |
| --- | --- | --- | --- |
| 1 | 5a: App push to protected `main` accepted by the "always" bypass, `GITHUB_TOKEN` push refused (GH013). 5c: a stale approval keeps `commit_id` of the approved head and still satisfies the rule; an unapproved owner merge is `blocked` and passes by the Admin bypass, `merged_by` = author. Lookup: closed-list and subject hit at the first poll (about 4 s), `commits/{sha}/pulls` up to 8.4 s. Org policy refuses "Actions can approve pull requests", so the owner opened the PRs and the App approved. Findings: `persist-credentials: false` for `revision.yml`; bot commits have no author login (use the trailer); client ID needs capital `I`. No contradiction with AD-11, AD-12, W-05, SDD §11. Notes: `side-session-notes/.../p2-s1-result.md` | [Test] | none (PP-6 not triggered) |
| 2 to 3 | PR 1 built, uncommitted on `tooling/p2-supply-chain`. `requirements/validate.txt` and `dev.txt` exported from `uv.lock` with hashes (`poe export`; `export_requirements.py --check` is a `poe check` step); a clean venv from each with `--require-hashes` validates the bundle and passes `tests/library`. `poe licences`: 36 locked packages checked, 0 findings (allowlist, ADR-006/007 exceptions and metadata resolutions parsed from `constraints.md`). `poe audit`: 0 findings. gitleaks v8.30.1 and its `linux_x64` SHA-256, and lychee-v0.24.2, filled in `constraints.md` (PP-2). `scan.py` with `profile/scan.yaml` and its meta-schema (PP-4); hook refuses a planted marker (Git Bash) and a planted secret (PowerShell, redacted) and passes clean commits; gitleaks hook skips with a notice when not installed. `poe check` clean, `poe test` 403 passed, coverage 98.77 %. New gaps G11 to G13 | [Test] | PP-2, PP-4 applied |
| 4 | | | |
| 5 | | | |
| 6 to 7 | | | |
| 8 | | | |
| 9 to 11 | | | |
| 12 to 13 | | | |
| 14 | | | |
| 15 to 16 | | | |
| Actual effort | agent h / owner h per PR | [Inf] | P3 and P4 re-estimate |

### Status of proposed entries

| # | Status | Evidence |
| --- | --- | --- |
| PP-1 | Proposed | |
| PP-2 | Decided 2026-11-03: fill, no ADR | Applied in PR 1: `constraints.md` table; DDR change-log row |
| PP-3 | Proposed | |
| PP-4 | Approved 2026-11-03 | Applied in PR 1: SDD §6 and C-04 wording; DDR change-log row |
| PP-5 | Proposed | |
| PP-6 | Conditional (step 1) | |
| PP-7 | Conditional (step 12) | |
| PP-8 | Proposed (OD-3 decided) | |
| PP-9 | Proposed (OD-10 decided) | |
