# Plan: build phase P4

Status: **Approved by the owner on 2026-11-19:** the plan as drafted; OD-9, OD-22, OD-23 and OD-24 answered explicitly (2026-11-17), the other open decisions on their defaults; scope kept rather than trimmed. PP-1 is P3 PP-13 (approved 2026-11-14); PP-2 to PP-14 are approved one by one when their text is shown. Nothing is built. What is built and why: `SPEC.md` (abbreviations are defined there). Checklist: `todo.md`. Effort is in **agent build hours**, **owner hours** and calendar days, as in P2 and P3; the basis is in "Effort". The SDD §14 P4 row (agent 26–37 h, owner 9–10 h, 6–9 days, P3 PP-15) is not edited here (PP-9).

**NEEDS YOU** marks a step that needs a decision, person, account, machine or setting that only the owner can supply. Types: *decision*, *person*, *account*, *machine*, *setting*.

## Rules for every step

1. **Fixed inputs.** The SRS, SDD, DDR and ADR-001 to ADR-011 do not change. A step that finds a conflict stops and adds a proposed entry (below); it does not edit the document.
2. **Where work happens.** Template changes: this repository, one branch per pull request, `tooling/<slug>` (`docs/<slug>` for plan and evidence-only changes). Pilot work: the pilot repository (OD-2), with its own pull requests, content and tooling kept apart as in any library. Destructive and live cases: scratch libraries in `open-renewables-sandbox` only, explicit repository on every `gh` call, synthetic content, nothing in `open-renewables` beyond the template's own release and settings (MTP §1).
3. **No commit, push, pull request, merge or tag** without the owner's instruction. The owner merges (squash; recorded self-approval) and pushes tags.
4. **Check before moving on.** A step is done when its check passes and `uv run poe check` and `uv run poe test` are green on the files it touched.
5. **Provider-neutral.** Workflows call only `uv run poe <task>` (AD-20); nothing product-specific is committed (ADR-002).
6. **Line endings.** Files are LF in the repository; edit CRLF working-tree files with line-ending-preserving scripts.
7. **Tests.** No network. Behaviour that cannot be tested goes to `../testing/known-gaps.md`.
8. **Defects.** A failure in the pilot or the MTP run is a defect with an MTP severity (S1 to S4, MTP §9), logged in the run folder; S1 and S2 are fixed before `v1.0.0` or carry an owner-recorded deviation. A fix is a tooling pull request on the template, then the failed case is rerun.
9. **Logging actuals.** Each pull request's and each session's agent and owner time are noted in `todo.md` when it closes; a second person's time, if one takes part, is noted separately and not counted as owner time.
10. **Live runs find what unit tests cannot** (P2 two defects, P3 three findings in S3a). Every live case is recorded with its run URL or commit.

## Order of work and pull requests

| PR | Steps | Branch (suggested) | Depends on |
| --- | --- | --- | --- |
| 0 | This plan | `docs/p4-plan` | — |
| D | 1 Dependabot #24 to #28 | Dependabot's own, or `tooling/p4-deps` (OD-12) | PR 0 |
| 1 | 2 Folder-scope header; P3 PP-13 (PP-1) | `tooling/p4-index-header` | PR 0 |
| 2 | 3 Authoring aids (`--set`, rename procedure, PP-9 warning decision deferred to step 7) | `tooling/p4-authoring` | PR 0 |
| 3 | 4 Test readiness: AT statuses, MTP decisions, parameter files | `docs/p4-test-readiness` | PR 0 |
| U | 4a User documentation (option B in `docs/guide/`, OD-22, OD-23) | `tooling/p4-user-guide` (it changes `init_library`) | PR 2 (the rename procedure) |
| RC | 5 `v0.9.0` tag | — (owner tag) | D, 1, 2, 3, U |
| P | 6 Pilot instantiation; 7 Pilot authoring (in the pilot repository) | pilot repository | RC |
| T | 8 Library-build test: the owner's real-life scenario (default); second-person timing (optional) | scenario library (owner's location) | RC |
| P | 9 Pilot on the platform: W-12, W-11, second approver, issue form, anchors, FR8.2 | pilot repository, sandbox | step 7 |
| A | 10 Traced agent run | — | step 9 (a pilot release on GitHub) |
| 4 | 11 MTP run; defect fixes (`tooling/p4-fix-<slug>`, one per defect or group) | `docs/p4-mtp-run` plus fix branches | RC, steps 8 to 10 |
| 5 | 12 Verification closure (PP-2 to PP-4, PP-9 actuals) | `docs/p4-verification` | PR 4 |
| 6 | 13 Hardening: generator default (ADR-012), versions, README, release notes, sandbox clean-up | `tooling/p4-v1` | PR 5 |
| — | 14 Exit: immutable releases on, `v1.0.0` tag, verify, archive the plan | — (owner) | PR 6 |

PR D, PR 1, PR 2 and PR 3 touch disjoint files and may run in parallel; `known-gaps.md`, `pyproject.toml` and `uv.lock` are shared, so the later pull request rebases. Steps 8 and 6 to 7 can run in parallel once the RC exists. Fixes found in step 11 land before PR 5; each fix after the RC is listed in the `v1.0.0` notes.

## Steps

Each step: work, then **Check**.

### 1. Dependabot pull requests #24 to #28 (PR D)

Work: five dev-group bumps opened 2026-11-07 (`mypy-extensions` 1.2.0, `nodeenv` 1.12.0, `coverage` 7.17.2, `virtualenv` 21.15.6, `platformdirs` 4.14.5), opened before the P3 lock changes, so each is probably stale. For each: read the diff (only `uv.lock` and the hashed `requirements/dev.txt` export should change), check the upstream release notes for a licence or behaviour change, ask Dependabot to rebase, wait for `validate` and `template-tests`. If any conflicts or the export is not regenerated by Dependabot, close all five with a comment pointing at one replacement pull request `tooling/p4-deps` made with `uv lock --upgrade-package <name>` for each and `poe export` (OD-12).

