# Plan: build phase P2

Status: **Approved by the owner on 2026-11-03:** the plan, the Q&A answers, the defaults for the remaining open decisions and proposed entries PP-1 to PP-9 as drafted (OD-12, the GitHub login, is still to be supplied at step 7). Nothing is built. What is built and why: `SPEC.md` (abbreviations are defined there). Checklist: `todo.md`. Effort is in **agent build hours** and **owner hours** per pull request, plus calendar time **[Inf]**; the basis is in "Effort". The SDD's person-day range (9.5–14.5; P1 close-out proposal 10.5–16) is not used here and the SDD is not edited (PP-1).

**NEEDS YOU** marks a step that needs a decision, person, account, machine or setting that only the owner can supply. Types: *decision*, *person*, *account*, *machine*, *setting*.

## Rules for every step

1. **Fixed inputs.** The SRS, SDD, DDR and ADR-001 to ADR-008 do not change. A step that finds a conflict stops and adds a proposed entry (below); it does not edit the document.
2. **Where work happens.** This repository, one branch per pull request, named `tooling/<slug>` (`docs/<slug>` for plan and runbook-only changes). Spikes and rehearsals run only in `open-renewables-sandbox` under the P0 guards: explicit repository on every `gh` call, synthetic content, nothing in `open-renewables` (OD-11).
3. **No commit, push, pull request or merge** without the owner's instruction. The owner merges (squash; recorded self-approval).
4. **Check before moving on.** A step is done when its check passes and `uv run poe check` and `uv run poe test` are green on the files it touched.
5. **Provider-neutral.** Tasks run through `uv run poe <task>`; workflows call only tasks (AD-20). No step creates `.claude/` or any product-specific file (ADR-002).
6. **Line endings.** Files are LF in the repository (`.gitattributes`). Edit existing CRLF working-tree files with line-ending-preserving scripts, not whole-file rewrites.
7. **Tests.** No network. Platform responses are recorded fixtures under `tests/template/fixtures/` (replayed by a fake transport); each adapter and workflow-facing function has golden files. Behaviour that cannot be tested goes to `../testing/known-gaps.md`.
8. **Actions.** Every `uses:` is pinned by full commit SHA with the version in a comment; every job declares `permissions`; no `pull_request_target`; no secret reaches a fork pull request (SDD §10).
9. **Logging actuals.** Each pull request's agent time and owner time are noted in `todo.md` when it closes, to calibrate the P3 and P4 estimate (P1 did not log them).

## Order of work and pull requests

| PR | Steps | Branch (suggested) | Depends on |
| --- | --- | --- | --- |
| 0 | This plan | `docs/p2-plan` | — |
| S1 | 1 V-05 closure (sandbox, no PR; fixtures land in PR 2) | — | Owner account steps |
| 1 | 2 Supply-chain tasks; 3 `scan.py` and hooks | `tooling/p2-supply-chain` | PR 0 |
| 2 | 4 Platform adapters; 5 Revision writer and `OKF9xx` | `tooling/p2-adapters-revision` | S1, PR 1 |
| 3 | 6 Stale report; 7 Intake and governance files | `tooling/p2-intake` | PR 1 |
| 4 | 8 Bundle and release | `tooling/p2-release` | PR 2 |
| 5 | 9 `init_library`; 10 `setup_repo`; 11 Self-test | `tooling/p2-instantiate` | PR 2, 3, 4 |
| S2 | Sandbox rehearsal of the workflow drafts (steps 12 and 14) | — | PR 5, S1 |
| 6 | 12 `validate.yml`, `template-tests.yml`, security jobs, matrix; 13 Required check (setting); 14 `revision.yml`, `stale-report.yml`, GitHub App, recovery runbook | `tooling/p2-ci` | S2 |
| 7 | 15 Scratch libraries, W-12 rehearsal, runbooks; 16 Exit | `tooling/p2-exit` | PR 6 |

