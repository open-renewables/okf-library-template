# Acceptance test cases

The cases of the [Master Test Plan](master-test-plan.md), grouped by requirement. Each case is written so that a person or any agent can run it from this page alone. [traceability-matrix.md](traceability-matrix.md) maps every criterion to its cases; [acceptance-templates.md](acceptance-templates.md) holds the blank case, run sheet and report.

## How to read a case

- **ID** is `AT-<requirement>-nn`. `<requirement>` is an SRS requirement (`FR2.5`, `NFR6`) or, for performance, the SDD section (`SDD12`).
- **Kind**: `scripted` (a command or test with an exact expected result), `live` (needs the hosting platform), `human` (a person or an agent follows the steps and a person judges the result), `review` (a person reads files against a stated checklist).
- **Mode**: `RO` read-only, runnable on a real library; `D` destructive, scratch libraries only (`destructive_allowed: true` in the [parameter file](library-under-test.yaml)). A case that needs a change to a read-only library works on a temporary copy and is then `RO`.
- **Pre**: `L` library under test (LUT) validates clean at the start (`V` below exits 0). `S` scratch library, one fresh library per `D` case unless the case says it reuses another's state. `G` platform `github` with the sandbox token and a scratch repository in `open-renewables-sandbox`. `T` a checkout of the template at the tag under test. `A2` a second GitHub account (open decision OD-AT1; without it the case runs on its stated fallback and the result is `partial`).
- **Steps** are `command → expected result`, run from the library root. `V` = `uv run python scripts/validate_profile.py --json`. `<type>`, `<prefix>`, `<ns>` and every path are read from the LUT's `profile.yaml` (`types[]`, `uid_prefix`, `vocabularies.namespaces[]`); nothing is hard-coded. `<c>` is a concept the case has just made. Commands marked `[T]` run in the template checkout, not in a library, because `tests/template/` is removed at instantiation (unless `--keep-tests`).
- **Evidence** codes: `E1` command output saved as `logs/<ID>.txt`; `E2` findings JSON; `E3` URL or screenshot of the platform object; `E4` `git log`/diff excerpt; `E5` timing sheet. Files go under the run folder named in the plan.
- **Status**: `ready`, or `pending P2 PRn` / `pending P3` / `pending P4` (the feature, task or workflow it needs is not built yet). Of P2 only PR 1 (supply-chain tasks, `scan.py`) is merged; `write_revision`, `stale_report`, `build_bundle`, `release`, `init_library`, `setup_repo`, `poe selftest`, the workflows and the docs tasks are pending and are named here only as the plan names them (`../plan/archive/2026-11-p2-ci-governance/plan.md`).
- Where a scenario is already defined by a P2 rehearsal (`../plan/archive/2026-11-p2-ci-governance/plan.md` steps 1, 12, 14, 15), the case adopts it by link and adds only the expectation and evidence. Finding codes are in [finding-codes.md](../architecture/finding-codes.md); fixtures in [fixtures.md](fixtures.md); gaps in [known-gaps.md](known-gaps.md).