**NEEDS YOU (person):** comment `@dependabot rebase` (or approve the replacement), review and squash-merge; close superseded Dependabot pull requests.

Check: `poe licences` and `poe audit` report zero findings; `poe export --check` passes; the `validate` export is unchanged (NFR6); CI green on three systems; no Dependabot pull request older than this plan remains open.

### 2. Folder-scope header (PR 1)

Work (ADR-010; P3 PP-13, approved, applied here as PP-1): `scripts/okfprofile/indexes.py` reads an optional YAML header on a folder's `index.md` and keeps it when it regenerates the body; the root index keeps `okf_version` and may also carry `description`; the parent's folder line becomes `- [Title](folder/index.md) — <description>`, or the title alone when there is none; check 5 (`OKF5xx`) compares the generated body only and treats the header as input, and a header with a key other than `description` (and `okf_version` on the root) is a finding with its own code (named in `finding-codes.md`); a header that is not valid YAML is a finding. `new_concept.py` does not write headers; `build_indexes.py` never invents one. Fixtures: pass (header kept, line shows it; no header; root with both keys) and fail (unknown key, bad YAML, a hand-edited body under a valid header). Golden index files regenerated. `author-concept` gains two lines: write a one-sentence `description` header when creating a folder; never edit the body. `AGENTS.md` names the exception in one line. PP-1 text: the SDD I-07 example and body rule, I-02 (none needed unless the index key gains a setting; then a row), and the SRS FR4.3 sentence, which the owner writes (proposed: "Index files are generated and never edited by hand, except an optional one-line `description` header on a folder's index (ADR-010); validation checks that committed indexes match the generator's output").

