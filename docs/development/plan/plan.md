# Plan: build phase P3

Status: **Approved by the owner on 2026-11-11:** the plan, all open decisions OD-1 to OD-15 (defaults accepted, OD-4, OD-5, OD-6 and OD-9 answered explicitly) and proposed entries PP-1 to PP-6 as drafted; PP-7 to PP-11 stay conditional. Nothing is built. What is built and why: `SPEC.md` (abbreviations are defined there). Checklist: `todo.md`. Effort is in **agent build hours**, **owner hours** and calendar days, as in P2; the basis is in "Effort". The SDD's P3 row (5–7 days, owner about 2 hours) is not edited here (PP-1).

**NEEDS YOU** marks a step that needs a decision, person, account, machine or setting that only the owner can supply. Types: *decision*, *person*, *account*, *machine*, *setting*.

## Rules for every step

1. **Fixed inputs.** The SRS, SDD, DDR and ADR-001 to ADR-008 do not change. A step that finds a conflict stops and adds a proposed entry (below); it does not edit the document.
2. **Where work happens.** This repository, one branch per pull request, named `tooling/<slug>` (`docs/<slug>` for plan-only changes). Rehearsals run only in `open-renewables-sandbox` under the P0 guards: explicit repository on every `gh` call, synthetic content, nothing in `open-renewables` (OD-11).
3. **No commit, push, pull request or merge** without the owner's instruction. The owner merges (squash; recorded self-approval).
4. **Check before moving on.** A step is done when its check passes and `uv run poe check` and `uv run poe test` are green on the files it touched.
5. **Provider-neutral.** Workflows call only `uv run poe <task>` (AD-20). No step commits `.claude/` or any product-specific file (ADR-002).
6. **Line endings.** Files are LF in the repository. Edit existing CRLF working-tree files with line-ending-preserving scripts, not whole-file rewrites.
7. **Tests.** No network. Site tests need the site groups and skip with a notice where they are not installed; CI installs them. Behaviour that cannot be tested goes to `../testing/known-gaps.md`.
8. **Actions.** Every `uses:` is pinned by full commit SHA with the version in a comment; every job declares `permissions`; no `pull_request_target`; no secret reaches a fork pull request (SDD §10).
9. **Logging actuals.** Each pull request's agent time and owner time are noted in `todo.md` when it closes, to calibrate the P4 estimate.
10. **Live runs find what unit tests cannot** (P2: two defects). Each workflow is rehearsed in the sandbox before its pull request is merged.

## Order of work and pull requests

| PR | Steps | Branch (suggested) | Depends on |
| --- | --- | --- | --- |
| 0 | This plan | `docs/p3-plan` | — |
| 1 | 1 Skill checks and `use-bundle`; 2 `author-concept` and adapter; 3 `AGENTS.md` | `tooling/p3-skills` | PR 0 |
| 2 | 4 Site stack; 5 `mkdocs.yml`, tasks, compatibility tests; 6 `site.yml`; 7 Instantiation and self-test | `tooling/p3-site` | PR 0 |
| S3a | Sandbox rehearsal of `site.yml` | — | PR 2 drafted |
| 3 | 8 `GOVERNANCE.md`, `README.md`, `NOTICE`; 9 RFC and `.idea/` | `tooling/p3-governance` | PR 1 |
| 4 | 10 `release.yml` and archive changes | `tooling/p3-release` | PR 1, PR 2 |
| S3b | 11 Sandbox rehearsal of `release.yml`, smoke runs of the skills | — | PR 4 drafted |
| 5 | 12 Stale-report read, leak-removal rehearsal; 13 Test docs, clean-up, exit | `tooling/p3-exit` | PR 3, PR 4, S3b |

PR 1 and PR 2 touch disjoint files and may run in parallel; `pyproject.toml`, `requirements/`, `finding-codes.md` and `known-gaps.md` are shared and the later pull request rebases (the owner is told of the touch). PR 3 can run alongside PR 2. PR 4 needs both skills (archive) and the site workflow (tag run). PR 5 is last. Fixed order inside PR 2: step 4, 5, 6, 7 as separate commits so the owner can review in that order (OD-1).

## Steps

Each step: work, then **Check**.

### 1. Skill checks and `use-bundle` (PR 1)