## FR1 Knowledge bundle and identifiers

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR1.1-01 | scripted | RO | L | `V` → exit 0, no error-level finding, none in `OKF1xx` | E2 | ready |
| AT-FR1.1-02 | scripted | D | S | For each `<type>`: `uv run python scripts/new_concept.py <type> <path>`; then `V` → zero errors; each file sits at `knowledge/<path>.md` and its concept ID is the path | E2 | ready |
| AT-FR1.2-01 | scripted | RO | T | `[T]` `uv run pytest tests/library/test_fixtures.py -q -k OKF1` → every `OKF1xx` fixture passes (fixtures.md, OKF101 to OKF120) | E1 | ready |
| AT-FR1.2-02 | scripted | D | S | In `<c>`: (a) move the frontmatter opener to line 2; (b) set a datetime key (for example `stale_after`) to `2027-01-01T00:00:00` with no offset; `V` after each → (a) `OKF101`, (b) `OKF120` | E2 | ready |
| AT-FR1.3-01 | scripted | D | S | New `<c>` → `uid` is `<prefix>-` plus four digits. Then, one at a time and restoring between: remove `uid`; set `ZZZ-1`; copy another concept's `uid`; commit then change `uid` and run `V --base HEAD~1` → `OKF601`, `OKF602`, `OKF603`, `OKF606` | E2 | ready |
| AT-FR1.3-02 | scripted | D | S | New `<c>` (uid n); set its `status: deprecated`; create another of the same type → new uid is above n, never n; repeat after deleting the registry entry of the deprecated one with `V` → `OKF608`/`OKF607`, and still no reuse | E2 | ready |
| AT-FR1.3-03 | scripted | RO | T | `[T]` `uv run pytest tests/template/test_registry.py -q` → passes, and a test names the 9,999 cap. If no test names it, record a defect (S3) | E1 | ready |
| AT-FR1.4-01 | scripted | D | S | Edit `profile/uid-registry.yaml` by hand (change a path; remove an entry; add an entry for no concept); `V` after each → `OKF605`, `OKF604`, `OKF608`; `new_concept.py` and `renumber.py` leave the registry valid | E2 | ready |
| AT-FR1.5-01 | scripted | D | S | In a git scratch repo with a base commit, then `V --base HEAD~1`: (a) move `<c>` without a label → `OKF605`; (b) same with `--label approved-move --fix-registry` → exit 0 and the registry gains `moved_from`; (c) delete `<c>` → `OKF607`; (d) change its `uid` → `OKF606`; (e) remove its `uid` → `OKF601` | E2 | ready |
| AT-FR1.5-02 | live | D | G | PR that moves a concept: without the `approved-move` label the `validate` check fails with `OKF605`; adding the label and re-running passes. Adopts plan step 12 | E3 | pending P2 PR6 |
| AT-FR1.6-01 | live | D | G | Two branches each run `new_concept.py` for the same type, both squash-merge. Expected: `validate` on `main` fails `OKF603`; one `validation-failure` issue opens; `uv run python scripts/renumber.py <later concept>` in a PR clears it. Adopts plan step 15(a) (duplicate uid) | E3 | pending P2 PR6 |
| AT-FR1.6-02 | scripted | D | S | Same scenario in a `git-local` scratch repo (two branches merged by `git merge --squash`): `V` on `main` → `OKF603`; `renumber.py <later concept>`, `uv run python scripts/build_indexes.py`, `V` → exit 0 | E2 | ready |
| AT-FR1.7-01 | scripted | D | S | Commit `<c>`, delete the file and its registry entry, `V --base HEAD~1` → `OKF607`; restore and set `status: deprecated` instead → exit 0 | E2 | ready |

