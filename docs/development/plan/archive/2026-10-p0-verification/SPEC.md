# SPEC: build phase P0, verification and site generator decision

Status: **Draft for owner approval.** No spike has started. Drafted 2026-10-26 on branch `docs/p0-verification-plan` (not committed).

## Requirement and sources

| Document | Role | Status |
| --- | --- | --- |
| [SRS](<../requirements/OKF Library Template - Software Requirements Spec.md>) | The requirement. Front matter `status: accepted` | Accepted |
| [SDD](<../architecture/OKF Library Template - Software Design Document.md>) §14 (P0 row) and §15 (V-01 to V-13) | Defines the phase and the verification items | Draft; P0 may propose edits to it |
| [DDR](<../adr/OKF Library Template - Design Decision Record.md>) | QA-36 (V-10), QA-38 (generator decision moved into P0), QA-45 (re-estimate) | Frozen series |
| [Stack report](<../architecture/OKF library technology stack options.md>) | Evidence for V-03 and V-04 (18 October 2026 test) | Evidence at its date |

**Abbreviations.** P0: build phase 0, "Verification" (SDD §14). V-nn: verification item nn (SDD §15). FR/NFR: SRS requirements. AD-, QA-, DR-, ADR-: decision IDs, cited as written (`../conventions.md`). Files with spaces in their names are linked with angle brackets above; V-10 settles whether that form is the one to keep.

P0 is not a feature with its own requirement. It answers questions that the accepted SRS and the draft SDD depend on, so that P1 starts on verified ground. Because it covers only P0, the SRS is not set to `Done` when P0 ends (P1 to P4 remain).

## Goal

Answer each of V-01 to V-13 with recorded evidence, decide the site generator (V-03, V-04; C-07, AD-13), and re-estimate P1 to P4, so that SDD §14's P0 exit is met: *each V-item answered; generator decided; design and estimate updated.*

## Out of scope

- Any change to a requirement or a decision. A spike outcome that would change one is written up as a **proposed** entry for the owner's approval (`plan.md`, "Proposed decision entries"); nothing is written to `adr/`, the SDD, the SRS or `constraints.md` in P0 until approved.
- P1 work: no `okfprofile`, no `pyproject.toml` in this repository, no template code. Spike code is throwaway and is not copied into the template.
- Any write to `open-renewables`. The only writes there are the three plan files, held on a local branch and not committed, pushed or merged.

## Where work happens

| Place | Use |
| --- | --- |
| This repository (`open-renewables/okf-library-template`), branch `docs/p0-verification-plan` | `plan/SPEC.md`, `plan/plan.md`, `plan/todo.md` only. No commit, push or merge without the owner's instruction |
| `open-renewables-sandbox/p0-spikes` (clone at `C:\Users\rich_\Local\GitHub\p0-spikes`) | All spikes. Observed 2026-10-26: public, empty, free organisation, default workflow token read-only |
| Fresh Claude Code session in this repository | **V-10a only**, read-only |

Every `gh` write is guarded against the sandbox organisation (`plan.md`, "Guards"). The p0-spikes repository is public, so spike content is synthetic and holds no secret, key or proprietary concept.

## Scope: items and done-when

SDD §15 holds the full wording of each item; this table adds the evidence that closes it. "Needs you" marks a person, account, machine or setting that only the owner can supply (detail in `plan.md`).