Work: `scripts/check_skills.py` (`poe check-skills`, offline, added to `poe check`; own output and exit code, `--json`, no `OKF` code, as `scan.py`): each `.agents/skills/*/SKILL.md` has frontmatter limited to `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`; `name` equals the folder, lower-case hyphenated; `description` non-empty and within the specification's length; body within the specification's recommended size; every relative file or script the skill names exists; no concept type name, `uid` prefix or tag namespace declared in `profile.yaml` appears in a skill (AT-FR7.1-01). Write `.agents/skills/use-bundle/SKILL.md` (C-08): read `AGENTS.md`, then `profile/profile.yaml` for types, statuses and vocabulary path; start at the root `index.md` and follow indexes one level at a time; read a concept's declared sections by heading, not the whole file; read tags against `vocab/`; for each concept used report `uid`, status, trust tier from the index line (keeping the `(self)` qualifier) and the release tag (from the archive's release-identity file, else ask the user; PP-3); never describe Unverified, Machine-confirmed or draft content as reviewed; say when a concept is deprecated or past `stale_after`. No script, so it runs from a release archive alone. A `references/` file holds the tier table if the body would exceed the size limit.

Check: `poe check-skills` passes on the real skill and fails on four planted faults (extra frontmatter field, name not equal to folder, a profile type name in the body, a missing referenced file); `poe check` includes it; the existing archive test lists the skill folder in `ARCHIVE_FOLDERS`; coverage holds; no provider-specific file added.

### 2. `author-concept` and the optional adapter (PR 1)