## FR2 Profile and validation

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR2.1-01 | scripted | D | S | Add a type by profile only: new entry in `profile.yaml` `types[]` (new `uid_prefix`), a schema in `profile/types/`, then `new_concept.py <newtype> <path>` and `V` → exit 0; `git diff --stat -- scripts` is empty | E2, E4 | ready |
| AT-FR2.1-02 | review | RO | T | For each type name, prefix and vocabulary namespace in `profile.yaml`: `grep -rnw "<name>" scripts/okfprofile` → no match outside comments and docstrings; any match is judged by the reviewer and recorded | E1 | ready |
| AT-FR2.2-01 | scripted | RO | T | `[T]` `uv run pytest tests/template/test_catalogue.py tests/library -q` → passes: every code has a catalogue row and a failing fixture, and checks 1 to 6 each have one (fixtures.md) | E1 | ready |
| AT-FR2.2-02 | scripted | D | S | Plant one fault per check in six concepts (1: `OKF120`; 2: unknown field; 3: sections out of order; 4: unknown tag value; 5: edit an `index.md`; 6: duplicate uid); `V` → findings in each of `OKF1xx`, `OKF2xx`, `OKF3xx`, `OKF4xx`, `OKF5xx`, `OKF6xx` | E2 | ready |
| AT-FR2.3-01 | scripted | D | S | With the AT-FR2.2-02 faults, `V` and `V --annotations` → every finding has `code`, `level`, `file`, `line`; annotations read `::error file=…,line=…::`; exit code non-zero | E2 | ready |
| AT-FR2.4-01 | live | D | G | Open a PR with a failing concept → `validate` fails; fix it → passes; submit an approving review → `validate` re-runs (Actions run list shows a `pull_request_review` run with the same job name) | E3 | pending P2 PR6 |
| AT-FR2.4-02 | live | D | G | Admin-bypass merge a failing commit to `main` → one issue labelled `validation-failure` opens; a second failing push updates that issue and opens no second. Adopts plan step 12 and Done-when 8 | E3 | pending P2 PR6 |
| AT-FR2.5-01 | scripted | D | S | Git scratch repo, branch `b`: relax the profile (set `reject_unknown_fields: false`) and add a concept with an unknown field; `uv run poe ci-validate --base main` → fails `OKF203` (base profile used); plain `V` on `b` passes, proving the difference | E2 | ready |
| AT-FR2.5-02 | live | D | G | The same change as a PR → `validate` fails with `OKF203`. Adopts plan step 12 | E3 | pending P2 PR6 |
| AT-FR2.5-03 | live | D | G | Adversarial: PR that edits `.github/workflows/validate.yml` to end with `exit 0` and adds a non-conforming concept. Record whether the required check fails. If it passes, raise a defect (S1): the PR's own workflow file ran. See open item PE-AT-5 | E3 | pending P2 PR6 |
| AT-FR2.5-04 | scripted | D | S | Adversarial: branch edits `scripts/okfprofile` so every check returns no findings and adds a bad concept; `uv run poe ci-validate --base main` → still fails (base tooling judges content); the tooling change alone is classified as tooling (`OKF001` absent) | E2 | ready |
| AT-FR2.6-01 | scripted | D | S | `V --change change.json` with `paths` holding one tooling and one content file: no label → `OKF001`; add `--label profile-migration` with no maintainer approval → `OKF002`; approval but `DECISIONS.md` unchanged → `OKF003`; all three → exit 0 | E2 | ready |
| AT-FR2.6-02 | live | D | G, A2 | Live mixed PR fails; with `profile-migration`, a maintainer approval and a `DECISIONS.md` change the publishing check passes. Fallback without A2: approval by the sandbox App (partial). Adopts plan step 12 | E3 | pending P2 PR6 |
| AT-FR2.7-01 | scripted | D | S | `<c>` with an unknown field → `OKF203`; with OKF `verified: [{by: "human:x", at: "2026-01-01T00:00:00Z"}]` → no `OKF203`; set `rules.reject_unknown_fields: false` → unknown field accepted | E2 | ready |
| AT-FR2.8-01 | scripted | RO | L | `uv run poe check` twice on one commit and `V` twice → identical findings (byte-equal JSON after removing timings) | E2 | ready |
| AT-FR2.8-02 | live | RO | G | Download the CI findings artifact for a commit and diff with `V` run locally on that commit → no difference | E2, E3 | pending P2 PR6 |
| AT-FR2.9-01 | scripted | D | S | For each `<ns>`: `<c>` with a tag value absent from the vocabulary → `OKF406`; add the value to its vocabulary concept with a definition → exit 0; where `kinds: true`, add the same value under two kinds → `OKF407` | E2 | ready |
| AT-FR2.10-01 | scripted | D | S | In the glossary concept add a term with `<a id="slug"></a>` equal to its GitHub slug; link to it from `<c>` → exit 0; link to a missing fragment → `OKF403`; change the id against `--base` → `OKF411` | E2 | ready |
| AT-FR2.10-02 | human | RO | G | Push the glossary and a linking concept to a scratch repo; on the platform page click the link and check it scrolls to the term, for a plain, a non-ASCII and a parenthesised term. Closes G3 and V-01 residue | E3 | pending P4 |
| AT-FR2.11-01 | scripted | RO | L | On each of Windows, macOS and Linux and Python 3.11 and 3.14 (own `UV_PROJECT_ENVIRONMENT` per version, see strategy.md): `uv run poe check` then `uv run poe test` → both exit 0. Closes G1, G10; V-13 | E1 | pending P2 PR6 (CI); ready locally |
| AT-FR2.11-02 | review | RO | G | List every `run:` line in `.github/workflows/*.yml`: each is `uv run poe <task>` or a platform-only step named in SDD AD-20 (App token, annotations, release upload, Pages) | E1 | pending P2 PR6 |

