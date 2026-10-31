# Plan: build phase P1

Status: **Approved by the owner on 2026-10-31:** the plan, the defaults for OD-1 to OD-10, and proposed entries PP-1 to PP-6 as drafted (ADR text is shown for review when each is written). Nothing is built. What is built and why: `SPEC.md` (abbreviations are defined there). Checklist: `todo.md`. Effort is in person-days **[Inf]**; SDD §14 allows 11–16 for P1. The steps below total **10.25–15**, and up to 1 day of contingency takes the top to the 16 allowed. The low end sits under the SDD's 11 because the steps assume no rework; the estimate is not narrowed to fit.

**NEEDS YOU** marks a step that needs a decision, person, account, machine or setting that only the owner can supply. Types: *decision*, *person*, *account*, *machine*, *setting*.

## Rules for every step

1. **Fixed inputs.** The SRS, SDD, DDR and ADR-001 to ADR-006 do not change. A step that finds a conflict stops and adds a proposed entry (below); it does not edit the document.
2. **Where work happens.** This repository, one branch per pull request, named `tooling/<slug>` (conventions, Git). No spike is planned. If one is needed, it runs only in `open-renewables-sandbox/p0-spikes` under the P0 guards (explicit repository on every `gh` call, synthetic content, nothing in `open-renewables`).
3. **No commit, push, pull request or merge** without the owner's instruction. The owner merges (squash).
4. **Check before moving on.** A step is done when its check passes with `poe check` and `poe test` green on the files it touched.
5. **Provider-neutral.** Tasks run through `uv run poe <task>`. No step creates `.claude/` or any product-specific file (ADR-002).
6. **Line endings.** Files are LF in the repository (`.gitattributes`, step 1). Edit existing CRLF working-tree files with line-ending-preserving scripts, not whole-file rewrites.
7. **Tests.** No network. Fixtures follow `../conventions.md` (`tests/library/fixtures/pass/<type>/…`, `fail/<code>/…`; tooling tests in `tests/template/`).

## Order of work and pull requests

| PR | Steps | Branch (suggested) | Days |
| --- | --- | --- | --- |
| 0 | This plan | `docs/p1-plan` | — |
| 1 | 1 Skeleton and quality bar | `tooling/p1-skeleton` | 0.75–1 |
| 2 | 2 Core reader and report; 3 Profile and schemas | `tooling/p1-core` | 1.5–2.25 |
| 3 | 4 Checks 1–2; 5 Check 3 | `tooling/p1-checks-1-3` | 2–3 |
| 4 | 6 Check 4; 7 Registry, check 6, `new_concept`, `renumber` | `tooling/p1-checks-4-6` | 2–3 |
| 5 | 8 Indexes and tiers; 9 Change rules, ownership, pre-check, warnings; 10 Entry points | `tooling/p1-indexes-changes` | 2.75–3.75 |
| 6 | 11 Example bundle (content only) | `concept/p1-example-bundle` | 0.25–0.5 |
| 7 | 12 Pre-commit and parity; 13 Test docs and catalogue; 14 Exit | `tooling/p1-exit` | 1–1.5 |

Steps run in order: each uses the previous step's module. Step 3 may be drafted in parallel with step 2. Step 11 waits for steps 8 and 10 and for PR 5 to be merged, so content is validated by merged tooling.

## Steps

Each step: work, then **Check**.

### 1. Skeleton and quality bar (0.75–1)

Work: `pyproject.toml` with groups `validate` (ruamel.yaml, markdown-it-py, mdit-py-plugins, jsonschema, PyYAML for the vendored script) and `dev` (ruff, mypy, pytest, pytest-cov, poethepoet, pre-commit); `[tool.poe.tasks]` `install`, `check`, `test`, `ci-validate` as in I-16 (tasks for scripts not yet written are added with the step that writes them); ruff rules and line length from `constraints.md`; mypy strict on `scripts/okfprofile`; pytest `pythonpath`; coverage with `fail_under = 85` and branch coverage; `.python-version` (3.12); `.gitattributes` (`* text=auto eol=lf`); `uv.lock`; `scripts/okfprofile/__init__.py` and one smoke test. Record the licence of every locked package against the allowlist.