Parallel sessions only where files do not overlap: S1 with PR 1; PR 3 with PR 2 (new files only). `pyproject.toml` tasks, `finding-codes.md` and `known-gaps.md` are shared; the later pull request rebases and the owner is told of the touch. The chain PR 1 → 2 → 4 → 5 → 6 → 7 is serial. PR 6 follows PR 5 so the self-test it runs already exists. PR 6 is the largest diff (three workflow groups and the App); inside it, commits are ordered `validate.yml`, then the security jobs and matrix, then `revision.yml`, so the owner can review in that order (OD-1).

## Steps

Each step: work, then **Check**.

### 1. Close V-05 in the sandbox (S1)

**NEEDS YOU (account, setting):** in `open-renewables-sandbox/p0-spikes`, create a GitHub App (`contents: write`, `pull_requests: read`, `pull_requests: write` for the test reviewer path), install it on that repository, store its client ID (variable) and private key (secret), add it to a `main` ruleset bypass list with mode "always"; no second account is used (OD-2): the non-owner and stale approvals are made by the App submitting review events. The agent writes the scripts and a step-by-step run sheet; the owner does the account and settings steps.

Work (agent, `gh` with explicit `--repo`, synthetic content): 5a push to a protected `main` with the App token bypass "always", and show that `GITHUB_TOKEN` is refused; 5c on a pull request: submit an approval review through the sandbox App on an earlier head, push a new commit, merge as the admin and as the author; record `reviews` (state, `commit_id`, `submitted_at`), `merged_by`, `merge_commit_sha`, labels and files; record the commit-to-pull-request lookups (closed-pull-request list by `merge_commit_sha`, `(#n)` in the subject, `commits/{sha}/pulls`) and their lag; save responses with tokens and personal data removed as fixtures with a README. Write the outcome to the shared notes and to `todo.md`.

Check: each of 5a and 5c has a written result labelled **[Test]**; fixtures exist for approved-current, approved-stale, non-owner, self-merge, merged-without-approval (the owner-approved and merged-by-someone-else cases are built by hand from the recorded response shape and labelled as such, a known gap per OD-2); any contradiction with AD-11, AD-12, W-05 or SDD §11 is a proposed entry (PP-6) before step 5 starts.

### 2. Supply-chain tasks (PR 1)

Work: `requirements/validate.txt` (and `dev.txt` if CI needs it) exported from `uv.lock` with hashes; `poe export` regenerates it and a check fails when it differs from the lock (`poe check` stays offline); `poe audit` (pip-audit through `uvx` on the exported set; exceptions read from `constraints.md`); `poe licences` (reads lock and installed metadata, applies the allowlist, the ADR-006/ADR-007 exceptions and metadata resolutions parsed from `constraints.md`, so the prose stays the only source; OD-6); fill "Pinned tool versions" with the gitleaks version and the SHA-256 of its release asset from that release's checksums file, plus the lychee version (PP-2, OD-7).

Check: a clean venv from `requirements/validate.txt --require-hashes` runs `validate_profile.py` and the validate tests; `poe licences` passes on the current lock and fails on a package added to a scratch lock with a GPL licence and on an unrecorded MPL-2.0 one; `poe export` is a no-op when the lock is unchanged; `poe audit` reports zero findings or lists each with its decision.

### 3. `scan.py` and hooks (PR 1)

Work: `scripts/scan.py` with patterns in configuration (default `profile/scan.yaml` with a meta-schema; confidentiality markers and secret-shaped patterns; library additions; PP-4), `--changed`, `--all`, `--json`, non-zero exit on a finding; the hook in `.pre-commit-config.yaml` (`repo: local`, through `uv run`); a gitleaks hook that runs only if the binary is installed; `poe scan`.

Check: planted marker and planted secret-shaped string each fail `scan.py`; a clean tree passes; the hook refuses a commit with a planted marker in Git Bash and PowerShell; with gitleaks absent the hook skips with a notice; the scan configuration validates against its meta-schema; coverage holds.

### 4. Platform adapters (PR 2)

Work: `okfprofile.platforms` with a protocol and data model (`MergedChange`: sha, subject, number or none, author, merged_by, labels, files, reviews with commit id, head sha; `Approval`), `github.py` (REST over `urllib` with the token from the environment, pagination, retries with back-off on the lookup lag, resolution order from W-05: closed-pull-request list by `merge_commit_sha`, `(#n)` in the subject, commit endpoint with retries) and `git_local.py` (commits since the last `Revision-Bot` commit, trailers `Approved-by`, `Full-Review`, `Agent-Drafted`, authors through `maintainers`, I-08); `codeowners` reused in both. The transport is injectable; the `validate.yml` helper that turns the event payload into `ChangeContext` (labels, reviews, head sha, author, agent markers, revision-bot flag) lives here.