## FR3 Provenance and trust

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR3.1-01 | scripted | D | S | `git-local`: commit a concept change with trailers (`Approved-by:`, `Agent-Drafted: yes`), `uv run poe revision` → one new commit with trailer `Revision-Bot: true`; each touched concept gains one line with date, author, approval outcome, approver and owner status, `commit <sha7>`, labels (grammar I-08). Adopts plan step 15(b) | E4 | pending P2 PR2 |
| AT-FR3.1-02 | live | D | G | Merge PRs for each case one owner plus the App can produce (self-approved, App-approved non-owner, App-approved stale, `PR none`); each bot line equals the golden line in `tests/template/golden/`. Adopts plan step 15(a) | E3, E4 | pending P2 PR7 |
| AT-FR3.1-03 | scripted | RO | T | `[T]` `uv run pytest tests/template -q -k "revision or tiers"` → passes; covers the owner-approved and merged-without-approval cases that rest on recorded fixtures (plan OD-2) | E1 | pending P2 PR2 |
| AT-FR3.2-01 | scripted | D | S | Two merges to `main`, run the writer once after the second only (first run suppressed) → both recorded in order; run again → no new commit | E4 | pending P2 PR2 |
| AT-FR3.2-02 | live | D | G | Two merges close together so the concurrency group cancels one run → the next run records both. Adopts plan step 14 | E3, E4 | pending P2 PR6 |
| AT-FR3.3-01 | scripted | D | S | After AT-FR3.1-01's revision commit: `uv run python scripts/build_indexes.py --check` exits 0 and `V` has no `OKF502` | E2 | pending P2 PR2 |
| AT-FR3.4-01 | scripted | D | S | Concept with footnote definitions after *Revision history*; run the writer → line inserted at the section end, footnotes unmoved (`git diff` shows only that line). Alter an existing line, then `V --base HEAD~1` → `OKF315` | E2, E4 | pending P2 PR2 |
| AT-FR3.4-02 | live | D | G | Push a hand edit of a revision line to `main` → the push-run `validate` fails and opens the tracking issue. A well-formed appended line is recorded as undetected (G4); expected result is the recorded behaviour, not a pass | E3 | pending P2 PR6 |
| AT-FR3.5-01 | live | D | G, A2 | Owner A authors, owner B approves, A merges → line `approved @B (owner)`; A merges own PR with admin bypass → `self-approved (owner)`. Fallback without A2: App-submitted approval as non-owner; owner-approved case rests on recorded fixtures (partial; OD-AT1) | E3, E4 | pending P2 PR7 |
| AT-FR3.5-02 | scripted | D | S | `git-local`: trailer `Approved-by:` naming a different `maintainers` entry → `approved @<login>`; naming the author or no trailer → `self-approved`; author absent from `maintainers` → email local part, `non-owner` | E4 | pending P2 PR2 |
| AT-FR3.5-03 | scripted | D | S | `V --change change.json` with a concept made `stable`: no review → `OKF701`; author owns it → `OKF702` warning only; review of the current head by another owner → exit 0 (fixtures pass/stable, fail/OKF701, OKF702) | E2 | ready |
| AT-FR3.6-01 | live | D | G | App approves on commit 1, push commit 2, merge → line `approved (stale) @<app> (non-owner)` and the concept tier is Machine-confirmed. Adopts plan step 15(a) | E3, E4 | pending P2 PR7 |
| AT-FR3.7-01 | scripted | RO | T | `[T]` `uv run pytest tests/template -q -k tiers` → passes `tiers.json`, including a one-line owner-approved fix to an agent-drafted concept staying Machine-confirmed | E1 | ready |
| AT-FR3.7-02 | scripted | D | S | In a scratch library after the writer: agent-drafted revision then an owner-approved one-line fix → index line says machine-confirmed; add an owner-approved `full-review` revision → `human-reviewed (self)` where self-approved | E4 | pending P2 PR2 |
| AT-FR3.8-01 | scripted | D | S | `rules.write_okf_verified: true`, run the writer for a human, a machine and an unverified concept → `verified` holds `human:<login>` entries, one `process:<bot>` entry, none; a 10-line reader (any `human:` entry means human-reviewed, else machine-confirmed, per V-11) gives the library's tier in all three cases. The reader is written for the run: no OKF tool derives a tier | E2 | pending P2 PR2 |
| AT-FR3.9-01 | scripted | D | S | `status: reviewed` → `OKF205`; declare it under `status.extensions` with a tier → exit 0 | E2 | ready |
| AT-FR3.10-01 | scripted | D | S | `<c>` with `status: stable` and no citation → `OKF703`; add a footnote, then (separately) an external link → exit 0 | E2 | ready |
| AT-FR3.11-01 | scripted | D | S | Concept A with `stale_after` in the past (with offset), concept B whose last revision is older than `stale_after_default`, concept C neither, D with an offset-less `stale_after` → `uv run poe stale --json` lists A and B only; D raises `OKF120`; a concept with no revision is Unverified, not stale | E2 | pending P2 PR3 |
| AT-FR3.11-02 | live | D | G | `stale-report.yml` run twice with a stale concept → one issue labelled `stale`, updated the second time. Adopts plan step 14 | E3 | pending P2 PR6 |