| ID | Question (short) | Feeds | Done when | Needs you |
| --- | --- | --- | --- | --- |
| V-01 | Does GitHub render `<a id>` anchors (before or inside headings, duplicate ids, non-ASCII, parentheses) so that links and the automatic slug behave as AD-14 assumes? | FR2.10, FR8.2 check 4; AD-14, I-01, W-04 check 4 | A table of fixture × rendered id × fragment link result from github.com; AD-14 placement and duplicate-id rule confirmed, or the rule that holds stated | — |
| V-02 | Do two- and four-space nested list items render the same in Python-Markdown (MkDocs, Zensical) and on GitHub? | FR8.2; I-01 indentation rule | Same fixture rendered by all three; nesting depth compared; I-01 rule confirmed or replaced | — |
| V-03 | Which Zensical features work, judged on output, not exit code (`/`-rooted links, `validation`, `strict`, `extra.status`, `extra.social`, `content.action.edit`, footnotes, `attr_list`, `toc`, tags)? Does MkDocs tolerate Zensical-only theme keys? | FR8.1, FR8.2, FR8.4; AD-13, C-07, I-13 | Feature × builder matrix with versions and date; the six FR8.2 checks on the spike bundle for Zensical; a config-only fix or a named blocker for each failure | — |
| V-04 | Does Docusaurus 3.10 in `detect` mode pass the six FR8.2 checks on three concepts? | FR8.1, FR8.2; AD-13 fallback | Six-check result with versions; dependency and licence footprint; build time | Concepts (see open question D-5) |
| V-05 | Do the ruleset bypass modes, required-check naming, API shape of bypass merges and review commit ids, concurrency cancellation and the fork-privacy limit behave as §11 and W-05 assume? | FR3.2, FR3.5, FR3.6, FR2.4; AD-01, AD-11, AD-12; §11, W-04, W-05, W-01 fork row | Observation per sub-item (5a to 5e in `plan.md`) with raw API output; §11 and the W-05 inference confirmed or corrected | Account (App creation, reviewer identity, fork target) |
| V-06 | How long does a second person take over W-01 end to end, including the App? | FR6.1; W-01 | Per-step times for the steps that can run without P1 and P2 scripts; the rest marked "not measurable in P0" | Person |
| V-07 | Are immutable releases available on GitHub Free? What are the Cloudflare Pages access-policy limits on the free plan? | FR7.3, FR8.5, NFR3; C-10, AD-15, §11 | Release behaviour observed (edit, delete, retag after publish); Cloudflare limits recorded from the vendor's documentation, and by a test only if an account is supplied | Account (Cloudflare); setting |
| V-08 | How does okf-skills map its findings to `OKF1xx`, how does it treat generated `index.md` files, and does the vendored validator run outside the Action? | FR1.1, FR1.2, FR2.2 check 1, FR2.8; AD-08, I-09 | Finding-to-code mapping table; result on index files; the validator run locally from the pinned commit with its dependency and licence listed | — |
| V-09 | Does Claude Code discover skills through `.claude/skills/` symlinks, and do they survive "Use this template", the release archive and Windows checkouts? | FR7.1; AD-16, C-08, W-10 | Discovery observed in a fresh session; symlink mode checked after each route; AD-16 confirmed, or the copy fallback specified | Setting (Windows symlink mode); extra sandbox repo (D-1) |
| V-10 | Do `CLAUDE.md` imports and Markdown links to files with spaces resolve, including from subfolders of `docs/development/`? | AD-21, §6; QA-36, QA-67 | **10a:** the SRS summary check and an import-loaded check in a fresh session here. **10b:** import and link forms compared in p0-spikes. The form to use is named | Person (open the fresh session, or approve one) |
| V-11 | How does OKF derive a trust tier from `verified` (latest entry or any entry), and what non-human actor prefix marks machine confirmation? | FR3.7, FR3.8; I-08 | Rule quoted from the pinned specification or okf-skills with file and line; I-08 mapping confirmed or adjusted, or the specification stated to be silent | — |
| V-12 | Does the same tag rebuilt on Linux, macOS and Windows, on Python 3.11 and 3.14, give one SHA-256 under the I-12 settings? | FR6.6, FR7.3; I-12, W-12 step 5, QA-61 | Six build results compared; settings that make them equal, or the cause of any difference | Machine (macOS and Linux) |
| V-13 | Do the poethepoet tasks, `uv run poe install` on a fresh clone and `repo: local` pre-commit hooks run unchanged on all three systems? | FR2.8, FR2.11, NFR7; AD-20, I-16, I-17 | Pass or fail per system and Python version, with the failing command and cause | Machine (macOS and Linux) |

## Site generator decision

C-07, AD-13 and QA-38 require the decision at the P0 exit. Material for MkDocs reaches end of life on **2026-11-05**, ten days after this draft, so V-03 and V-04 run first.