Check: replay tests from the step 1 fixtures for every approval case; a lagging lookup is retried then resolved by the subject; a squash commit without a pull request resolves to `PR none`; `git_local` reads trailers from scratch git repositories; an author missing from `maintainers` is recorded by email local part as non-owner; no core module imports an adapter (a test fails if it does); mypy strict and coverage hold.

### 5. Revision writer and `OKF9xx` (PR 2)

Work: `write_revision.py` and `okfprofile/revision_writer.py`: find the commits on `main` since the last `Revision-Bot` commit, skip changes whose line is present, infer approval, currency and owner status per concept (W-05 steps 1 to 6), build lines (I-08), insert after the last line of the *Revision history* section and before footnote definitions, regenerate affected indexes, write `verified` when `write_okf_verified` (mapping with `process:` actor), one commit with the `Revision-Bot: true` trailer; `--check-since <tag>` reports changes without lines as `OKF9xx`; `poe revision`; assign `OKF9xx` codes in the catalogue (PP-3) with fixtures; `rules.revision_token` read, not used for calls.

Check: golden revision lines for each row of I-08 including the owner status of two concepts in one pull request (FR5.4); a dropped run: two merges, one run suppressed, the next run records both (FR3.2); a second run is a no-op; hand-edited and deleted lines fail on the next validation of `main` (G4 narrowed); the tier of the result equals the P1 golden tiers; `verified` mapping per tier agrees with an OKF reading of `human:` and `process:` (V-11); every `OKF9xx` has a failing fixture and the catalogue test passes; `git_local` writer produces the same lines from trailers; the writer never edits outside the section, indexes and `verified`.

### 6. Stale report (PR 3)

Work: `stale_report.py` (earlier of `stale_after` and `stale_after_default` after the last revision, FR3.11; `--json`; Markdown body for one tracking issue; revision-gap listing through `--check-since`; the pip-audit result is added by the workflow, not the script); `poe stale`.

Check: fixtures past each limit appear (FR3.11 acceptance); an offset-less `stale_after` is not accepted as a limit; a concept with no revision is reported as Unverified, not stale; JSON and Markdown agree.

### 7. Intake and governance files (PR 3)

Work: `.github/CODEOWNERS` (tooling paths to the maintainer; bundle folders as in I-15), `pull_request_template.md` (the four labels, I-11), `ISSUE_TEMPLATE/` (`new-concept.yml`, `correction.yml`, `feedback.yml`, `config.yml`, I-10), `dependabot.yml` (actions and pip), the label list as data for `setup_repo.py` (`intake:*`, `agent-drafted`, `full-review`, `approved-move`, `profile-migration`, `stale`, `validation-failure`); `poe check-config` validating workflows, forms and Dependabot against vendored JSON Schemas through `uvx check-jsonschema` (not part of `poe check`, needs a tool download once).

**NEEDS YOU (decision):** the GitHub login(s) for CODEOWNERS and `maintainers` (OD-12).

Check: `poe check-config` passes and fails on a planted bad form; each issue form names only labels in the label list; `codeowners` resolves a path in two folders to two owners; template text names every label; no file outside tooling paths and `.github/` is touched.

### 8. Bundle and release (PR 4)