## FR4 Indexes

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR4.1-01 | scripted | RO | L | `uv run python scripts/build_indexes.py --check` → exit 0; every folder under `knowledge/` has `index.md`; line count equals subfolders plus concepts per folder (`find` and `grep -c "^- \["`) | E1 | ready |
| AT-FR4.2-01 | scripted | D | S | After revisions give one concept each tier, `build_indexes.py` → each concept line ends `· <status> · <tier>`, with `(self)` where self-approved. Golden shapes: `[T]` `uv run pytest tests/template/test_indexes.py -q` | E1, E4 | pending P2 PR2 |
| AT-FR4.3-01 | scripted | D | S | Hand-edit an `index.md` → `OKF502`; delete one → `OKF501`; `build_indexes.py` then `V` → exit 0 | E2 | ready |

## FR5 Contribution workflow

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR5.1-01 | review | RO | G | `grep -c -E "agent-drafted\|full-review\|approved-move\|profile-migration" .github/pull_request_template.md` → all four named (compare with the label list in the file) | E1 | pending P2 PR3 |
| AT-FR5.2-01 | scripted | D | S | `V --change change.json` with `agent_markers: true` and no label → `OKF802`; add `--label agent-drafted` → no `OKF802` (fixture fail/OKF802); `git-local`: commit with `Agent-Drafted: yes` trailer and no label equivalent → writer records `agent-drafted` | E2 | ready (validator); pending P2 PR2 (trailer) |
| AT-FR5.3-01 | human | D | G | Pilot: a person who does not use git submits the `new-concept` form; the maintainer or an agent turns it into a PR with `new_concept.py`; merge. Expected: the issue closes with the PR and the concept validates. Pilot contribution of P4 | E3 | pending P4 |
| AT-FR5.3-02 | review | RO | G | Forms parse (`uv run poe check-config`), name only labels in the `setup_repo.py` label list, and a library created with forms switched off has no `.github/ISSUE_TEMPLATE/` | E1 | pending P2 PR3 |
| AT-FR5.4-01 | scripted | D | S | CODEOWNERS giving folders A and B different owners; one change touching a concept in each, approved by owner A only → revision lines differ: `(owner)` for A's concept, `(non-owner)` for B's | E4 | pending P2 PR2 |
| AT-FR5.5-01 | scripted | RO | L | `test -f DECISIONS.md` and `grep -n "Instantiated from okf-library-template" DECISIONS.md` → entry DR-01 with the licence choices | E1 | pending P2 PR5 |