Check: `uv sync --all-groups` on a fresh clone; `uv run poe check` and `uv run poe test` pass; `uv lock --locked` passes; the suite passes with `uv run --python 3.11` and `--python 3.14`; `git ls-files --eol` shows no `w/crlf` after a fresh clone with `core.autocrlf` both true and false; bare `poe` is not used anywhere; the licence listing has no package off the allowlist (if mypy's `pathspec` appears in `dev`, raise PP-3 before merging).

### 2. Core reader and report (1–1.5)

Work: `config` (load `profile.yaml`, validate against its meta-schema, resolve types, formats, vocabularies); `document` (first line must be `---`, YAML 1.2 by ruamel.yaml with scalar values kept as strings, body by markdown-it-py with mdit-py-plugins; expose headings, sections, list items with source line and nesting level, links, anchors, footnotes); `report` (finding model with code, level, file, line, message; JSON, GitHub-style annotations, Markdown summary); `architecture/finding-codes.md` started (PP-4). Docstrings per conventions.

Check: unit tests for each reader behaviour, including `status: no` and an unquoted date staying strings, CRLF input, nested items at two and four spaces, footnotes, `<a id>` anchors; findings render identically as JSON and as annotations; coverage and mypy strict hold.

### 3. Profile and schemas (0.5–0.75)

Work: `profile/profile.yaml` for the template's example types (default types in OD-1), `profile/schemas/` meta-schemas for `profile.yaml` and `uid-registry.yaml`, `types/okf-base.schema.json` (all keys of OKF at `ad30107`, plus `uid`) and one schema per type referencing it with `unevaluatedProperties` as I-03 specifies, `formats/` for any section format that carries items. No domain value appears in `scripts/`.

Check: the profile validates against its meta-schema; each schema validates a hand-written passing frontmatter and rejects one fixture per rule (unknown field, wrong `type` const, bad `uid` pattern, offset-less datetime, bad tag pattern); `grep` of `scripts/` finds no type name, prefix or vocabulary value (FR2.1 review).

### 4. Checks 1 and 2 (1–1.5)

Work: vendor okf-skills' `okf_validate.py` verbatim at `a8b96420…` under `scripts/vendor/okf-skills/` with the MIT licence, the Apache-2.0 notice for the specification text, and a record of commit and file hash (PP-1 for the lint exemption); check 1 imports `validate()`, maps each message to an `OKF1xx` code by section marker and text prefix (V-08 table), applies profile levels, drops the two suppressed warnings, never passes `--strict`; `okfprofile` also enforces frontmatter-first and datetime-offset (`stale_after`, `verified[].at`, declared datetime fields); check 2 validates frontmatter against the type schema with `jsonschema` and reports unknown fields when `reject_unknown_fields` is true while accepting OKF's optional keys (FR2.7).

Check: one failing fixture per code, each raising exactly that code; a test feeds every pinned message (taken from the V-08 run) through the mapper and fails on any unmapped message, so a re-pin that changes wording is caught; a concept with OKF `verified` passes with unknown fields rejected; the vendored file's hash equals upstream's at the pin; PyYAML (1.1) and ruamel (1.2) disagreeing on `status: no` does not produce contradictory findings.

### 5. Check 3: body structure (1–1.5)

Work: sections, order (`strict` or `any`), required flag, empty placeholder, title heading, formats (item pattern, enums, vocabulary groups, required children in order, I-04); CI-managed *Revision history* section: lines must match the I-08 grammar and may only be appended against the base (the base-diff part is wired in step 9; PP-6); two-space nesting in a section whose format has children is an error; angle-bracket text in prose outside code spans is flagged (I-01).

Check: one failing fixture per code; a hand-edited revision line, a deleted line and an out-of-grammar line each fail; footnote definitions after the section are left alone (FR3.4); a four-space list nests and a two-space one is flagged; coverage holds.

### 6. Check 4: links, anchors, vocabularies, paths (1–1.5)

Work: `vocab` (load vocabulary concepts, values, kinds, definitions; values unique across kinds); internal links relative only, root-relative rejected (ADR-005), spaces as `%20` or angle brackets, target must exist in `knowledge/`; anchors resolve to an automatic slug or an explicit id, fragments compared case-insensitively, explicit ids must be lower case, a duplicate explicit and automatic id is accepted if consistent, `{#id}` rejected (AD-14); glossary anchors never change (compared with the base when one is given, FR2.10); tag membership against vocabularies; the four path-rule kinds and the `tag_*` rules from I-02.

Check: one failing fixture per code; `%20` and angle-bracket links resolve (the okf-skills false warning does not surface); an upper-case `<a id>` fails; a changed glossary anchor fails; a tag missing from its vocabulary fails.

### 7. Registry, check 6, `new_concept`, `renumber` (1–1.5)

Work: `registry` (read, diff, update, next number per prefix, never reuse); check 6 (missing, malformed, duplicate, changed or absent `uid`; path differing from the registry unless the move is flagged approved and the old path recorded; deleted concept file fails, FR1.7); `new_concept.py <type> <path>` (next `uid`, required tags from the path, declared sections with placeholders, relative links); `renumber.py`; `validate_profile.py --fix-registry` for approved moves only. The approved-move signal is a flag or input file here; where it comes from on a platform is P2.

Check: one failing fixture per code; two branches taking the same number produce a duplicate on merge and `renumber.py` clears it (FR1.6 acceptance, run on local branches); `new_concept.py` output passes all checks; a hand edit that desynchronises the registry fails.

### 8. Indexes and revision tiers (1–1.5)

Work: `indexes` (one `index.md` per folder, folders then concepts sorted by title, **relative links**, status and tier on each concept line, `max_concepts_per_directory` warning, root index with `okf_version`; whole bundle or given concepts; `build_indexes.py [--check]`; check 5); pure part of `revision`: parse I-08 lines, per-revision tier, concept tier over the window since the latest owner-approved `full-review`, `human-reviewed (self)` qualifier, `Unverified` when no revision.

Check: golden index files; golden tier cases for every row of the I-08 tables, including stale approval, non-owner approval, merged without approval, `require_non_author_approver` true, and the one-line owner-approved fix to an agent-drafted concept staying Machine-confirmed; a stale or hand-edited index fails check 5; generating twice is a no-op; CRLF checkout input gives the same output.

### 9. Change rules, ownership, publishing pre-check, warnings (1.25–1.75)

Work: `changes` (classify changed paths as tooling or content using the SDD §6 list; mixed change fails `OKF0xx` unless the migration input is present; migration needs a maintainer approval input and a changed `DECISIONS.md`); `--tooling-from <ref>` (materialise that ref's `scripts/`, `profile/` and lock files in a temporary folder and run them on the working tree's content); `codeowners` (GitHub last-match-wins, owners per path, per-concept ownership, FR5.4); the publishing pre-check (OKF7xx: the three W-04 rules and the citation rule) as pure functions over supplied review data; the four warning kinds from I-02 (`tag_not_equal_segment`, `agent_label_missing`, `stable_section_nonempty`, `directory_size`), the second taking supplied markers; the base-diff for the revision section (step 5) and for removed concepts (step 7).

Check: a profile that relaxes a rule plus a non-conforming concept fails under `--tooling-from` and passes without it (FR2.5 acceptance); mixed change fails and passes with the migration input and approval (FR2.6); a pull-request fixture touching two folders records two owner statuses (FR5.4); each pre-check branch has a fixture; the warning fixtures raise warnings, not errors.

### 10. Entry points and tasks (0.5)

Work: `validate_profile.py` (`--changed`, `--base <ref>`, `--tooling-from <ref>`, `--fix-registry`, `--json`), `new_concept.py`, `renumber.py`, `build_indexes.py` as thin wrappers; non-zero exit on error, human output on stderr; poe tasks `ci-validate` and any task added by earlier steps; coverage excludes the thin scripts.

Check: each script's `--help`, `--json` and exit code have a test; `uv run poe check` runs checks 1–6 and the index check on `knowledge/` and `tests/library/fixtures/pass/`; a local run and a run through the `ci-validate` task on the same commit produce identical JSON (FR2.8, FR2.11).

### 11. Example bundle (0.25–0.5)

Work, content only, after PR 5 is merged: one example concept per declared type, vocabularies and glossary entries needed by the examples, generated indexes, registry entries; matching passing fixtures under `tests/library/fixtures/pass/`.

Check: pinned checker and profile validator report no error on `knowledge/` (FR1.1 acceptance); `build_indexes.py --check` is clean; each type has a passing fixture.

### 12. Pre-commit and parity (0.25–0.5)

Work: `.pre-commit-config.yaml` with `repo: local` hooks run through `uv run`: ruff with fixes, `validate_profile.py --changed`, `build_indexes.py --check` (the `scan.py` hook is added in P2, OD-2); a generated 600-concept bundle timed once as information, not a gate (constraint timed in P2).

Check: hooks run in Git Bash and PowerShell on this machine; a commit that breaks a rule is refused; a clean commit passes; the 600-concept time is recorded in `testing/` (target under 10 s, SDD §12).

### 13. Test documents and finding catalogue (0.5–0.75)

Work: `testing/strategy.md` (levels: unit, fixture bundle, golden file; what P2 adds), `testing/fixtures.md` (what each fixture proves), `testing/known-gaps.md` (cross-system run, Python-Markdown divergences other than nesting, unconfirmed GitHub scroll targets from V-01, hand-edit detection limits, and whatever steps found); finish `architecture/finding-codes.md` (code, level, check, message, fixture).

Check: every code in `scripts/` appears in the catalogue with a fixture path, and a test fails if one does not (constraints: every code has a failing fixture); links in the new documents resolve.

### 14. Exit (0.25)

Work: full gate on Python 3.11 and 3.14; coverage figure; revise the P2 to P4 estimate from P1 actuals (proposal, not applied); prepare the `v0.1.0` tag message.

Check: SPEC "Done when" items 1 to 8 are each ticked in `todo.md` with evidence; the owner tags `v0.1.0` (alpha) after the last pull request is merged.

## Needs from you: summary

| Item | Need | Type | Blocks |
| --- | --- | --- | --- |
| All | Approve this plan; answer OD-1 to OD-10 or accept the defaults | decision | Step 1 (OD-8); steps 3 and 8 (OD-1) |
| Proposed entries | Approve or reject PP-1 to PP-6 | decision | PP-1 before step 4 merges; PP-2 before step 8; PP-3 only if it arises in step 1 |
| Each pull request | Instruct commit, push, PR; review; squash-merge (single maintainer: recorded self-approval) | person | Every PR |
| Exit | Push the annotated tag `v0.1.0` | person | P1 exit |
| Optional | A macOS and a Linux machine, or a sandbox smoke run (OD-9) | machine | Cross-system evidence before P2 |
| Accounts, settings | None. No GitHub App, Cloudflare, symlink or Developer Mode setting is needed in P1 | — | — |

## Proposed entries

Nothing below is written until the owner approves its text. IDs for ADRs are assigned on approval (ADR-007 is drafted; next is ADR-008).

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| PP-1 | Always: `scripts/vendor/okf-skills/` is a verbatim third-party file and cannot meet the ruff, mypy and coverage limits | `../constraints.md` Code and Tests rows (an exemption for `scripts/vendor/` only) | ADR-008 (ADR-007 was taken by PP-3) |
| PP-2 | Always: SDD I-07's example uses root-relative links, which ADR-005 rejects and P1 does not emit | SDD I-07 example text (wording; no decision changes) | SDD edit with a DDR change-log row |
| PP-3 | Only if step 1 finds an MPL-2.0 package (for example `pathspec`, a mypy dependency) in the `dev` group | ADR-006 reason text and the `constraints.md` exception table | ADR-007, drafted 2026-10-31 (also resolves the `nodeenv` and `colorama` metadata) |
| PP-4 | Always: I-09 gives code ranges only, and every code needs a stable number | New file `../architecture/finding-codes.md` assigning codes within the I-09 ranges; V-08's slots are a starting point | New document; no SDD edit |
| PP-5 | Only if the owner rejects the OD-2 or OD-3 defaults | SDD §14 and C-04 placement of `scan.py`, `requirements/` export and the revision pure part | SDD edit with a change-log row |
| PP-6 | Always: FR3.4's "a hand edit fails check 3" cannot be proven from content alone; P1 uses the line grammar plus a base-branch diff | Wording of how the check works, in the finding catalogue and `known-gaps.md`; a stronger rule (for example signed lines) would change I-08 | Note in the catalogue; ADR only if the owner wants a stronger rule |
| PP-7 | Always: the example profile and schemas need parameters that SDD I-02 to I-04 do not list: `types` on a path rule (so a rule can target one type), `enum` on a format child (RE example in I-04), `publishing` as free text on a status extension, `unevaluatedProperties: false` added by the validator at load rather than stored in each type schema (equivalent to I-03), and the rule that undeclared H2 sections are allowed when a type's body `order` is `any` (settled in step 5). All are additive and optional | SDD I-02, I-03, I-04 wording (additions; no existing behaviour changes) | SDD edit with a DDR change-log row; ADR only if the owner prefers another form |

## Risks

| Risk | Effect | Response |
| --- | --- | --- |
| P1 is the largest block and no spike exercised `okfprofile` | Overrun beyond 16 | Contingency day; steps 5, 6, 9 are the widest; stop and report after PR 3 with actuals |
| 85 % branch coverage and `mypy --strict` from the first commit | Effort easy to underestimate | Tests written with each step, not at the end |
| okf-skills messages have no codes | A re-pin silently changes mapping | Pinned-message test (step 4); vendored file verbatim |
| PyYAML (vendored script) and ruamel (profile) disagree on YAML 1.1 and 1.2 values | Contradictory findings | Test in step 4; profile validator is the authority (AD-08) |
| Python-Markdown (site) differs from markdown-it-py (validator) beyond nesting | Passes locally, renders differently | Recorded in `known-gaps.md`; P3 site tests |
| Spec gaps found while building (scope notes, I-07 links) | A design question mid-step | Stop the step, add a proposed entry or open decision, continue elsewhere |
| Mixed-change rule not enforced until P2 | Tooling and content merged together by mistake | Separate PRs by discipline (OD-7) |
| Windows-only runs | Path or line-ending bugs on other systems | `.gitattributes`, CRLF tests, `pathlib` throughout; P2 matrix; OD-9 |
| Scope creep into P2 (revision writer, adapters, `scan.py`) | P1 overruns | SPEC out-of-scope list; interpretations 1–3 |
| Dev-group transitive licences off the allowlist | Constraint breach | Licence listing in step 1; PP-3 |

## Open decisions

Each has a default that applies if the owner does not answer.

| ID | Question | Default |
| --- | --- | --- |
| OD-1 | Which concept types does the template profile declare? I-07 mentions a "scope note" but the SDD defines no such type or file location | Item (`ITM`), Vocabulary (`VOC`), Glossary (`GLS`), one example each. No scope-note type; folder lines in generated indexes carry the folder title only. Revisit by RFC before P3 |
| OD-2 | Where does `scan.py` land? SDD §14 names it in neither P1 nor P2, but I-17 lists its hook | P2, with gitleaks and the CI scan jobs; the P1 pre-commit file omits that hook |
| OD-3 | Where does the revision line parser and tier derivation land, and the `requirements/*.txt` export? | Parser and tiers in P1 (step 8); `requirements/` export in P2 with CI |
| OD-4 | Map okf-skills messages, or patch the vendored script to emit codes? | Map; vendored copy verbatim (a patch would amend AD-08) |
| OD-5 | Anchor case rule: require lower-case explicit ids, or only compare case-insensitively? | Both: require lower case, and resolve fragments case-insensitively |
| OD-6 | Merge order of the open P0 archive pull request ([#8](https://github.com/open-renewables/okf-library-template/pull/8)) | Merge #8 first, then rebase this branch; the only conflict is the three plan files, resolved by keeping this branch's content under `plan/` |
| OD-7 | Example bundle with the profile in one pull request, or separate? | Separate: tooling PRs first, a content-only PR after (conventions, Git) |
| OD-8 | Pull request size | Seven PRs as in the table above |
| OD-9 | Cross-system evidence in P1 | Windows with Python 3.11 and 3.14 only; macOS and Linux in the P2 matrix; recorded as a known gap. Alternative: a sandbox smoke run in `open-renewables-sandbox/p0-spikes` |
| OD-10 | The `v0.1.0` tag | Owner pushes an annotated tag on `main`; no GitHub Release (`release.yml` is P2) |