Options, as the SDD already frames them:

| Option | Meaning |
| --- | --- |
| A | Keep AD-13: MkDocs 1.6.1 with Material blocking, Zensical non-blocking |
| B | Switch: Zensical blocking, MkDocs non-blocking (the stack report's switch criterion) |
| C | Docusaurus in `detect` mode, the fallback |

Proposed decision criteria, for the owner to accept or change before the spikes run. These are evidence rules, not a decision:

1. B is eligible only if Zensical passes all six FR8.2 checks on the spike bundle by configuration alone (no source file changed, FR8.1) at an exact pinned version, with its own and its locked dependencies' licences on the allowlist in `../constraints.md`.
2. If Zensical fails a check with no workaround, A stays eligible, with the residual exposure after end of life recorded and a review date set.
3. C is eligible only if it passes all six checks. It adds a Node toolchain to a Python-only repository, which needs its own ADR under `../conventions.md` ("a new runtime dependency … needs an ADR") and a change to `../constraints.md`.
4. The recommendation, with the evidence, goes to the owner as a proposed ADR. The generator is not chosen by this plan.

Owner direction, 2026-10-28: proceed with option A and expect a later move to Zensical for the release site. This keeps AD-13 and applies its existing switch criterion (stack report: Zensical becomes blocking when it passes all six checks on the pilot bundle). The P0 rerun of the Zensical checks is dropped; known issues are listed in the recommendation instead. The ADR text stays Proposed until the owner approves it.

## Quality bar and conventions

- `../constraints.md` applies to the template repository. Spike code lives outside it and ships nothing, so ruff, mypy, coverage and lock limits do not apply to it. Where a spike mirrors a constrained thing, it follows the constraint: workflow actions pinned by full SHA and read-only per-job permissions (Workflows row), Python 3.11 and 3.14 (Supported Python row), and dependency licences checked against the allowlist.
- `constraints.md` row "Site" says the Zensical build is non-blocking until the P0 generator decision. The decision may therefore require a change to that row, which needs an ADR; it is listed as a proposed entry, not edited.
- `../conventions.md` governs the three plan files and any proposed entries: British English, sentence-case headings, ISO dates, decision IDs cited as written, exact file names.
- `../testing/README.md`: the testing files are written in P1. P0 writes none. A P0 finding that needs a later automated test is recorded in the P0 outcome as input for `known-gaps.md`.

## Interpretations the owner should confirm

1. **V-06 in P0.** `init_library.py` and `setup_repo.py` do not exist until P2, and FR6.1's acceptance criterion says "timed by a second person in the pilot". P0 can therefore time only the platform steps of W-01 (1, 2, and 5, plus the manual equivalent of 4). The full FR6.1 measurement stays in P4. This changes no requirement.
2. **V-10 split.** SDD §15 gives one first check (fresh session here, read-only). The link-form comparison needs files with spaces and a rendering view, so it runs in p0-spikes as 10b.
3. **V-12 and V-13 machines.** Hosted runners (ubuntu, macos, windows) in the public sandbox repository cover Linux and macOS without the owner's hardware. Real hardware is an optional cross-check.
4. **V-05 fork check.** A fork needs an owner other than the sandbox organisation. If no second account is supplied, the answer comes from GitHub's documentation and is marked **[Doc]** rather than **[Test]**.
5. **Outcome recording.** SDD §14's gate says outcomes are "recorded in the DDR", but the QA- and DR- series is frozen (QA-68). The proposal is DDR change-log rows plus edits to SDD §15, both drafted at the exit and applied only on approval.
6. **Closing P0.** At the exit the three plan files move to `plan/archive/2026-10-p0-verification/` as the flow requires, but the SRS is not set to `Done`.

## Exit

All of SDD §14's P0 exit conditions, plus: each V-item has a result file in p0-spikes; the proposed entries are drafted and presented; the re-estimate replaces QA-45's 35–55 versus 27–41 person-day range with a justified figure, or states why it cannot. The owner decides what is accepted.