## FR6 Instantiation

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR6.1-01 | human | D | G | A second person, with the run sheet and a stopwatch, creates a library and merges a first validated concept (`github` path, W-01 steps 1 to 6). Expected: total at most 30 minutes; times per step recorded. V-06 | E5 | pending P4 |
| AT-FR6.1-02 | human | D | S | Same for `git-local` (estimate 14 minutes) | E5 | pending P4 |
| AT-FR6.2-01 | scripted | D | S | `init_library.py --answers` with a proprietary code licence and the default content licence → `LICENSE` (owner's), `LICENSE-content` (CC BY 4.0), `LICENSE-template` (Apache 2.0 text), `NOTICE` present | E1 | pending P2 PR5 |
| AT-FR6.2-02 | scripted | D | S | Defaults only → content CC BY 4.0, code Apache 2.0, no `LICENSE-template`; `README.md` states which licence covers which paths | E1 | pending P2 PR5 |
| AT-FR6.3-01 | scripted | D | S | After `init_library`: no `CLAUDE.md`, `docs/`, `tests/template/`, `.github/workflows/template-tests.yml`; `AGENTS.md` has no `template-only` markers; `grep -rn "<placeholder marker>"` → no match; `V` and `build_indexes.py --check` → exit 0 | E1 | pending P2 PR5 |
| AT-FR6.3-02 | scripted | D | S | Adversarial: seed a leftover placeholder and, separately, a template-only file in the answers' source copy → `uv run poe selftest` fails for each | E1 | pending P2 PR5 |
| AT-FR6.3-03 | live | RO | G | Actions history of the template shows the self-test job green for `github` and `git-local` on the last three template PRs | E3 | pending P2 PR6 |
| AT-FR6.4-01 | scripted | D | S | Upgrade path: scratch library created by clone; `git remote add template <template repo>`; `git fetch --tags`; `git merge --no-commit <newer tag>` → conflicts only in files the library changed; resolve; `uv run poe check` and `uv run poe test` pass. The criterion is "—"; this tests the supported route (QA-52) | E4 | pending P2 PR5 |
| AT-FR6.4-02 | scripted | D | S | Diverge: edit one script under `scripts/` and record it in `DECISIONS.md`; `uv run poe check` and `V` → still exit 0 | E1 | pending P2 PR5 |
| AT-FR6.5-01 | scripted | D | S | `git-local` library with outbound network blocked (offline machine or `HTTPS_PROXY=http://127.0.0.1:9`): `V`, `build_indexes.py --check`, a commit with trailers, `uv run poe revision`, `uv run poe stale`, `uv run poe release v0.0.1` → all exit 0 and no network call is attempted | E1 | pending P2 PR4 |
| AT-FR6.5-02 | review | RO | T | `grep -rn "api.github.com\|urllib" scripts/okfprofile` → only under `platforms/`; `[T]` the test that fails when a core module imports an adapter passes | E1 | pending P2 PR2 |
| AT-FR6.6-01 | live | D | G | W-12 rehearsal on the `git-local` library: pre-check, `git push --all` and `--tags` to `p2-w12-target`, tooling PR switching `platform`, `setup_repo.py`, rebuild each release from its tag. Expected: `git rev-list --all` before equals after; revision lines unchanged; each archive tar digest equals the tag message. Adopts plan step 15(c) | E4 | pending P2 PR7 |
| AT-FR6.6-02 | scripted | D | S | After AT-FR6.6-01: new merges write `PR #n` lines while older `commit <sha7>` lines stay; the `maintainers` map still attributes both | E4 | pending P2 PR7 |

## FR7 Agent skills and delivery

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR7.1-01 | review | RO | L | Each `.agents/skills/<name>/SKILL.md` has only `name` (equal to its folder), `description` and optional `license`, `compatibility`, `metadata`, `allowed-tools`; both `author-concept` and `use-bundle` exist; neither names a type, prefix or tag | E1 | pending P3 |
| AT-FR7.1-02 | human | D | S | Agent run (any provider): follow `author-concept` to draft a concept of each `<type>`; `V` → exit 0; PR labelled `agent-drafted`. No edit to the skill | E1, E2 | pending P3 |
| AT-FR7.1-03 | human | RO | L | Agent run: with only the release archive, follow `use-bundle` on five questions the reviewer chose; expected: navigation by `index.md` one level at a time, sections read by heading, vocabularies read from `vocab/` | E1 | pending P3 |
| AT-FR7.2-01 | human | RO | L | Traced agent run on the release archive: for each answer the report lists concept `uid`, status, trust tier (with `(self)`) and release tag; reviewer checks every cited `uid` exists at that tag. Expected: 100 % of citations trace | E1 | pending P4 |
| AT-FR7.2-02 | human | D | S | Adversarial: a relevant concept is `draft` with no revision (Unverified); the agent must state that it is unverified; fail if it calls it reviewed | E1 | pending P4 |
| AT-FR7.3-01 | scripted | D | S | `uv run poe release v0.0.1` then in `dist/`: `sha256sum -c *.sha256` → OK; `tar -tzf` lists `knowledge/`, `profile/`, `AGENTS.md`, `README.md`, `CITATION.cff`, licence files, `NOTICE` (and `.agents/skills/use-bundle/` from P3); manifest holds tag, commit, versions, counts, `platform` | E1 | pending P2 PR4 |
| AT-FR7.3-02 | scripted | D | S | Fresh clone at the tag, `uv run poe bundle` → same tar digest as the tag message; `.tar.gz` digest compared only if Python and zlib versions match (ADR-004). Repeat on the three systems (V-12) | E1 | pending P2 PR4 |
| AT-FR7.3-03 | live | D | G | Push a tag in the sandbox → a release exists with archive, checksum, manifest, notes; asset edit refused (immutable). V-07 residue | E3 | pending P3 |
| AT-FR7.4-01 | scripted | D | S | Merge a concept change but delete its revision line (or skip the writer); `uv run poe release v0.0.2` → fails with an `OKF9xx` finding; restore and rerun → passes | E2 | pending P2 PR4 |

## FR8 Website

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-FR8.1-01 | scripted | D | S | `uv run poe docs-build` then `git status --porcelain knowledge/` → empty; the build fails if `knowledge/` is made unreadable, showing it reads in place | E1 | pending P3 |
| AT-FR8.2-01 | scripted | D | S | Checks 1 and 2: each folder `index.md` is a landing page; a relative link between concepts resolves to a site route (strict build exits 0; `grep` the built HTML for the target path) | E1 | pending P3 |
| AT-FR8.2-02 | scripted | D | S | Checks 3 to 5: an unknown frontmatter key is kept; a heading anchor equals the platform slug; a concept using `status`, `title`, `tags`, `slug` keys keeps the profile meaning; a colon-namespaced tag gives a valid page and URL | E1 | pending P3 |
| AT-FR8.2-03 | scripted | D | S | Check 6: a prose line with `<1000 V and {braces}` and a footnote render unchanged in the built HTML | E1 | pending P3 |
| AT-FR8.2-04 | review | RO | S | Compare constructs the profile does not use between markdown-it-py and Python-Markdown output (lists after paragraphs, tables, nested footnotes, inline HTML) and list each divergence. Closes G2 | E1 | pending P3 |
| AT-FR8.3-01 | live | D | G | Tag run builds the site from the tag; the deployed or artifact site manifest names the latest tag | E3 | pending P3 |
| AT-FR8.4-01 | human | RO | S | On a preview build, "Suggest an edit" opens the platform editor on that concept file; the site-wide issue link opens the issue forms | E3 | pending P3 |
| AT-FR8.5-01 | review | RO | G | For a library before its v1.0.0: `gh api repos/<owner>/<repo>/pages` → 404 (no public site) unless the owner recorded an alpha or beta site in `DECISIONS.md` | E1 | pending P3 |

## Non-functional

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-NFR1-01 | human | RO | L | Extract a release archive; using only `ls`, `cat` and `grep`, reach one concept from the root `index.md` through folder indexes and read its declared sections. Expected: no tool beyond file reading was needed | E1 | pending P2 PR4 |
| AT-NFR2-01 | review | RO | T | Read each SRS requirement against the checklist: is it met by only one product? Record any that is. Then `grep -rn "gh \|api.github" scripts/okfprofile` → only under `platforms/` | E1 | ready |
| AT-NFR3-01 | review | RO | G | Organisation plan is Free; Actions usage for the run month is within the free allowance (billing page); private-library jobs use Linux only (OD-3) | E3 | pending P2 PR6 |
| AT-NFR4-01 | scripted | RO | L | `uv run poe licences` → exit 0 on each of the three systems (closes G11); the licence files from AT-FR6.2-01 are present; `LICENSE`, `NOTICE` untouched in the template | E1 | ready |
| AT-NFR5-01 | review | RO | L | Sample five concepts: plain English, SI units, standards cited by number and edition. No tool checks this; the reviewer records pass or fail per concept | E1 | ready |
| AT-NFR6-01 | scripted | D | S | Add a line matching a pattern in `profile/scan.yaml` (build the string at run time; never a real secret) and stage it → `uv run poe scan` exits non-zero, the pre-commit hook refuses the commit (Git Bash and PowerShell); remove it → exit 0. A confidentiality marker likewise | E1 | ready |
| AT-NFR6-02 | live | D | G | Push the planted string in a sandbox PR → the gitleaks CLI job fails and `scan.py` fails on a marker. Closes G12 | E3 | pending P2 PR6 |
| AT-NFR6-03 | scripted | RO | L | `uv run poe audit` → zero findings or only listed exceptions (needs network and `uvx`). Closes G13 | E1 | ready |
| AT-NFR6-04 | review | RO | G | Workflows: every `uses:` is a 40-character SHA; each job has `permissions`; no `pull_request_target`; the pinned-SHA test passes; no secret in a fork PR run | E1 | pending P2 PR6 |
| AT-NFR6-05 | scripted | D | S | Clean venv: `uv pip install --require-hashes -r requirements/validate.txt` then `V` → exit 0. Adversarial: alter one hash → install refuses | E1 | ready |
| AT-NFR7-01 | live | D | G | `setup_repo.py` on a scratch repo; delete a label and change a setting; rerun → both restored; run again → no change. Adopts plan step 10 and Done-when 9 | E3 | pending P2 PR5 |
| AT-NFR7-02 | scripted | D | S | Fresh clone: `uv sync --locked` then `uv run poe test` pass; then a clean venv from `requirements/validate.txt` runs `V` | E1 | ready |
| AT-NFR7-03 | scripted | D | S | Flip one byte of a release archive → `sha256sum -c` fails; rebuilding from the tag still matches the recorded digest. The missed-revision recovery is AT-FR3.2-01 | E1 | pending P2 PR4 |

## Performance

| ID | Kind | Mode | Pre | Steps → expected | Ev. | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AT-SDD12-01 | scripted | RO | L | Generate the 600-concept bundle in a temporary copy of the library (method: performance.md); time `V` and `build_indexes.py --check` three times → each under 10 s; record machine and system. Closes G8 | E5 | ready (generator is harness work) |
| AT-SDD12-02 | live | RO | G | The `validate` job on that bundle in CI takes under 3 minutes | E3, E5 | pending P2 PR6 |
| AT-SDD12-03 | scripted | RO | T | `[T]` `uv run poe selftest` completes within the time budget agreed in performance.md | E5 | pending P2 PR5 |