Work: `build_bundle.py` per I-12 and ADR-004 (entries sorted, mode normalised, owner 0, mtimes set to the tagged commit's time, gzip without name or timestamp; manifest with tar SHA-256, `.tar.gz` SHA-256, Python and zlib versions, `platform`, counts by type, status and tier); `release.py <tag>` (gate by `--check-since`, full validation, bundle into `dist/`, annotated tag with the SHA-256 in `git-local`; check only in `github`); `poe bundle`, `poe release`.

Check: building twice gives equal tar digests; a checked-out tag rebuilt in a scratch clone reproduces the digest (FR7.3); a missing revision line fails the release (FR7.4); the archive reads with `tar` and the checksum verifies; the expected digest of a fixed fixture bundle is stored as a golden value for the matrix to compare (V-12, step 12); the `.tar.gz` digest is compared only when recorded Python and zlib versions match.

### 9. `init_library.py` (PR 5)

Work: questionnaire and `--answers` file (platform, name, title, description, maintainer, licence holder, content licence default CC BY 4.0, code licence default Apache 2.0, proprietary allowed, profile name, primary type and prefix, keep examples, `--keep-tests`); rewrite placeholders; write `LICENSE`, `LICENSE-content`, `LICENSE-template` as needed, keep `NOTICE`; reset the registry; write `DECISIONS.md` DR-01; remove template-only files (SDD §6) and, for `git-local`, `.github/` content except `CODEOWNERS`; idempotent on rerun.

Check: after a run no placeholder marker, no template-only file and no `docs/` remain; chosen licences, the Apache 2.0 text and `NOTICE` are present (FR6.2); rerun changes nothing; `AGENTS.md` markers stripped; the instantiated tree passes `validate_profile.py` and `build_indexes.py --check`.

### 10. `setup_repo.py` (PR 5)

Work: labels, squash-only merges, read-only default workflow permissions, Dependabot, `revision_token: github-token` for private libraries; for public libraries and the template: ruleset (require pull request, `validate` check where it exists, one approval with code-owner review, bypass admin "for pull requests only", App "always"), secret scanning and push protection; `--dry-run` (reports, changes nothing), `--check` (App installed and on the bypass list), `--promote` (W-11); every `gh` call takes the repository explicitly; rerunnable; `docs/development/operations/runbook-promote-library.md`.

**NEEDS YOU (setting, later):** running it against a real repository is the owner's act.

Check: `--dry-run` against recorded responses lists exactly the changes needed from a bare repository and none from a configured one; in the sandbox, a run on a scratch repository sets everything and a second run changes nothing; deleting a label and a setting then rerunning restores them (NFR7); `--promote` in the sandbox produces the W-11 end state.

### 11. Instantiation self-test (PR 5)

Work: `tests/template/instantiation/` with `answers-github.yaml` and `answers-git-local.yaml` (non-default licence choice); W-10 as a pytest module and `poe selftest` (copy without `.git`, run `init_library`, assert files and placeholders and licences, run validation and index check, run `new_concept` for each type and validate, and for `git-local`: `git init`, commits with trailers, `poe revision`, `poe release v0.0.1`, rebuild from the tag and compare the digest); `setup_repo.py` only in `--dry-run`.

Check: both modes pass; a seeded leftover placeholder and a leftover template-only file each fail; the `git-local` run calls no platform API (the fake transport raises if used); the test runs in under the time budget agreed in `testing/performance.md`.

### 12. Workflows, security jobs, matrix (PR 6)

Rehearse first in the sandbox (S2): copy the PR branch into a scratch sandbox repository with its ruleset and App, run each trigger, then open the pull request.

Work: `validate.yml` (triggers as W-04; job `validate` named identically for `pull_request` and `pull_request_review`; base-branch tooling for content; labels to `--label`, `approved-move` to the move rule, `profile-migration` to the migration rule; reviews to the pre-check; Linux, Python 3.11 and 3.14; push-to-`main` job running full checks and a `report` job opening or updating one `validation-failure` issue; skips the revision-only check for `Revision-Bot` commits per C-06); `template-tests.yml` (pytest and `poe check` on Linux, macOS and Windows × 3.11 and 3.14; `pre-commit run --all-files` on all three; licence check; selftest; pip-audit when `uv.lock` changes; gitleaks CLI at the pinned version with checksum verified; speed gate: a generated 600-concept bundle validated in under 10 s on the Linux runner; tar digest golden compared on all three systems); `check-config` job; permissions per job; actions pinned by SHA.

Check: workflows pass `poe check-config` and a pinned-SHA test (every `uses:` is a 40-character SHA, none uses `pull_request_target`); in the sandbox the same-commit local and CI findings are equal (FR2.8); a PR that relaxes the profile and adds a non-conforming concept fails (FR2.5); a mixed PR fails and passes with `profile-migration` plus approval (FR2.6); an `approved-move` label lets a registry move pass and its absence fails it (FR1.5); two PRs taking one `uid` produce a failure on `main` and one issue that updates on a second failure and the `renumber.py` fix clears (FR1.6, FR2.4); a planted secret fails the gitleaks job and a planted marker fails `scan.py` (NFR6); matrix is green on six jobs, pre-commit green on three (G1, G10 closed); the digest is equal on all three systems (V-12); speed gate result recorded (G8).

### 13. Required check on the ruleset (PR 6, setting)

**NEEDS YOU (setting):** after `validate` has run green on `main` at least once, add it as a required check to the `main` ruleset of `open-renewables/okf-library-template` (the runbook `operations/runbook-create-template-repository.md` is updated with the exact click path). Keep "Require approval of the most recent reviewable push" and "Do not allow bypassing" off (SDD §11).

Check: a throwaway docs-plus-knowledge pull request (closed unmerged) fails the check and cannot be merged without admin bypass; the next normal pull request shows the check as required.

### 14. `revision.yml`, `stale-report.yml`, GitHub App (PR 6)

Rehearse first in the sandbox (S2) with the sandbox App.

**NEEDS YOU (account, setting):** create the organisation App for `open-renewables/okf-library-template` (repository `contents: write`, `pull_requests: read`; one repository only), install it, put its client ID in a repository variable and its private key in a secret, add it to the `main` ruleset bypass list with mode "always"; the agent supplies a run sheet and `setup_repo.py --check` verifies it (about 10 minutes, SDD C-06).

Work: `revision.yml` (push to `main`, concurrency group `revision`, skip commits carrying `Revision-Bot: true`, App token, rebase and retry up to three times on a non-fast-forward, calls `uv run poe revision`); `stale-report.yml` (weekly and on demand: `poe stale`, `--check-since`, `poe audit`, one issue labelled `stale`); `docs/development/operations/runbook-recover-revision-history.md` (a missed run, a dropped line, a failed push, App key rotation).

Check: in the sandbox, a squash merge produces one bot commit with the lines and indexes; its push does not retrigger `revision.yml`; two merges with one run cancelled by the concurrency group are both recorded by the next run; the bot commit passes `validate`; the weekly job creates and then updates one issue; `setup_repo.py --check` reports the App on the bypass list. On the template repository after merge: the first knowledge-touching PR produces a bot commit and `main` stays green.

### 15. Scratch libraries, W-12, runbooks (PR 7)

**NEEDS YOU (account):** create the three synthetic repositories in `open-renewables-sandbox` (OD-11): `p2-scratch-github`, `p2-scratch-local` and `p2-w12-target`. V-06 timing is carried to P4 (OD-10).

Work: (a) GitHub scratch library from `init_library` with `platform: github`: merge pull requests for each approval case that one owner plus the App can produce (self-approved, App-approved non-owner, App-approved stale, `PR none`), a dropped run and a duplicate `uid`; the owner-approved and merged-without-approval cases rest on recorded fixtures (OD-2); (b) `git-local` scratch library: same cases from local commits and trailers, `poe release`; (c) W-12 rehearsal on the `git-local` library: pre-check, push, tooling pull request switching the platform, `setup_repo.py`, rebuild each earlier release from its tag and compare checksums; `docs/development/operations/runbook-move-git-local-to-platform.md`; (d) `runbook-leak-removal.md` (the only way history is rewritten, `../conventions.md`); (e) a run sheet `operations/runbook-instantiate-library.md` for the P4 timing by a second person (V-06 is carried to P4); (f) update `testing/` documents.

Check: each approval case in (a) and (b) matches its golden line; commit identifiers and revision lines are unchanged after (c) and each archive matches its recorded checksum (FR6.6); runbooks name only commands that exist; the second person's times for the platform steps are recorded in `testing/` or the carry to P4 is recorded (OD-10).

### 16. Exit (PR 7)

Work: full gate locally on 3.11 and 3.14 and in CI on three systems; coverage figure; `known-gaps.md` updated; P3 and P4 estimates proposed in the Effort units from P2 actuals (proposal, not applied); draft `v0.2.0` tag message.

Check: SPEC "Done when" 1 to 11 each ticked in `todo.md` with evidence; the owner tags `v0.2.0` after the last pull request is merged.

## Effort

Estimates are for an agent-built, owner-reviewed process **[Inf]**. Two figures per pull request, in hours: **agent** = active build time including test and CI iteration, **owner** = review, decisions, and account or setting steps. They are not additive with the SDD's person-days, which assumed one human doing all of it.

**Basis.** (1) P1 sizing: seven pull requests and the close-out in about four calendar days (2026-10-31 to 2026-11-03) against a plan of 10.25–15 person-days; actual hours were not logged. (2) Agent hours are taken as about 2 hours per P1-plan person-day of equivalent work, which would put P1 at roughly 20–30 agent hours; this is an assumption, to be calibrated by logging P2 actuals (rule 9). (3) Work against a real platform (workflows, rulesets, the App) is multiplied by 1.5 for CI iteration and the lag seen in V-05 (about 20 s per lookup). (4) Owner review is 0.5–1.5 hours per pull request, scaled by diff size and by how much logic needs checking; account and setting steps are counted at hands-on time.

**Assumptions.** One pull request reviewed per sitting; the owner turns a review around within one working day; parallel sessions only where files do not overlap (S1 with PR 1, PR 3 with PR 2); there is no second account, so two approval cases rest on fixtures; the owner's login is supplied for CODEOWNERS; no V-05 result forces an SDD change (otherwise add 4–8 agent hours and 1–2 owner hours for the proposed entry and its rework).

| Item | Agent (h) | Owner (h) | Owner content |
| --- | --- | --- | --- |
| PR 0 plan and Q&A | done | 1–1.5 | Review three files, ODs, PPs |
| S1 V-05 closure | 2–3 | 0.75–1.25 | App and ruleset set-up (0.5–0.75), review of result (0.25–0.5) |
| PR 1 supply chain, `scan.py` | 5–8 | 0.75–1.25 | Review; confirm pinned versions |
| PR 2 adapters and revision writer | 13–20 | 2.25–3.5 | Review of inference logic and golden lines |
| PR 3 stale report, intake files | 3–5 | 1–1.5 | Review; supply login |
| PR 4 bundle and release | 5–8 | 1–1.5 | Review |
| PR 5 init, setup, self-test | 8–12 | 1.5–2 | Review; run `setup_repo` on a scratch repository |
| S2 sandbox rehearsal | 3–5 | 0.5–1 | Watch results; no second account |
| PR 6 CI, security jobs, revision CI, App | 9–14 | 3–3.75 | Review (2–2.75), ruleset setting (0.25), App creation and secrets (0.75) |
| PR 7 rehearsals, runbooks, exit | 5–8 | 1.75–2.5 | Review, create three sandbox repositories, tag |
| **Total** | **53–83** | **13.5–19.75** (about 14–20) | |

**Calendar elapsed [Inf].** 7–12 working days, central estimate 9. The serial chain is six pull requests (PR 1, 2, 4, 5, 6, 7) at one per sitting, with S1 and PR 3 absorbed in parallel; at P1's pace (about 1.75 pull requests per day) it could finish in 4–5 days, but P2 adds waits P1 lacked: account and App steps and platform runs (up to 3 days). A slower owner turnaround (every other day) stretches the range to about 13 working days.

## Needs from you: summary

| Item | Need | Type | Blocks |
| --- | --- | --- | --- |
| All | Approve this plan; answer OD-1 to OD-12 or accept the defaults | decision | Step 1 |
| Proposed entries | Approve or reject PP-1 to PP-9 | decision | PP-2 and PP-4 before PR 1 merges; PP-3 before PR 2; PP-5 before PR 4 |
| Step 1 | Sandbox GitHub App, secret, ruleset on `p0-spikes` | account, setting | Step 5 (`revision.yml`) |
| Step 7 | GitHub login(s) for CODEOWNERS and `maintainers` | decision | PR 3 |
| Step 13 | Add `validate` to the `main` ruleset | setting | Mixed-change enforcement |
| Step 14 | Create and install the organisation App; variable, secret, bypass entry | account, setting | `revision.yml` on the template |
| Step 15 | Three synthetic repositories in the sandbox | account | Exit |
| Each pull request | Instruct commit, push, PR; review; squash-merge | person | Every PR |
| Exit | Push annotated tag `v0.2.0` | person | P2 exit |

## Proposed entries

Nothing below is written until the owner approves its text. IDs for ADRs are assigned on approval (next is ADR-009).

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| PP-1 | Always: the owner asked for agent and owner hours and calendar time in place of person-days | SDD §14 P2 row (9.5–14.5) and the executive-summary sentence quoting it; proposed text: agent 53–83 h, owner about 14–20 h, 7–12 working days **[Inf]**, with the P1 proposal 10.5–16 withdrawn | SDD edit with a DDR change-log row; P3 and P4 re-expressed at the P2 exit |
| PP-2 | Always: `constraints.md` "Pinned tool versions" is marked **To fill at the start of P2** | `../constraints.md` that table (gitleaks version and asset SHA-256, lychee version) | Fill of the placeholder the owner already decided (25 October 2026); ADR only if the owner reads a fill as a change to the bar |
| PP-3 | Always: `OKF9xx` has no numbered codes | `../architecture/finding-codes.md` (codes within the I-09 range, as P1 PP-4) | New rows; no SDD edit |
| PP-4 | Always: SDD C-04 says `scan.py` patterns "live in configuration" but names no file | SDD §6 layout and C-04 wording (`profile/scan.yaml`, its meta-schema); `profile/` is already a tooling path | SDD edit with a DDR change-log row |
| PP-5 | Always: SDD §14 puts `build_bundle` in the P3 row but `release.py` and reproducible archives in P2 | SDD §14 P2 and P3 rows (wording: `build_bundle` moves to P2; `release.yml` stays P3) | SDD edit with a DDR change-log row |
| PP-6 | Only if step 1 contradicts AD-11, AD-12, W-05 or SDD §11 (for example App bypass behaves differently, `commit_id` is absent, the lookup lag exceeds the retry budget) | The named AD or workflow text, or a new ADR | ADR or SDD edit; step 5 waits |
| PP-7 | Only if the 10 s speed gate fails on shared runners with no code change | `../constraints.md` Validation speed row (for example a runner-class note) | ADR; the limit is not relaxed silently |
| PP-9 | OD-10 carries V-06 to P4 now; SDD §14 carries the platform steps to "End of P2" | SDD §14 carried-item table (V-06 row: platform steps move to P4 with the full timing) | SDD edit with a DDR change-log row |
| PP-8 | OD-3 decided (default accepted): SDD C-05 says `validate.yml` and `template-tests.yml` run on 3.11 and 3.14 without naming systems | SDD C-05 wording (template tests run on three systems; library `validate.yml` on Linux) | SDD edit with a DDR change-log row |
| PP-10 | Always: `init_library.py` needs behaviour SDD §6 and W-01 do not state: for `git-local` it also removes `.github/dependabot.yml` and `.github/labels.yml` (the section lists only the issue forms, the pull request template and the workflows); when `tests/template/` is removed it drops the coverage gate in `pyproject.toml` (otherwise `poe test` fails at under 85 % because the tests that cover `okfprofile` are gone); it generates the library `README.md`, `CITATION.cff` and `DECISIONS.md` and renames the project in `pyproject.toml` and `uv.lock`; and it does not rename the primary type (known gap G23) | SDD §6 "Template-only files" paragraph and W-01 step 3 (wording), with a DDR change-log row | SDD edit; the primary-type question is the owner's |

## Risks

| Risk | Effect | Response |
| --- | --- | --- |
| The App, ruleset and three-way approval inference were never exercised against live GitHub | Writer built on wrong assumptions | Step 1 first, with recorded fixtures; PP-6; step 5 waits |
| Workflows can only be proven on GitHub | Slow edit-push-wait loops; a broken workflow on the protected template | Rehearse in the sandbox (S2) before each workflow pull request; `check-config` and the pinned-SHA test catch the cheap errors |
| `revision.yml` bot commit on a protected `main` | Writes refused or loops | App "always" bypass proven in step 1; trailer loop guard; concurrency group; tested in the sandbox |
| Commit-to-pull-request lookup lags (about 20 s in V-05) | A change recorded as `PR none` | Resolution order of W-05 with retries; a replay test covers the lag |
| Mixed-change rule becomes live in step 13 | Later `docs/`-plus-`knowledge/` pull requests fail | Announced; revision bot commits touch `knowledge/` only; P2 pull requests before it keep the split by discipline |
| Action SHA drift and Dependabot churn | Review load for a single maintainer | Dependabot groups action updates weekly; pinned-SHA test |
| 600-concept speed gate flaky on shared runners | False failures | Measure on Linux only, record variance in sandbox first; PP-7 rather than a silent relaxation |
| macOS and Windows minutes cost on private libraries | NFR3 breach for libraries | Matrix only in `template-tests.yml`; library `validate.yml` Linux only (OD-3); verify the multiplier before step 12 **[Inf]** |
| Trailers in `git-local` are not authenticated | Self-approval recorded as another owner's approval | Accepted by QA-59; listed in `known-gaps.md`; optional signing documented in the runbook |
| No second account for approval cases | Owner-approved and merged-by-someone-else cases are tested on recorded fixtures, not live | Accepted (OD-2); App-submitted reviews cover non-owner and stale cases live; recorded as a known gap |
| One large CI pull request (validate, security jobs, revision, App) | Hard to review; a fault blocks all three | Ordered commits, sandbox rehearsal first (S2), `validate.yml` proven before the App step enables `revision.yml` |
| Scope creep into P3 (`release.yml`, site, skills) | P2 overruns | SPEC out-of-scope list; interpretations 1 and 2 |
| Platform API shapes change after recording | Replay tests pass, live fails | Fixtures carry the recording date; the exit rehearsal runs live |

## Open decisions

Each has a default that applies if the owner does not answer.

| ID | Question | Default |
| --- | --- | --- |
| OD-1 | Pull request granularity | **Decided (2026-11-03):** seven pull requests, with adapters and revision writer together and all workflows together |
| OD-2 | Who is the second reviewer account for V-05 5c and the approval cases? | **Decided (2026-11-03): none.** Non-owner and stale approvals are made live by an App-submitted review; owner-approved and merged-without-approval cases use recorded fixtures built from the recorded shape; a known gap is recorded |
| OD-3 | Where does the operating-system matrix run? | **Decided (2026-11-03):** `template-tests.yml` on Linux, macOS and Windows × 3.11 and 3.14; library `validate.yml` Linux only (PP-8) |
| OD-4 | Is `build_bundle.py` in P2? | **Decided (2026-11-03):** yes (PP-5) |
| OD-5 | `scan.py` configuration location and pattern set | `profile/scan.yaml` with meta-schema; markers plus secret-shaped patterns; libraries add patterns (PP-4) |
| OD-6 | Source of the licence allowlist for `poe licences` | Parse `constraints.md` (single source), no copy in code |
| OD-7 | Which gitleaks and lychee versions to pin | The latest releases at the start of PR 1; the agent reads the release checksums file (public, read only) and the owner confirms the values in the review |
| OD-8 | Do hooks and `poe check` stay offline? | Yes; network tasks (`audit`, `check-config`) are separate tasks run in CI |
| OD-9 | Tag at exit | **Decided (2026-11-03):** Owner pushes annotated `v0.2.0` (alpha) on `main`; no GitHub Release (`release.yml` is P3) |
| OD-10 | V-06 platform steps timing | **Decided (2026-11-03): carried to P4 now.** The SDD §14 carry is extended by a proposed entry (PP-9); a run sheet is written in step 15 |
| OD-11 | Where rehearsals run | **Decided (2026-11-03): the owner creates the three repositories.** V-05 in `open-renewables-sandbox/p0-spikes`; scratch libraries and the W-12 target as new synthetic repositories in `open-renewables-sandbox` named `p2-scratch-github`, `p2-scratch-local` and `p2-w12-target`; the owner creates them or grants rights; all deleted or archived at exit |
| OD-12 | GitHub login for CODEOWNERS and `maintainers` | The owner supplies it at step 7; the files use a placeholder until then and the PR is not merged with one |