**NEEDS YOU (decision):** write or approve the FR4.3 wording (requirements are the owner's); approve the SDD I-07 text when shown.

Check: fixtures and golden files pass; `OKF5xx` fires for a body edit under a valid header and not for a header edit; the template's own folders get headers and `poe check` is clean; `use-bundle` still navigates (the folder line format is the only change an agent sees); `check-skills` passes; coverage holds; a W-10 self-test run keeps headers across instantiation.

### 3. Authoring aids (PR 2)

Work: (a) `new_concept.py --set key=value` (repeatable; values are YAML scalars or flow lists; a key that the type's schema does not declare is refused before the file is written; `--json` reports them), which lets a Vocabulary get its `namespace` and closes the second half of G23. (b) A section "Rename the primary type" in `../operations/runbook-instantiate-library.md`: the files to change (`profile.yaml` type name and prefix, the type schema and its file name, example concepts and their `uid`s, the registry, `tests/library/` fixtures, `DECISIONS.md` entry), the order, and the check (`poe check`, `poe test`); a test runs the procedure on a scratch copy and passes (the `test_runbooks.py` pattern extended to a scripted run). No `init_library` question (SDD W-01 step 3 says "renamed by hand"; OD-6). (c) The PP-9 warning kind is **not** built here; step 7 records whether pilot authoring produced the D1 or D2 constructs and the owner decides then (OD-7).

Check: `--set` tests (declared key, undeclared key refused, list value, Vocabulary created with `namespace` validates); the rename test passes on a copy and the template is unchanged; `poe check` and `poe test` pass; G23 narrowed to "procedure, not a command" or closed (owner's call at step 12).

### 4. Test readiness (PR 3)

Work: in `../testing/acceptance-test-cases.md`, replace every `pending P2 PRn` and `pending P3` status with `ready` (the feature exists; cite the merged pull request) or `blocked` with a reason; mark the P4 cases `ready for P4`. Apply the MTP decisions taken in this plan: OD-AT1 to OD-AT5 (OD-10, OD-11) written into MTP §11 as decided; PE-AT-4 (new gaps) added to `known-gaps.md` only when step 11 confirms them. Fill `library-under-test.yaml` copies for the runs planned: `scratch-local` (E-LOCAL), `scratch-github` (E-GH), `pilot` (E-REAL after promotion, `destructive_allowed: false`). Write the run sheet skeleton (`run-sheet.md`) and the results report template in `../testing/runs/README.md`. Refresh `traceability-matrix.md` for ADR-010, ADR-011 and the cases added in P3.

Check: `grep -n "pending P2\|pending P3" ../testing/acceptance-test-cases.md` is empty; every case in the matrix exists in the case file and the reverse; the three parameter files name no secret, only environment variables; MTP §7 entry criteria listed with their state in `todo.md`.

### 4a. User documentation (PR U)

Added 2026-11-17 at the owner's request. Numbered 4a so later step numbers stay stable.

**What exists.** For template users: `README.md` (94 lines: features, quick start, commands, skills, site and releases, licence). In a library: a generated `README.md` (about 20 lines), `AGENTS.md` (agent-facing), `GOVERNANCE.md` (rules), and the two skills. **What is missing.** (1) The operational runbooks, `runbook-instantiate-library.md`, `-promote-to-public.md`, `-move-git-local-to-platform.md`, `-revision-writer-recovery.md` and `-remove-leaked-content.md`, live in `docs/development/operations/`. `init_library` removes all of `docs/` (SDD §6, `TEMPLATE_ONLY`), so a library loses the procedures for W-11, W-12, recovery and leak removal, which it needs after instantiation. The template README also points at the instantiation sheet there. (2) `finding-codes.md` is in `docs/development/architecture/`, so a library has no reference for the `OKF` codes its validator prints. (3) There is no human-facing guide for customising the profile (types, sections, formats, vocabularies, path rules, warnings, the primary-type rename of step 3), for authoring a concept without an agent, for the `git-local` trailers, for releases and the site, or for merging a later template tag (QA-52). Everything else the SDD describes is design text, not user guidance.

**Options (OD-22).**

| Option | Content | Kept in libraries | Agent (h) | Owner (h) |
| --- | --- | --- | --- | --- |
| A. README only | Expand the template and generated READMEs with a "where to find what" section; runbooks and finding codes stay template-only | No guide | 2–3 | 0.5 |
| **B. Library guide, essentials (recommended)** | `docs/guide/`: `index.md`; *Getting started* (routes, instantiate, first concept; the instantiation runbook moved here); *Maintaining a library* (reviews, approval and trust tiers in plain terms, releases, the site, and the promote, move, recovery and leak-removal runbooks moved here); *Customising the profile* (types, sections, formats, vocabularies, path rules, warnings, the step 3 rename); *Reference* (poe tasks, `finding-codes.md` moved here, revision-line grammar, profile keys by pointer to `profile/schemas/`) | Yes | 8–12 | 2–3 |
| C. Full guide | B plus a worked tutorial from an empty library to its first release, a human authoring guide (no agent), a contributor guide (issue forms, pull requests), *Upgrading from a later template tag*, and troubleshooting | Yes | 14–18 | 3–4 |

**Location (OD-23).** Chosen: `docs/guide/`, kept by `init_library`, which then removes only `docs/development/` (and `docs/` if it is otherwise empty). Alternatives: a top-level `guide/` folder (no change to what is removed under `docs/`, but a second documentation root); or one root `GUIDE.md` (simplest; becomes long under option C). The site stays the bundle only (`docs_dir: knowledge`); the guide is plain Markdown read on the platform or locally, and is not in the release archive (I-12, which serves consumers). `runbook-create-template-repository.md` stays template-only.

Work (option B, location `docs/guide/`): write the four parts in user terms, citing the SDD item each follows rather than restating design; move the five runbooks and `finding-codes.md` with `git mv` and re-point every link (template README, `docs/development/AGENTS.md` and README, `operations/README.md`, tests that read them); `init_library` keeps `docs/guide/` and its generated README links to `docs/guide/index.md`; `AGENTS.md` names the guide in one line; the guide's commands are covered by the `test_runbooks.py` command check; the self-test asserts the guide exists in both instantiated libraries and has no link into `docs/development/`. PP-14 for the SDD §6 change.

**One guide, two audiences (owner's clarification, 2026-11-17).** The template's guide can be turned into the new library's own guide at instantiation, as the user chooses during `init_library` (OD-24), so it is drafted as a library guide first, with the template-specific parts marked:

- **Voice.** Written about "this library" and its profile, not "the template", wherever the text is true of any library. Template-specific text (choosing a route, answering the questionnaire, "Use this template") is limited to *Getting started* and wrapped in the same `template-only` markers `AGENTS.md` already uses, which `init_library` strips.
- **Platform blocks.** Text true of one platform only sits between `platform: github` or `platform: git-local` markers; `init_library` keeps the block for the chosen platform and strips the other, so a `git-local` library's guide has no pull-request or Actions procedure (and the W-12 runbook stays, because a `git-local` library may move).
- **Placeholders.** The library's name, title, repository, maintainer, site generator and primary type appear as the placeholders `init_library` already rewrites in `README.md` and `GOVERNANCE.md`; no other value is hard-coded, and nothing names a concept type, `uid` prefix or tag namespace (the `check-skills` rule applied to the guide).
- **After instantiation.** In the library, *Getting started* becomes *How this library was created* (template tag, platform, licences, the `DECISIONS.md` DR-01 entry) plus *Working on this library* (clone, `uv sync`, first concept). A short *This library's conventions* page is left as a stub with headings (scope, folders, sources, review practice) for the owner to fill; the rest of the guide is generic and stays as is. The library may then edit the guide freely (FR6.4).
- **The user chooses: morph, copy or remove.** `init_library` asks *"Turn the template guide into this library's own guide (morph), copy it as it is (copy), or remove it (remove)?"* in the questionnaire, and reads the answers-file key `guide: morph | copy | remove`. **Morph** does what the bullets above describe. **Copy** keeps the guide as written for the template, with only the template-only markers removed and nothing rewritten; the platform blocks for both platforms stay. **Remove** deletes `docs/guide/` (and `docs/` with it), drops the guide's line from `AGENTS.md` and the generated README, and warns that the runbooks and the finding-code reference go with it. The prompt offers `morph` as the default answer; the choice is recorded in `DECISIONS.md` DR-01.

The self-test gains, for `morph` (the `github` copy) and `copy` (the `git-local` copy), so both run on every template change, and `remove` in an instantiation test on a third copy (no `docs/` left, no link to the guide in `AGENTS.md` or the README, the warning printed): for `morph`, no `template-only` or wrong-platform marker or block remains, no placeholder is unresolved, no "the template" wording outside *How this library was created*, and the conventions stub exists; for `copy`, the guide equals the template's apart from the removed markers. Adds about 2–3 agent and 0.5 owner hours to PR U.

**Decided 2026-11-17:** option B in `docs/guide/` (OD-22, OD-23). **NEEDS YOU (decision, person):** approve PP-14 when its text is shown; read the guide closely (it is what a library owner, and step 8a, will follow).

Check: the guide exists in both instantiated trees and every relative link resolves (no link into `docs/development/`); every command in it exists; `poe check`, `poe test` and `poe selftest` pass; step 8a follows the guide's *Getting started* instead of the old runbook path, and every place you had to look elsewhere is a correction to the guide.

### 5. Release candidate `v0.9.0`

Work: after PR D, PR 1, PR 2, PR 3 and PR U merge, draft the annotated tag message (what changed since `v0.5.0`, known gaps, "release candidate for v1.0.0"); the owner tags `v0.9.0` on `main`; `release.yml` publishes a pre-release; download and verify as in P3 (`sha256sum -c`, tar digest equals the manifest, `RELEASE` names the tag). Immutability stays off for the RC (OD-15).

**NEEDS YOU (person):** push the annotated tag `v0.9.0`.

Check: the four `release.yml` jobs green; archive verified; the scheduled `stale-report.yml` after the tag reports no gap against `v0.9.0`.

### 6. Pilot instantiation

Work: the pilot repository is created from the `v0.9.0` release archive as a `git-local` library (W-01 `git-local` route, OD-3), name `okf-pilot-solar-pv` (OD-2), with the answers file stored outside the repository; the owner is the maintainer and the licence choice is CC BY 4.0 content and Apache 2.0 code unless the owner says otherwise. The primary type is renamed by the step 3 procedure (OD-4: `Risk`, prefix `RSK`, sections from the RE Risk template if the owner supplies it, otherwise the template's `Description` and `Checks` plus at most two sections the owner names); the vocabularies `group` and `category` get values for the pilot's folders; the Glossary is kept; `DECISIONS.md` records the rename and the stack. Time each step and record where the procedure was unclear.

**NEEDS YOU (decision):** the pilot's name, visibility (OD-2), primary type and sections (OD-4).

Check: `poe check` and `poe test` pass in the pilot after the rename; `tests/library/` fixtures pass with the new type; the profile names no `Item` or `ITM`; `DECISIONS.md` has DR-01 and the rename entry; the rename took the recorded time (feeds G23).

### 7. Pilot authoring

Work: about 20 concepts of the primary type in two or three folders, drafted with the `author-concept` skill from sources the owner supplies or approves (RE solar PV risks, owner's own words, sources cited as footnotes; NFR5); each folder gets a scope header (step 2); vocabulary values and glossary entries added as the concepts need them (Vocabulary values by an approved change, FR2.9). Commits on `main` follow `git-local` rules: one squash commit per change with `Agent-Drafted: yes`, `Approved-by:` where the owner reviewed it, `Full-Review: yes` for a whole-concept review; `poe revision` after each. Planned tier mix (Done when 5): at least five concepts owner-reviewed and `stable` (cited; Human-reviewed (self)), most agent-drafted and Machine-confirmed, at least one left `draft` with no revision (Unverified) for AT-FR7.2-02. Two local releases: `v0.1.0` after about ten concepts, `v0.2.0` after the rest (`poe release`). Record per concept: the skill steps that needed a correction, any finding the validator raised, and every place an author wrote a list directly after a paragraph or inside a footnote (D1, D2), for OD-7.

**NEEDS YOU (person, decision):** supply or approve sources; review each concept (about 10 minutes each); decide which are `stable`; decide OD-7 (warning kind) from the D1 and D2 count.

Check: `poe check` clean; every index line shows status and tier, with all four tiers present; `poe release v0.1.0` and `v0.2.0` pass their gates and their archives rebuild to the recorded digests; `author-concept` worked without edits on the renamed type (AT-FR7.1-02), or each edit is a defect; the site builds strict with both generators on the pilot (`poe docs-build`, `poe docs-alt`).

### 8. Library-build test (V-06, FR6.1)

**8a. Default: the owner's real-life scenario.** Work: before the run, the agent reads the owner's scenario (which library, platform, licences, types, folders and first concept it needs; OD-9) and maps each need to a W-01 step, a profile setting or a known gap, so expected shortfalls are named in advance. The owner then builds the scenario's library from `v0.9.0` with the user guide's *Getting started* (step 4a; the instantiation runbook, moved there under option B or C), timing each step in the runbook's table and noting every place the sheet was unclear, a step needed knowledge the sheet does not give, or the scenario needed something the template does not offer (for example a type rename, a second vocabulary kind, a platform setting). The stop point is the same as FR6.1's: the first validated concept merged. The agent writes up the findings in the run folder; each is a defect (MTP severity), a runbook correction (`docs/p4-mtp-run`), a known gap, or, if it is the design of W-01, PP-12. Where the scenario library lives (sandbox, the owner's own organisation, or local) is the owner's choice; if it holds real content it gets only the read-only subset of later cases (MTP E-REAL).

**8b. Optional: second person.** If the owner arranges one: a person who has not built the template follows the same sheet without help on `github` (a private scratch repository in `open-renewables-sandbox`, without the App: the App and ruleset are W-11, not W-01, for a private library) and on `git-local`; the owner or agent only records times and stopping points. This is the run that meets FR6.1 as written.

**NEEDS YOU (decision, person):** name or share the scenario mapping (path or document; OD-9) and where its library lives; run the build with a timer. Optional: a second person and their GitHub account in the sandbox organisation (about 1.5 hours).

Check: 8a total at most 30 minutes to the first merged concept, every step timed, every finding classified; runbook timing table filled with the owner's row; corrections merged; FR6.1 recorded `pass` if 8b ran within 30 minutes, otherwise `partial` with the owner's acceptance and PP-4 and PP-13 decided; scratch repositories archived after.

### 9. Pilot on the platform

Work: (a) **W-12** (`../operations/runbook-move-git-local-to-platform.md`): create `open-renewables-sandbox/okf-pilot-solar-pv`, push all branches and both tags, switch `platform: github` in one tooling pull request, `setup_repo.py`, rebuild each past archive from its tag and upload it as a Release only if its SHA-256 equals the tag message (G32: several tags; a deliberately wrong digest on a scratch copy is refused). (b) **W-11** if the pilot is public (OD-2): promote, App installed, `rules.revision_token: github-app`; the next revision run uses the App token (G32). (c) **Second directory owner, only if a second GitHub account exists** (G35, OD-9): CODEOWNERS gives that account one folder; it approves a change to a concept in it (`approved @<second> (owner)`) and merges one pull request of the owner's without an approval (`merged without approval @<second>`); both lines match I-08 (AT-FR3.5-01 in full). Without one, AT-FR3.5-01 stays `partial` on the App-approval and recorded-fixture fallback and G35 stays open. (d) **Issue form** (FR5.3, AT-FR5.3-01): a person who does not use git, or by default the owner in the browser without git, submits `new-concept.yml`; the agent turns it into a pull request with `new_concept.py`, the issue closes on merge. (e) **Anchors** (G3, V-01, AT-FR2.10-02): glossary terms with a plain, a non-ASCII and a parenthesised name; on github.com click each link from a concept and record where the page lands. (f) **FR8.2 on the pilot bundle** with both generators (AT-FR8.2-01 to -03), and the ADR-001 criterion judged on it (input to OD-13). (g) A pilot release `v0.3.0` on GitHub through `release.yml` for step 10 (OD-19).

**NEEDS YOU (account, setting):** create the pilot repository (or allow the agent to), install the sandbox App on it; for (c), only if you have one, a second account added as collaborator and its two actions; for (d) submit the form from the browser (or ask someone); for (e) a browser check (the agent can do it in the built-in browser if the owner allows the site).

Check: each sub-step recorded with its run URL; revision lines for (c) equal the I-08 grammar; G32 and G35 closed or narrowed; G3 closed, or the placement that fails is a known gap and an SDD placement rule is proposed (PP-11); the six checks recorded per generator.

### 10. Traced agent run (FR7.2)

Work: a fresh agent session with no other context is given the pilot `v0.3.0` archive (downloaded and verified) and `AGENTS.md` from it, and the `use-bundle` skill in it; the reviewer asks eight questions (at least two that need two folders, one whose best answer is the Unverified concept, one outside the bundle). The reviewer checks every cited `<uid>@<tag>` exists at the tag, and that status and tier match the index line (`(self)` kept). AT-FR7.2-02: the agent must say the draft concept is unverified. Optional: the same prompts on a second runtime (OD-16, G38). Record the transcript location (not committed; OD-AT3) and a summary in the run folder.

**NEEDS YOU (person):** choose the eight questions; act as reviewer, or name one (MTP §10: not the author of the content where there is a choice).

Check: 100 % of citations trace; no Unverified or Machine-confirmed concept described as reviewed; the out-of-bundle question answered "not covered"; a miss is a defect against the skill, fixed and rerun.

### 11. Master Test Plan run (PR 4 and fix pull requests)

Work: MTP phases 1 to 5 by hand (OD-11), evidence in `../testing/runs/2026-11-<dd>-scratch-local/`, `-scratch-github/` and `-pilot/`. Phase 1 smoke on all three; phase 2 full local on E-LOCAL (Windows by hand; macOS and Linux by the CI matrix, OD-AT5); phase 3 live on E-GH, run by the owner with the agent preparing each case (OD-10), including the adversarial AT-FR2.5-03 on the scratch repository (OD-17; PP-5 if the required check passes); phase 4 release and rehearsals (FR7.3, FR7.4, V-12 digests on three systems by CI, FR6.4 merge of a later template tag into a library created by clone: `v0.5.0` to `v0.9.0`); phase 5 links steps 8 to 10. Each failure is a defect with a severity; S1 and S2 are fixed in `tooling/p4-fix-<slug>` pull requests and rerun; S3 and S4 are fixed or added to `known-gaps.md`. The results report states pass, partial, fail, blocked per case and the owner's acceptance of each `partial`.

**NEEDS YOU (person, decision):** run the live cases (OD-10); accept or reject each `partial`; decide S2 deviations, if any.

Check: every FR and NFR criterion has a result; no open S1 or S2; the traceability matrix carries the results; new gaps listed (PE-AT-4).

### 12. Verification closure (PR 5)

Work: V-01 to V-13 each set to closed with evidence: V-01 by step 9 (e); V-05 already closed in P2 S1 (recorded); V-06 by step 8 (by the owner's scenario build, recorded as such, unless 8b ran; PP-13); V-07 parts carried as not applicable (OD-14); the others answered in P0 and re-run in step 11. SDD §13: each row's verification marked done with the case IDs. Proposed entries PP-2 (SDD §15 outcome column and §14 carried-items table; DDR change-log row, since the DDR is where the gate says outcomes are recorded), PP-3 (MTP named in SDD §13 and §14), PP-4 (SRS wording, owner) shown for approval. `known-gaps.md`, `strategy.md` "What P4 adds", `master-test-plan.md` status line updated. P4 actuals recorded (PP-9).

**NEEDS YOU (decision):** approve PP-2 and PP-3; decide PP-4 (your wording).

Check: SDD §14 gate items each have evidence in `todo.md`; no V-item is open; `test_runbooks.py` and `poe check` pass on the edited documents.

### 13. Hardening for `v1.0.0` (PR 6)

Work: (a) **Default site generator** (ADR-011, OD-13): evidence from step 9 (f), the Zensical release history since 0.1.1, the Material end-of-life exposure (`poe audit` results since 2026-11-05); ADR-012 records the decision either way (PP-10). (b) **Versions** (OD-18): `pyproject.toml` `version = "1.0.0"`, the template profile `template_version: 1.0.0` and `profile_version` reviewed; a test that the two agree, so the next release cannot drift. (c) **README**: status line from beta to stable; the known gaps that a library owner should know (G35 if still partial, FR6.1 timed by the owner only if no second person ran it, G38, G39). (d) **Release notes**: the `v1.0.0` tag message draft (changes since `v0.5.0`, fixes after the RC, known gaps, how to verify). (e) **Sandbox clean-up** (OD-20): archive `p3-scratch-github`, `p0-spikes` and the step 8 (if in the sandbox) and step 11 scratch repositories; the pilot is archived after `v1.0.0`; delete the sandbox App's private key and uninstall it once no rehearsal needs it. (f) `poe check`, `poe test` on 3.11 and 3.14 and CI on three systems on the PR 6 head.

**NEEDS YOU (decision, account):** decide OD-13; archive repositories and uninstall the App.

Check: ADR-012 accepted; the version test passes; README has no "beta"; the tag message drafted in `todo.md`; full gate green.

### 14. Exit

Work: the owner turns on immutable releases for `open-renewables/okf-library-template` (a setting with no API call, G26; OD-15) and pushes the annotated tag `v1.0.0` on the PR 6 merge commit; `release.yml` publishes a release that is not marked pre-release; download and verify (`sha256sum -c`, tar digest, `RELEASE`, `use-bundle` present); confirm an asset cannot be deleted (G39 restated: the Release record itself can be). Then, on the owner's instruction, move the plan files to `plan/archive/2026-11-p4-pilot-hardening/`, re-point links, and ask the owner to set the SRS to `Done` (OD-21).

**NEEDS YOU (setting, person):** immutable releases on; push `v1.0.0`; set the SRS status.

Check: SPEC "Done when" 1 to 13 ticked with evidence; the release is immutable and verified.

## Effort

Estimates are for an agent-built, owner-reviewed process **[Inf]**, in hours: **agent** = active build and run time including test and CI iteration; **owner** = review, decisions, account and setting steps, live cases, concept review and merges. A second person's time (about 1.5 hours, optional) is not counted.

**Basis.** (1) P3 actuals: about 36 agent hours, 7 owner hours, 4 days, inside its plan; P2 54, 8 and 7. (2) The SDD §14 P4 row (P3 PP-15) was built from those actuals before this plan listed the MTP run, the Dependabot pull requests, the RC, the pilot move by W-12 and W-11, the second-approver and issue-form cases, and the verification paperwork. (3) Concept authoring is the largest uncertainty: 20 concepts at 25–35 agent minutes and about 10 owner minutes each, plus review rounds. (4) The MTP has about 150 cases; most are `[T]` test selections or short scripted runs, but phase 3 is live and slow. (5) Live work is multiplied by 1.5 for iteration, as in P3.

**Assumptions.** One pull request reviewed per sitting; review within one working day; the scenario mapping exists and needs no rework; no second person (8b adds about 0.5 agent and 0.5 owner hours); the sandbox App still exists; no second runtime; no S1 defect (an S1 adds 3–6 agent hours and 1 owner hour each).

| Item | Agent (h) | Owner (h) | Owner content |
| --- | --- | --- | --- |
| PR 0 plan and Q&A | done | 1–1.5 | Review three files, ODs, PPs |
| PR D Dependabot | 0.5–1 | 0.25–0.5 | Rebase comments, merges |
| PR 1 folder-scope header, PP-1 | 3–4 | 0.5–0.75 | FR4.3 wording, review |
| PR 2 authoring aids | 2–3 | 0.5 | Review |
| PR 3 test readiness | 2–3 | 0.25 | Review |
| PR U user documentation (option B, morphed into the library's guide) | 10–15 | 2.5–3.5 | Read the guide closely, in the template and in an instantiated library |
| RC `v0.9.0` | 0.5 | 0.25 | Tag |
| Steps 6 and 7 pilot instantiation and 20 concepts | 10–15 | 3.5–5 | Names, type, sources, concept reviews |
| Step 8 library-build test (owner's scenario) | 1–1.5 | 1.5–2 | Share the scenario, run the timed build, classify findings |
| Step 9 pilot on the platform | 3–5 | 1–1.5 | Repository, App, collaborator, browser check |
| Step 10 traced agent run | 2–3 | 1 | Questions, review the trace |
| PR 4 MTP run and fixes | 6–10 | 1–1.5 | Live cases, partial acceptance |
| PR 5 verification closure | 2–3 | 0.5–0.75 | PP-2 to PP-4 |
| PR 6 hardening and step 14 exit | 3–4 | 1–1.5 | Generator decision, settings, tag, clean-up |
| **Total** | **45.5–68.5** (about 46–69) | **14–20** | |

Against the SDD §14 P4 row (26–37 agent, 9–10 owner) this is higher by about 20–32 agent and 5–10 owner hours, from the items listed in basis (2) and the user documentation added on 2026-11-17 (option B, with the guide morphed into each library's own; option A would take 6–9 agent and 1.5–2.5 owner hours off, option C would add 6 agent and 1 owner hour). Two ways to close the gap: accept the bottom-up figures (PP-9 edits the row), or trim: run only the MTP cases not already proved live in P2 and P3 (saves about 3–4 agent hours) and author 12 concepts instead of 20 (saves about 4 agent and 1.5 owner hours). The default is to keep the scope and propose PP-9.

**Calendar elapsed [Inf].** 9–13 working days, central estimate 11. Serial chain: PR 1 and PR 2, PR U, the RC, pilot authoring (review rounds), pilot on the platform, the traced run, the MTP fixes, PR 5, PR 6, tag. The scenario build runs in parallel with authoring; concept review rounds are the most likely delay. At P3's pace (one pull request a day plus parallel sessions) about 8 days.

## Needs from you: summary

| Item | Need | Type | Blocks |
| --- | --- | --- | --- |
| All | Approve this plan; answer OD-1 to OD-24 or accept the defaults | decision | Step 1 |
| Proposed entries | PP-1 (FR4.3 wording is yours), PP-2, PP-3, PP-8, PP-10 always; PP-14 (option B chosen); PP-4 and PP-6 your wording; PP-5, PP-7, PP-11, PP-12, PP-13 only if they fire; PP-9 for the effort row | decision | PP-1 before PR 1 merges; PP-8 before PR 2; PP-2 to PP-4 before PR 5; PP-10 before PR 6 |
| Step 1 | `@dependabot rebase` or approve a replacement; merge | person | RC |
| Step 4a | PP-14; close reading of the guide (option B in `docs/guide/` decided 2026-11-17) | decision, person | RC |
| Step 5 | Push `v0.9.0` | person | Pilot, timing |
| Step 6 | Pilot name, visibility, primary type and sections | decision | Step 6 |
| Step 7 | Sources; review about 20 concepts; choose which are `stable`; OD-7 | person, decision | Step 9 |
| Step 8 | The scenario mapping and where its library lives; the timed build. Optional: a second person and their sandbox account | decision, person | Gate |
| Step 9 | Pilot repository, App installed; the issue form submitted; anchor check in a browser; a second account's approval and merge only if you have one | account, setting, person | Steps 10, 11 |
| Step 10 | Eight questions; a reviewer | person | Gate |
| Step 11 | Run the live cases; accept partials; decide deviations | person, decision | Gate |
| Step 13 | Default generator (OD-13); archive sandbox repositories; uninstall the App | decision, account | Exit |
| Step 14 | Immutable releases on; push `v1.0.0`; set the SRS to `Done` | setting, person | Exit |
| Each pull request | Instruct commit, push, PR; review; squash-merge | person | Every PR |

## Proposed entries

Nothing below is written until its text is shown and approved. IDs for ADRs are assigned on approval (next is ADR-012).

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| PP-1 | Always: P3 PP-13, approved 2026-11-14, applied when the header is built (step 2) | SRS FR4.3 (the owner's wording); SDD I-07 example and body rule, I-02 only if a setting is added; `author-concept` and `AGENTS.md` lines | SRS edit by the owner; SDD edit with a DDR change-log row |
| PP-2 | Always: the gate says V-01 to V-13 closed "with outcomes recorded in the DDR"; SDD §15 still shows V-05, V-06, V-07 partly answered or carried and V-01 without the GitHub scroll check | SDD §15 outcome column (V-01, V-05, V-06, V-07) and §14 carried-items table; a DDR change-log row listing each closure | SDD edit with a DDR change-log row |
| PP-3 | Always (MTP PE-AT-2): SDD §13 and §14 do not mention the Master Test Plan | SDD §13 verification column ("see the acceptance matrix"); §14 P4 row ("run the Master Test Plan") | SDD edit with a DDR change-log row |
| PP-4 | Always (MTP PE-AT-3): FR3.4, FR3.8, FR6.1 cannot be tested as written; FR6.4, FR8.5 and NFR5 have no criterion | SRS wording, the owner's: FR3.4 "a hand edit that breaks the line grammar or removes a line fails; authorship is not tested"; FR3.8 "a reader implementing the V-11 rule derives the same tier"; FR6.1, if no second person runs it, for example "a person creates a library for a real scenario and merges a first validated concept in under 30 minutes, timed per step"; otherwise "a second person who has not built the template" | Owner decision; no edit by the agent |
| PP-5 | Only if AT-FR2.5-03 shows the required `validate` check passing on a pull request that edits `validate.yml` (MTP PE-AT-5) | SDD AD-18 or C-05: for example a code-owner review required on `.github/`, or the check run from the base | New ADR; the defect is S1 |
| PP-6 | Optional (MTP PE-AT-1): "AT" is a new ID scheme | `../conventions.md` abbreviation list | Owner edit; a DDR change-log row |
| PP-7 | Only if OD-7 chooses to build a warning for the D1 and D2 divergences | SDD I-02 warning-kind table (a new kind, for example `list_needs_blank_line`); `finding-codes.md` | SDD edit with a DDR change-log row |
| PP-8 | Always, with step 3: `new_concept.py` gains `--set`; the primary-type rename becomes a documented procedure | SDD C-04 `new_concept.py` row (one clause); W-01 step 3 ("renamed by hand (known gap G23)" becomes "renamed by the procedure in `runbook-instantiate-library.md`") | SDD edit with a DDR change-log row |
| PP-9 | Always at exit, and now if the owner accepts the bottom-up estimate | SDD §14 P4 row (plan figures now; actuals at exit) and the §1 effort sentence | SDD edit with a DDR change-log row |
| PP-10 | Always: ADR-011 says the default is revisited before `v1.0.0` | ADR-012 (keep `mkdocs`, or switch to `zensical`); if switched, SDD C-07, I-02 default and AD-13 status line, `init_library` default | New ADR; SDD edit if switched |
| PP-11 | Only if step 9 (e) shows GitHub does not scroll to an `<a id>` in a placement the profile allows | SDD I-01 or AD-14: a placement rule for explicit anchors | SDD edit, or ADR if AD-14 changes |
| PP-12 | Only if the `github` timing exceeds 30 minutes because of a W-01 step as designed (for example the App) | SDD W-01 (move the step, or mark it W-11 only) | SDD edit with a DDR change-log row; FR6.1 is not relaxed |
| PP-13 | Only if no second person runs step 8b: the SDD §14 v1.0.0 gate says "a second person instantiates a library in under 30 minutes" and V-06 says "Second person performs W-01" | SDD §14 gate bullet and §15 V-06 (for example "a timed instantiation against a real-life scenario, by the owner or a second person"); FR6.1 itself is PP-4, the owner's | SDD edit with a DDR change-log row, or an owner-recorded deviation at the gate |
| PP-14 | Unless OD-22 is option A: SDD §6 says `init_library` removes `docs/`, and lists the runbooks and finding codes under `docs/development/` | SDD §6 layout (`docs/guide/` kept in libraries; runbooks and `finding-codes.md` moved there) and the template-only paragraph (`docs/development/`, not `docs/`); W-01 step 3 and C-04 `init_library.py` (it asks whether to morph, copy or remove the guide, OD-24); `../AGENTS.md` and `../README.md` paths. AD-21 is unchanged: development documentation stays template-only | SDD edit with a DDR change-log row; an ADR only if you read it as amending AD-21 |

## Risks

| Risk | Effect | Response |
| --- | --- | --- |
| The owner's scenario build is not a test by a person new to the template | It understates the time and the places a newcomer would stop | Note every point where knowledge outside the sheet was used; FR6.1 recorded `partial` unless 8b runs; PP-4, PP-13 |
| The user guide drifts from the SDD and the scripts | A library owner follows a wrong procedure | The guide cites SDD items rather than restating design; its commands and links are tested; step 8a reads it as a user would |
| No second GitHub account | G35's two approval cases stay on fixtures | Known gap at `v1.0.0`, named in the README; closes when a second maintainer joins |
| Concept authoring and review take longer than planned | P4 overruns | Review in batches of five; trim to 12 concepts if the owner chooses (Effort) |
| Pilot content is public in the sandbox (OD-2) | RE content becomes public before the RE library exists | Visibility is the owner's choice; private skips the ruleset half of W-11 and G35's code-owner enforcement, not the recording |
| The primary-type rename by hand breaks something the tests do not cover | The pilot needs repair, G23 harder than thought | Run the step 3 procedure on a scratch copy first (its test); time it |
| The MTP's ~150 cases by hand take longer than 6–10 hours | Overrun | Phase 1 and the `[T]` cases first; cases already proved live in P2 and P3 cite that evidence instead of rerunning (owner may choose this trim) |
| An S1 defect is found late (for example PE-AT-5) | `v1.0.0` slips | Run AT-FR2.5-03 early in step 11; PP-5 |
| GitHub dropped events (G34) | A live case stalls | Push again; record |
| Zensical pre-1.0 changes between the RC and `v1.0.0` | The comparison build changes | Exact pin; Dependabot pull requests for it are reviewed, not auto-merged |
| Material for MkDocs past end of life | An advisory with no fix | `poe audit` weekly; ADR-012 decides the default with that evidence |
| Immutable releases cannot be undone for a tag | A defect in `v1.0.0` assets is permanent | RC first; immutability on only for `v1.0.0`; the archive is rebuilt and verified by `release.yml` before publish |
| The bottom-up estimate is above the SDD row | Surprise | Stated here and in PP-9 |

## Open decisions

Each has a default that applies if the owner does not answer.

| ID | Question | Default |
| --- | --- | --- |
| OD-1 | Pull request granularity | Seven template pull requests (0, D, 1 to 6) plus fix pull requests from step 11; pilot work in the pilot repository |
| OD-2 | Pilot location, name and visibility | `open-renewables-sandbox/okf-pilot-solar-pv`; public after W-11 so the ruleset and code-owner rules apply (GitHub Free); archived after `v1.0.0`; no Pages site |
| OD-3 | Pilot path | Start `git-local` from the `v0.9.0` archive, two local releases, then W-12 to GitHub and W-11 (SDD §13 FR6; G32) |
| OD-4 | Pilot primary type and sections | Rename `Item`/`ITM` to `Risk`/`RSK` by the step 3 procedure; sections from the RE Risk template spec if you supply it, otherwise `Description`, `Checks` and up to two you name |
| OD-5 | Pilot content and review depth | 20 RE solar PV risks, drafted with `author-concept` from sources you approve; you review every concept; at least five made `stable` by an owner `full-review`; one left `draft` and Unverified |
| OD-6 | G23 form | `new_concept.py --set` built; the rename is a tested runbook procedure; no `init_library` question |
| OD-7 | PP-9 warning kind for D1 and D2 | Decided after step 7: build only if pilot authoring wrote D1 or D2 at least once and the validator did not catch it; otherwise the authoring rule stands and the warning is post-v1.0.0 |
| OD-8 | Release candidate | Yes: `v0.9.0` pre-release after PR D to PR 3, not immutable |
| OD-9 | How the library build is tested, and whether a second person or account takes part | **Owner's instruction 2026-11-17:** the owner builds a library against a mapped-out real-life scenario, timed per step (8a); a second person is optional (8b). Default: no second person and no second account; FR6.1 `partial` with PP-4 and PP-13; G35 stays a known gap; the owner submits the issue form from the browser |
| OD-10 | Who runs the live cases (MTP OD-AT1) | You run phase 3 in the sandbox with the agent preparing each case; the agent runs phases 1, 2 and 4; AT-FR2.6-02 and AT-FR3.5-01 run on their fallbacks and are `partial` unless a second account exists |
| OD-11 | MTP harness and run options (OD-AT2 to OD-AT5) | No harness for `v1.0.0` (cases by hand; harness after `v1.0.0`); raw logs not committed; the pilot gets the read-only subset after promotion; CI matrix evidence is enough for macOS and Linux |
| OD-12 | Dependabot #24 to #28 | Rebase and merge each if green and only `uv.lock` and `requirements/dev.txt` change; otherwise close all five and replace with one `tooling/p4-deps` pull request |
| OD-13 | Default site generator for `v1.0.0` | Keep `mkdocs` as the template default (proven on every change; Zensical is pre-1.0), recorded in ADR-012 with the step 9 evidence; you may switch |
| OD-14 | V-07 remaining parts | Closed as not applicable: no library wants a private preview or private immutable release; reopened if one does |
| OD-15 | Immutable releases on the template | Off for `v0.9.0`; turned on immediately before the `v1.0.0` tag (P3 OD-9) |
| OD-16 | Second runtime for the skills (G38) | Not run; G38 stays a known gap at `v1.0.0` and is named in the README; you may run the step 10 prompts on another runtime |
| OD-17 | Where the adversarial AT-FR2.5-03 runs | A scratch GitHub library in the sandbox, never the pilot or the template |
| OD-18 | Version fields | Set by hand to `1.0.0` in PR 6, with a test that `pyproject.toml` and the template profile agree; no release-gate change |
| OD-19 | Pilot release used for the agent run | `v0.3.0` on GitHub through `release.yml`, after W-12 and W-11; immutability on for the pilot only if you want to rehearse it once more |
| OD-20 | Sandbox clean-up | Archive `p3-scratch-github` and `p0-spikes` now (P3 decision); keep the App for the pilot; archive the scratch and pilot repositories and uninstall the App at P4 exit |
| OD-21 | SRS status and upstream engagement | After `v1.0.0` you set the SRS to `Done`; the OKF upstream issue and validator contribution are after `v1.0.0` and outside this plan |
| OD-22 | User documentation scope (step 4a) | **Decided (owner, 2026-11-17):** option B, a library guide with the essentials, the five runbooks and the finding-code reference moved into it |
| OD-23 | User documentation location | **Decided (owner, 2026-11-17):** `docs/guide/`, kept by `init_library`, which then removes only `docs/development/` |
| OD-24 | Does `init_library` turn the template's guide into the library's own guide? | **Decided (owner, 2026-11-17):** the user selects during `init_library`: `morph` (template-only text stripped, the chosen platform's blocks kept, placeholders rewritten, *Getting started* becomes *How this library was created*, a conventions stub added), `copy` (unchanged apart from the markers) or `remove` (no guide; links to it dropped). Answers-file key `guide`; the prompt offers `morph` as its default |