Work: `.agents/skills/author-concept/SKILL.md` (C-08): read the declared type, body sections and formats from the profile; create the file with `uv run scripts/new_concept.py <type> <path>`; fill the declared sections in their formats; choose tags only from the vocabularies; cite sources as footnotes; leave `status: draft` (stable is an owner's act); never edit the *Revision history* section, any `index.md` or the registry by hand; run `build_indexes.py` and `validate_profile.py`; mark the change agent-drafted (the `agent-drafted` label in `github` mode, an `Agent-Drafted: yes` trailer in `git-local` mode, chosen from `platform` in the profile); name the Vocabulary `namespace` and Glossary limits as manual steps (G23 stays open). `scripts/link_skills.py` (`poe link-skills`): copies each `.agents/skills/<name>` to `.claude/skills/<name>` for Claude Code, idempotent, refuses to overwrite a folder it did not create, `--link` for a directory link, `--dry-run`, `--json`; `/.claude/skills/` is already in `.gitignore`. The command is documented in `README.md` and `AGENTS.md` (ADR-002). Evaluation prompts for P4 (OD-14) are written to `../testing/skill-evals.md`: positive and negative trigger prompts and the expected behaviour per skill, after the allenday pattern named in the SRS.

Check: `poe check-skills` passes; a test extracts every fenced command from both `SKILL.md` files and fails if a script, task or flag does not exist (the `test_runbooks.py` pattern); a scratch library follows the author skill's command sequence and the result validates and has an up-to-date index; `link_skills` twice changes nothing, refuses a foreign folder, and leaves `git status` clean; the repository still has no tracked `.claude/` path.

### 3. `AGENTS.md`, library-facing (PR 1)

Work: replace the stub below the `template-only` markers (the markers and the block stay): what the bundle is and its layout; navigate by indexes one level at a time; cite a concept by `uid` and release tag; the trust tiers (Unverified, Machine-confirmed, Human-reviewed, `human-reviewed (self)`) and the rule never to treat the first two as reviewed; where the profile, vocabularies and registry are; how to author (the two skills, the adapter command, `uv run poe check`); what is CI-managed and never hand-edited (revision history, indexes, registry); tooling and content go in separate pull requests; the two platform modes in one paragraph; no domain text and no concept type named. Short enough to sit in an agent's context (target under 120 lines).

Check: `init_library` output has no template-only text and no unresolved placeholder in `AGENTS.md` (self-test); every command it names exists (runbook-style test); `CLAUDE.md` in the template still loads `AGENTS.md` (V-10 import form); `check-skills` rule on type and prefix names also passes on `AGENTS.md`.

### 4. Site stack (PR 2)

Work: dependency groups `site-mkdocs` (`mkdocs==1.6.1`, `mkdocs-material` 9.7.x as the newest 9.7 release, whose end of life was 2026-11-05) and `site-zensical` (exact `zensical` 0.0.x, the latest release at the start of the PR; OD-3); neither in `default-groups`; `poe install` already syncs all groups; `uv lock`; `requirements/site-mkdocs.txt` and `site-zensical.txt` exported with hashes (`export_requirements.py` and its `--check` extended); `poe licences` extended to the site groups with their dependencies (G11); `poe audit` covers the site exports; lychee asset SHA-256 filled in `constraints.md` "Pinned tool versions" (PP-2); verify both stacks install on Python 3.11 and 3.14. Any licence not on the allowlist is a proposed entry (PP-8), not an edit.

Check: a clean venv from each hashed file installs with `--require-hashes` and `--version` runs; `poe licences` reports zero findings with the site groups installed or lists each with its decision; `poe export` is a no-op on an unchanged lock; `poe audit` reports zero findings or lists each with its decision; the `validate` group and its export are unchanged (NFR6).

### 5. `mkdocs.yml`, tasks and compatibility tests (PR 2)

Work: `mkdocs.yml` at the I-13 baseline (`docs_dir: knowledge`, `strict`, `use_directory_urls`, `navigation.indexes`, `content.action.edit`, `repo_url`, `edit_uri`, footnotes, `attr_list`, `toc`, `tags`, issue-form link in `extra.social`, `extra.status`; `theme.variant: classic` and Zensical's own link keys only if MkDocs tolerates them); `scripts/build_site.py` and tasks `docs` (serve), `docs-build` (strict MkDocs build), `docs-zensical` (Zensical build run in a temporary copy because it has no `--site-dir`), `docs-linkcheck` (lychee offline with fragments; skips with a notice if absent); `scripts/check_site.py` (`--json`): compare the built page list with the bundle's concept list and between builders, and `--manifest <tag> <commit>` write `release.json` into a built site (PP-3). A fixture bundle under `tests/template/fixtures/site/` exercises FR8.2: folder `index.md` as landing page; relative links with `%20`, and between folders; unknown frontmatter keys; explicit `<a id>` anchors against heading slugs; the reserved keys `id`, `title`, `description`, `tags`, `slug`, `status`; colon-namespaced tags; `<1000 V and {braces}`; footnotes. Tests (`site` marker) run both builders. MkDocs must pass all six. For Zensical each check has a recorded expected result and a reason; a release that changes a result fails the test and says so, so a silent change cannot pass (ADR-001: judge output, not exit code). A second test builds the same `mkdocs.yml` with both builders' keys present (ADR-001 carried issue). A divergence test renders the constructs the profile does not use (lists after paragraphs, tables, nested footnotes, inline HTML next to Markdown) with markdown-it-py and Python-Markdown and writes the differences to `../testing/site-divergences.md` for review (G2, AT-FR8.2-04). A site build of a generated 600-concept bundle is timed on Linux (OD-8).

Check: AT-FR8.1-01 (build reads in place: `git status --porcelain knowledge/` empty; fails if `knowledge/` is unreadable) and AT-FR8.2-01 to -03 pass on MkDocs; Zensical results recorded per check, each failure a known gap or a proposed entry (PP-7 if MkDocs rejects Zensical keys, so one `mkdocs.yml` is not possible); divergences listed, any that need a profile or authoring rule are a proposed entry (PP-9); a planted broken link fails the strict build; time recorded in `../testing/performance.md`.

### 6. `site.yml` (PR 2)

Work: triggers: pull requests touching `knowledge/`, `profile/`, `mkdocs.yml`, the lock or the workflow, and tags `v*` (W-08); job `mkdocs` (blocking: `poe docs-build`, `check_site`, release manifest on tags, preview artifact); job `zensical` (`continue-on-error`: `poe docs-zensical`, lychee at the pinned version with its checksum verified, page-list comparison, a summary of results); job `deploy` (`needs: mkdocs`; runs only if `poe site-deploy-check` says the tag is v1.0.0 or later and `library.site_url` is set, so the template and every library stay off Pages before v1.0.0, FR8.5; `pages: write` and `id-token: write` on this job only). A library without GitHub has none of this (`init_library` removes `.github/workflows/`).

**NEEDS YOU (account, setting), at S3a:** create the synthetic repository `p3-scratch-github` in `open-renewables-sandbox` (public, App installed as before), enable GitHub Pages for it (OD-6, OD-11).

Check: `poe check-config` passes; tests prove every `uses:` is a full SHA, no `pull_request_target`, every job declares `permissions`, `pages` and `id-token` write appear only in `deploy`, every `uv run` is a poe task (extending the P2 tests); the S3a rehearsal below.

**S3a, sandbox rehearsal (before PR 2 merges):** instantiate `p3-scratch-github` from the PR 2 branch with `init_library` and `setup_repo`; a pull request that changes a concept builds the preview artifact; AT-FR8.4-01: in the artifact, "Suggest an edit" points at `edit/main/knowledge/<path>` and the footer link at `issues/new/choose`; a tag `v0.0.1` builds from the tag and the site `release.json` names it (AT-FR8.3-01); `gh api repos/<repo>/pages` shows no site after those runs (AT-FR8.5-01); with `library.site_url` set, tag `v1.0.0` deploys to Pages, then Pages is disabled again (OD-6); Zensical job is red or green without failing the run; both results recorded **[Test]**.

### 7. Instantiation and self-test (PR 2)

Work: `init_library.py` rewrites `mkdocs.yml` (site name from the library title, `site_url` from `library.site_url`, `repo_url`, `edit_uri`, issue-form link), and for `git-local` removes the repository-based keys so a local site shows no dead link (PP-6); the leftover-name check covers `mkdocs.yml`; `poe selftest` gains W-10 step 4 (`poe docs-build` on both instantiated copies; skipped with a notice where the site group is not installed, required in CI) (G25).

Check: both instantiated trees build strict; a seeded `okf-library-template` string in `mkdocs.yml` fails the self-test; the `git-local` site has no repository link; a rerun is a no-op; `poe selftest` stays within the budget in `../testing/performance.md`, or the budget change is noted.

### 8. `GOVERNANCE.md`, `README.md`, `NOTICE` (PR 3)

Work: `GOVERNANCE.md` from the SRS Governance section and C-09: roles (maintainers, directory owners); one approval for `stable`, with a single maintainer's recorded self-approval and when to set `require_non_author_approver`; definition of stable; contribution routes (issue forms, pull requests) and labels; decisions in `DECISIONS.md`; semver and what makes a major release; staleness and deprecation (never delete); where to report a security problem; maintainer and contact placeholders rewritten by `init_library` (G18: `config.yml` links this file). `README.md` (the template's own): remove "in development (build phase P0)" and "(planned)"; quick start with the three instantiation routes and the runbook; commands; skills and the optional Claude Code adapter; site and release in two lines each; licence map; document list. `NOTICE`: review only; it changes only if a step vendors something (none planned; site dependencies are installed, not vendored).

Check: the instantiated library has no template text or unresolved placeholder in `GOVERNANCE.md` or `README.md`; the `config.yml` link resolves to a file; every command in the README exists (runbook-style test); a test checks that each path `NOTICE` names exists and that every folder under `scripts/vendor/` is named there; the licence map matches the files present after instantiation (FR6.2).

### 9. Housekeeping (PR 3)

Work: `../rfcs/RFC-001-scope-notes.md` (G6, Status: Draft): I-07 says folder lines show "scope from the folder's scope note" but no type or location exists, and the P4 pilot needs scope notes (SDD §14); the RFC sets out options (a folder `_scope.md` concept type; frontmatter on a hand-written folder page; none) with a recommendation, and builds nothing (OD-4). Untrack `.idea/` and add it to `.gitignore` (G30; OD-12), then drop the instantiation warning that existed only for it.

Check: the RFC follows `../rfcs/README.md`; `git ls-files .idea` is empty; instantiation prints no `.idea` warning; `poe check` and `poe selftest` pass.

### 10. `release.yml` and archive changes (PR 4)

Work: `release.yml` on tags `v*.*.*`, jobs with their own permissions: `gate` (`poe release <tag>` in `github` mode: revision-line gate against the previous tag and validation, FR7.4); `build` (`poe bundle <tag>`, `--verify`, upload artifacts); `rebuild` (a second clean checkout of the tag rebuilds the archive and compares the tar digest, the `.tar.gz` digest only if Python and zlib match, ADR-004; Linux only, so private libraries stay inside free minutes, OD-3 of P2); `publish` (the only job with `contents: write`: create the Release as a draft, attach archive, checksum and manifest, then publish so an immutable Release is complete when it becomes final; generated notes; marked pre-release while the major version is 0; PP-4). Archive: write a release-identity file (tag, commit, date; PP-3) and confirm the builder includes `.agents/skills/use-bundle/`; tolerate the absence of `CITATION.cff` (the template has none, OD-10); regenerate the golden digest for the matrix (V-12). `setup_repo.py` documents immutable releases as the manual setting it already lists.

**NEEDS YOU (setting):** immutable releases are a repository setting with no API call (G26). Turn it on in the sandbox repository for S3b; on the template, turn it on only after S3b and only if you accept that `v0.5.0` and its assets can then never change (OD-9).

Check: static tests (pinned SHAs, least privilege, tasks only, `contents: write` only in `publish`); the archive lists exactly the I-12 contents plus the release-identity file; AT-NFR1-01 as a scripted check (reach one concept from the root index and read its sections with `ls`, `cat` and `grep` only); building twice and from a scratch clone at the tag gives equal tar digests; a deleted revision line fails the gate and a restored one passes (AT-FR7.4-01); the golden digest is stored.

### 11. Release rehearsal and skill smoke runs (S3b)

Run in `p3-scratch-github` with immutability on: push `v0.0.1`; AT-FR7.3-03: a Release exists with archive, checksum, manifest and notes, marked pre-release, and an attempt to replace or delete an asset is refused; `sha256sum -c` passes and the tar digest equals the manifest; the rebuild job is green; delete a concept's revision line and push `v0.0.2`: the gate fails with an `OKF9xx` finding and no Release exists; restore it and tag again. Then two agent runs with a fresh agent session each and no other context than the files given (one provider; the owner may add a second runtime, OD-13): (a) `use-bundle` from the downloaded archive and `AGENTS.md` only, on five questions chosen by the reviewer, expecting navigation by indexes, sections read by heading, tags read from `vocab/`, and per concept `uid`, status, tier and tag (AT-FR7.1-03; the traced 100 % check is P4); (b) `author-concept` in a clone, drafting a concept that validates and is labelled agent-drafted (AT-FR7.1-02 on the scratch library, not yet the pilot). Record each result and any change the skills need.

**NEEDS YOU (person):** choose the five questions; optionally run the same prompts on another runtime and report.

Check: AT-FR7.3-03 and AT-FR7.4-01 pass live; both smoke runs meet their expectations or the skill is corrected and rerun; results labelled **[Test]** and stated as one provider (ADR-002); contradictions with C-10, W-07 or I-12 are proposed entries (PP-4, PP-10) before PR 4 merges.

### 12. Stale-report read and leak-removal rehearsal (PR 5)

Work: (a) read the scheduled `stale-report.yml` run of 2026-11-09 (run 42629913632, success; its job summary and whether an issue exists) and record the result in `todo.md` (G27); after PR 3 and PR 4 merge, confirm the next scheduled run (Monday 2026-11-16 at the earliest) is green and its report includes the new tag in the revision-gap check. (b) Rehearse `../operations/runbook-remove-leaked-content.md` on `p2-w12-target` (OD-11), which already has a tag, a Release, a ruleset and the App: merge a pull request that adds a synthetic secret-shaped string (a labelled fake), detect it with `poe scan --all` and gitleaks, then follow the runbook with `git filter-repo` (installed with `uvx` or pip), disable the ruleset, force-push, re-enable it and run `setup_repo.py --check`. Observe and record: what `validate` on `main` reports after the rewrite (`OKF315`, `OKF9xx`), what happens to revision lines that cite old commits, whether the tag and the Release asset still match a rebuild, and what stays on the platform (cached views and pull request diffs cannot be rehearsed; the runbook says so). Correct the runbook where the run disagrees (G33).

**NEEDS YOU (setting):** disabling and re-enabling the sandbox ruleset, and confirming `p2-w12-target` still exists and may be rewritten.

Check: (a) the 2026-11-09 run is read and the later run is green, or the failure is a known gap; (b) the runbook is followed step by step with each command run, differences corrected in the same pull request, no command in it that does not exist (`test_runbooks.py`), G33 closed or narrowed to the platform-side steps.

### 13. Test documents, clean-up and exit (PR 5)

Work: update `../testing/`: acceptance cases `pending P3` set to `ready` or recorded with a result (FR7.1-01, FR7.3-03, FR7.4-01, FR8.1 to FR8.5, NFR1); `traceability-matrix.md`; `strategy.md` "P3 adds"; `master-test-plan.md` entry line; `known-gaps.md` (close or narrow G2, G11, G18, G21, G25, G27, G30, G33; list new gaps, including that one provider only ran the skills); delete or archive the sandbox repositories and Apps created in P2 and P3 (OD-11; the P2 todo item); run the full gate locally on Python 3.11 and 3.14 and in CI on three systems; coverage figure; propose the P4 estimate from P3 actuals in the same units; draft the `v0.5.0` tag message.

**NEEDS YOU (account):** archive or delete the sandbox repositories and Apps once the leak rehearsal is done.

Check: SPEC "Done when" 1 to 11 each ticked in `todo.md` with evidence; after the last pull request merges the owner tags `v0.5.0`, the release workflow ran on it, and "Done when" 12 is ticked.

## Effort

Estimates are for an agent-built, owner-reviewed process **[Inf]**, in hours: **agent** = active build time including test and CI iteration, **owner** = review, decisions, account and setting steps and merges.

**Basis.** (1) P2 actuals: about 54 agent hours for seven pull requests (6, 9, 5, 6, 9, 10, 9) and about 8 owner hours, in 7 calendar days, at the low end of its plan. (2) P3 has five pull requests and two sandbox rehearsals, smaller in logic than the adapters and revision writer, but with two new areas without a spike: the Zensical and MkDocs behaviour on one config (ADR-001 carried issue) and the skills. (3) Live workflow work is multiplied by 1.5 for iteration (P2 found two defects only live). (4) Owner time is 0.75–2 hours per pull request, by diff size and by how much needs judgement; the skills and `GOVERNANCE.md` are prose the owner must read closely.

**Assumptions.** One pull request reviewed per sitting; review turned around within one working day; PR 1 and PR 2 run in parallel; the sandbox Apps from P2 still exist; no second runtime is tested; no conditional proposed entry (PP-7 to PP-11) fires (otherwise add 3–6 agent hours and 1–2 owner hours for each).

| Item | Agent (h) | Owner (h) | Owner content |
| --- | --- | --- | --- |
| PR 0 plan and Q&A | done | 1–1.5 | Review three files, ODs, PPs |
| PR 1 skills and `AGENTS.md` | 5–8 | 1–1.5 | Close reading of both skills and `AGENTS.md` |
| PR 2 site stack, `mkdocs.yml`, `site.yml`, instantiation | 9–14 | 1.5–2 | Review; confirm Zensical pin and licences |
| S3a site rehearsal | 2–3 | 0.5–0.75 | Create `p3-scratch-github`, enable Pages |
| PR 3 governance files, RFC, `.idea/` | 3–5 | 0.75–1 | Read `GOVERNANCE.md` and the RFC |
| PR 4 `release.yml`, archive | 6–9 | 1–1.5 | Review |
| S3b release rehearsal, smoke runs | 2–3 | 0.5–1 | Immutable setting, choose questions |
| PR 5 stale read, leak rehearsal, test docs, exit | 5–8 | 1.5–2.5 | Ruleset toggle, clean-up, review, tag |
| **Total** | **32–50** | **7.25–11.25** (about 7–11) | |

**Calendar elapsed [Inf].** 5–8 working days, central estimate 6. The serial chain is PR 2, PR 4, PR 5 with PR 1 and PR 3 in parallel; waits are the two sandbox rehearsals and the leak rehearsal's settings. At P2's pace (one pull request a day) it could finish in 4–5 days; a turnaround of every other day stretches it to about 10. The SDD's "owner about 2 hours" for P3 counts review only; the units above include merges, settings and the rehearsals, as P2's 8 hours did (PP-1).

## Needs from you: summary

| Item | Need | Type | Blocks |
| --- | --- | --- | --- |
| All | Approve this plan; answer OD-1 to OD-15 or accept the defaults | decision | Step 1 |
| Proposed entries | Approve or reject PP-1 to PP-6 (PP-7 to PP-11 only if they fire) | decision | PP-2 before PR 2 merges; PP-3, PP-4 before PR 4; PP-5 before PR 1; PP-6 before PR 2 |
| Step 6 | Create `p3-scratch-github` (public, App installed) and enable Pages on it | account, setting | S3a |
| Step 9 | RFC-001 scope notes: decide before P4 | decision | P4 pilot |
| Step 10 | Immutable releases: on in the sandbox for S3b; on the template only after S3b and only if you accept it for `v0.5.0` | setting | S3b; the tag |
| Step 11 | Choose five questions for the `use-bundle` run; optionally run a second runtime | person | S3b |
| Step 12 | Confirm `p2-w12-target` may be rewritten; disable and re-enable its ruleset | setting | Leak rehearsal |
| Step 13 | Archive or delete sandbox repositories and Apps | account | Exit |
| Each pull request | Instruct commit, push, PR; review; squash-merge | person | Every PR |
| Exit | Push annotated tag `v0.5.0` | person | P3 exit |

## Proposed entries

PP-1 to PP-6 approved as drafted on 2026-11-11 (text shown for review when each is written); PP-7 to PP-11 are conditional. Nothing below is written until its text is shown. IDs for ADRs are assigned on approval (next is ADR-009).

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| PP-1 | Always: the P2 close-out proposes P3 "5 to 7 days, owner about 2 hours" in person-day style; the units in use since P2 are agent hours, owner hours and calendar days | SDD §14 P3 row and the executive-summary sentence that quotes effort; proposed text: agent 32–50 h, owner about 7–11 h, 5–8 working days **[Inf]**; P4 re-expressed at the P3 exit | SDD edit with a DDR change-log row |
| PP-2 | Always: `../constraints.md` "Pinned tool versions" records the lychee version but not the SHA-256 of the release asset that CI needs for a checksum-verified install | That table (lychee asset SHA-256, read from the release's checksum file) | Fill, as P2 PP-2; ADR only if the owner reads it as a change to the bar |
| PP-3 | Always: I-12 lists no file in the archive that carries the tag, so an agent given only the archive cannot report it (FR7.2), and W-08 and FR8.3 name a site "manifest" without defining one | SDD I-12 (archive gains a small `RELEASE` file: tag, commit, date, generated at build, so the archive stays reproducible), W-07 and C-10 wording; W-08 and C-07 (the site build writes `release.json` with the same fields into the site root); the golden digest is regenerated. Alternative: the user supplies the tag, no archive change | SDD edit with a DDR change-log row |
| PP-4 | Always: `release.yml` does more than W-07 states: a clean rebuild-and-compare job, a Release made as a draft then published (so an immutable Release is complete), and a pre-release mark while the major version is 0 | SDD W-07 and C-10 wording | SDD edit with a DDR change-log row |
| PP-5 | Always: ADR-002 requires an optional adapter "created by one command or task"; SDD C-04 and §6 do not list it | SDD C-04 (row for `link_skills.py`, `poe link-skills`), §6 layout, C-08 sentence | SDD edit with a DDR change-log row |
| PP-6 | Always: `init_library.py` needs behaviour W-01 does not state: it rewrites `mkdocs.yml` (name, URL, repository and edit links, issue link), removes the repository-based keys for `git-local`, and fills the placeholders in `GOVERNANCE.md` | SDD §6 "Template-only files" paragraph and W-01 step 3 (wording) | SDD edit with a DDR change-log row |
| PP-7 | Only if step 5 shows MkDocs rejects or misreads Zensical's own link keys in one `mkdocs.yml` | SDD I-13 and ADR-001's "one shared `mkdocs.yml`" (for example a second file for Zensical) | New ADR |
| PP-8 | Only if a site dependency has a licence outside the allowlist (step 4) | `../constraints.md` exceptions table | New ADR, as ADR-006 |
| PP-9 | Only if a Python-Markdown divergence (G2) makes a construct the profile allows render differently from GitHub | SDD I-01 authoring rule or the profile | RFC or ADR |
| PP-10 | Only if S3b shows the draft-then-publish flow or `gh release create` conflicts with immutable releases | SDD W-07, C-10, AD-15 | ADR |
| PP-11 | Only if a 600-concept site build exceeds 2 minutes per builder on the Linux runner (SDD §12 **[Inf]**) | SDD §12 row | ADR; the limit is not relaxed silently |

## Risks

| Risk | Effect | Response |
| --- | --- | --- |
| Zensical does not honour `mkdocs.yml` keys, and it skips unsupported settings without warning | A green build hides a broken page or link | Judge output, not exit code: page-list and lychee checks; recorded per-check expectations that fail when a release changes them |
| MkDocs and Material are past end of life (2026-11-05) | Dependency advisories land with no fix | Exact pins, `poe audit` weekly, review at P4 as ADR-001 states; accepted while sites are previews |
| One `mkdocs.yml` for two builders may not be possible | Rework of ADR-001's shared-file decision | Test early in step 5; PP-7 |
| Python-Markdown differs from markdown-it-py on a construct a library uses | A page renders differently from the validator's reading | G2 divergence study in step 5; PP-9; authoring rule |
| Immutable releases and the draft-then-publish flow are untested on a repository the owner controls | A wrong flow cannot be undone for a tag | Sandbox first (S3b); template immutability set only after it; PP-10 |
| `v0.5.0` on the template creates a real, permanent Release | A defect in `release.yml` is public | Rehearse on `p3-scratch-github` first; the owner decides immutability for the template (OD-9) |
| Skills are tested on one provider | `AGENTS.md` and skill pointers may not work on another runtime (ADR-002) | Stated as a known gap; second runtime optional (OD-13); full check in P4 |
| Leak rehearsal force-pushes a protected branch | Damage to a repository with value | Synthetic repository only (`p2-w12-target`), owner toggles the ruleset |
| GitHub dropped events in P2 (G34) | A rehearsal run does not start | Documented fix: re-label or push again |
| Release identity needs an SDD edit (PP-3) | PR 4 cannot merge until decided | Decide PP-3 early; the alternative needs no archive change |
| Scope creep into P4 (pilot, second runtime, switch to Zensical) | P3 overruns | SPEC out-of-scope list; interpretations 1 and 2 |
| The owner estimate (7–11 h) is above the SDD's 2 hours | Surprise | Stated in "Effort" and PP-1 |

## Open decisions

Each has a default that applies if the owner does not answer.

| ID | Question | Default |
| --- | --- | --- |
| OD-1 | Pull request granularity | **Decided (2026-11-11):** Five pull requests plus two sandbox rehearsals (table above); inside PR 2, four ordered commits |
| OD-2 | Do the site groups join `default-groups`? | **Decided (2026-11-11):** No; `poe install` syncs all groups, and CI installs the group each job needs |
| OD-3 | Which Zensical and Material versions? | **Decided (2026-11-11):** The latest Zensical 0.0.x and the newest Material 9.7.x at the start of PR 2, exact-pinned; the owner confirms in review |
| OD-4 | Scope notes (G6) | **Decided (2026-11-11):** RFC-001 drafted in PR 3 with a recommendation; nothing built in P3; the owner decides before P4 because the pilot needs them |
| OD-5 | Does the archive carry the tag (PP-3)? | **Decided (2026-11-11):** Yes: a `RELEASE` file in the archive and `release.json` in the site |
| OD-6 | Is the Pages deploy path proved live? | **Decided (2026-11-11):** Yes, once, on `p3-scratch-github` (synthetic, public) with `library.site_url` set and tag `v1.0.0`, then Pages is disabled; otherwise static tests only |
| OD-7 | Is `site` a required status check? | **Decided (2026-11-11):** No; `validate` is the only required check (SDD §11); a path-filtered workflow cannot be required |
| OD-8 | Is the site build time a gate? | **Decided (2026-11-11):** Recorded on Linux in `../testing/performance.md`; a breach of 2 minutes is PP-11 |
| OD-9 | `v0.5.0` on the template | **Decided (2026-11-11):** `release.yml` creates a pre-release on `open-renewables/okf-library-template`; immutability is turned on for it only if the owner decides after S3b |
| OD-10 | Missing `CITATION.cff`, `DECISIONS.md`, `GOVERNANCE.md` in the template | **Decided (2026-11-11):** `GOVERNANCE.md` is added; `CITATION.cff` and `DECISIONS.md` stay generated by `init_library`; the builder tolerates the missing `CITATION.cff` |
| OD-11 | Rehearsal repositories | **Decided (2026-11-11):** New `p3-scratch-github` (public, App installed) for S3a and S3b; `p2-w12-target` reused for the leak rehearsal; all archived or deleted at exit |
| OD-12 | `.idea/` | **Decided (2026-11-11):** Untracked and ignored (G30) |
| OD-13 | Second runtime for the skills | **Decided (2026-11-11):** Not tested in P3; stated as a known gap; the owner may run the prompts on another runtime and report |
| OD-14 | Skill evaluation | **Decided (2026-11-11):** Trigger and behaviour prompts written as data in `../testing/skill-evals.md` for P4; no model call in CI |
| OD-15 | Form of the Claude Code adapter | **Decided (2026-11-11):** `poe link-skills` copies (a link on request); `/.claude/skills/` stays git-ignored |
