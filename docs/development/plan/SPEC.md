# SPEC: build phase P3, site, release and skills

Status: **Approved by the owner on 2026-11-11:** the plan, open decisions OD-1 to OD-15 and proposed entries PP-1 to PP-6 as drafted. Nothing is built. Drafted on branch `claude/p3-plan-0d06e3` (not committed). Effort is in agent hours, owner hours and calendar days, as for P2 **[Inf]** (`plan.md`).

## Requirement and sources

| Document | Role | Status |
| --- | --- | --- |
| [SRS](<../requirements/OKF Library Template - Software Requirements Spec.md>) | The requirement. Front matter `status: accepted` | Accepted |
| [SDD](<../architecture/OKF Library Template - Software Design Document.md>) §14 (P3 row), §7 C-07, C-08, C-10, §8 I-12 to I-14, §9 W-06 to W-09, §10, §11 | Defines the phase, the site build, the skills and the release | Fixed for P3 |
| [DDR](<../adr/OKF Library Template - Design Decision Record.md>) | QA-20, QA-26, QA-37, QA-38, QA-47, QA-60 to QA-62, QA-74 | Frozen series |
| [ADR-001 to ADR-008](../adr/README.md) | Notably ADR-001 (generator), ADR-002 (provider-neutral skills), ADR-004 (archive digest), ADR-005 (relative links), ADR-006 and ADR-007 (licences) | Accepted |
| P2 close-out ([archived plan](archive/2026-11-p2-ci-governance/todo.md)), `v0.2.0` tag message, `side-session-notes/p2-s2-result.md` | Inputs listed under "Carried into P3" | Applied |

**Abbreviations.** P3: build phase 3, "Site, release, skills" (SDD §14). FR/NFR: SRS requirements. AD-, QA-, DR-, ADR-: decision IDs, cited as written. I-nn, C-nn, W-nn, V-nn: SDD items. G-n: known gap (`../testing/known-gaps.md`). AT-: acceptance case (`../testing/acceptance-test-cases.md`). PP-n: a proposed entry for the owner; OD-n: an open decision with a default (`plan.md`).

P3 is one phase of the SRS, so the SRS is not set to `Done` when P3 ends.

## Goal

Meet SDD §14's P3 exit: **v0.5.0 (beta)**, tagged by the owner. At that point the template can build and preview a site from its bundle with two generators, cut a GitHub Release with a verified archive that carries the consuming skill, and ship both agent skills and the library-facing documents (`AGENTS.md`, `GOVERNANCE.md`, `README.md`, `NOTICE`). Everything the owner's template-build gate needs except the pilot (P4) is then in place.

## Scope

| Area | Delivered in P3 | SDD / SRS source |
| --- | --- | --- |
| Site stack | `site-mkdocs` and `site-zensical` dependency groups, hash-locked exports, `mkdocs.yml` (I-13 baseline), tasks `docs`, `docs-build`, `docs-zensical`, `docs-linkcheck`, a page-list comparison | C-07; AD-13; ADR-001; FR8.1 |
| Site compatibility | The six FR8.2 checks as tests on a fixture bundle, run on both generators; Python-Markdown divergences listed (G2); MkDocs tolerance of Zensical keys (ADR-001 carried issue) | FR8.2; V-03; AT-FR8.\* |
| Site workflow | `site.yml`: MkDocs blocking, Zensical non-blocking with lychee and page-list checks, preview artifact, tag build, Pages deploy path (off before v1.0.0), release manifest on the site | W-08; FR8.3 to FR8.5 |
| Site links | "Suggest an edit" (`repo_url`, `edit_uri`) and site-wide issue-form link; none for `git-local` | FR8.4; QA-37 |
| Release workflow | `release.yml`: revision-line gate, validation, archive, checksum, manifest, GitHub Release, immutable where available, rebuild check | C-10; W-07; FR7.3, FR7.4; V-07 residue |
| Release archive | `use-bundle` skill and a release-identity file inside the archive so an agent can report the tag from the archive alone | I-12; FR7.2, FR7.3 (PP-3) |
| Skills | `author-concept` and `use-bundle` in `.agents/skills/` (six spec fields, no provider file); optional Claude Code adapter task; static checks | C-08; I-14; ADR-002; FR7.1 |
| Library documents | `AGENTS.md` (library-facing), `GOVERNANCE.md`, `README.md`, `NOTICE` review; instantiation rewrites their placeholders | C-08; SDD §14; SRS Governance |
| Instantiation | `init_library.py` rewrites `mkdocs.yml` and `GOVERNANCE.md`; the W-10 self-test adds the strict site build (G25) | W-10 step 4; PP-6 |
| Leak-removal rehearsal | `runbook-remove-leaked-content.md` run on a synthetic repository with a tag and a Release (G33) | NFR7; `../AGENTS.md` |
| Scheduled report | First scheduled `stale-report.yml` run verified; next one observed after the P3 merges | W-06; G27 |
| Housekeeping | `.idea/` decision (G30); scope-note RFC (G6); sandbox clean-up carried from P2 | known-gaps |
| Tests and test docs | Site-compat and skills tests, release rehearsal, golden digest regenerated; `testing/` updated | `../testing/strategy.md` ("P3 adds") |

### Requirements covered

| Requirement | In P3 | Left for |
| --- | --- | --- |
| FR7.1 | Both skills written and statically checked (frontmatter, no type, prefix or tag hard-coded); one smoke run by an agent from the archive | P4: "work on the pilot without edits" (AT-FR7.1-02, -03), second runtime |
| FR7.2 | `use-bundle` reports `uid`, status, tier, release tag; archive carries the tag | P4: the traced run (AT-FR7.2-01, -02) |
| FR7.3, FR7.4 | `release.yml` on the template: archive with `use-bundle`, checksum, manifest, Release; gate fails on a missing line | — |
| FR8.1 to FR8.4 | Build in place, six checks on both builders, latest-release manifest, both links on a preview | The platform half of FR2.10 (AT-FR2.10-02) and G3: P4 |
| FR8.5 | No Pages site for the template or a library before v1.0.0 (AT-FR8.5-01) | — |
| NFR1 | Archive read with file tools only (AT-NFR1-01) | — |
| NFR6 | `site.yml` and `release.yml` pinned by SHA, least privilege, no secret to forks | — |
| FR6.3, FR6.5 | Self-test builds the site (`github` and `git-local`); a local site works without a platform | — |
| FR1 to FR6, NFR2 to NFR5, NFR7 | Unchanged | — |

## Out of scope

- **P4:** pilot library and about 20 concepts; V-06 timing by a second person (FR6.1); traced agent run (FR7.2); pilot contribution via an issue form (FR5.3); primary-type rename and `new_concept.py --set` (G23); a second approver account (G35); W-12 with several tags (G32); GitHub scroll targets (G3); the switch to Zensical as the blocking build (ADR-001 criterion is judged on the pilot bundle; the switch is a later ADR).
- A public site for the template or any library (FR8.5); GitHub Pages is exercised only on a synthetic sandbox repository.
- Adapters for other hosting platforms (post-v1.0.0); pre-filled per-page issue links (QA-37); `format_item_consistency`, `linked_set_drift`, `citation_index` (QA-45).
- Any change to a requirement or decision. Anything that would change one is a proposed entry (`plan.md`); nothing is written to `adr/`, the SDD, the SRS or `constraints.md` until the owner approves it.
- Provider-specific files committed to the repository: no `.claude/`, no product plugin manifest (ADR-002).
- Building scope notes (G6): P3 drafts an RFC only (OD-4).

## Carried into P3

| Source | Item | Where in `plan.md` |
| --- | --- | --- |
| SDD §14 P3 row | `mkdocs.yml` or the chosen generator; `site.yml`; `release.yml`; both skills; `AGENTS.md`, `GOVERNANCE.md`, `README.md`, `NOTICE`; leak-removal rehearsal | Steps 1 to 12 |
| ADR-001 | Re-test Zensical from P3 by the parallel job; `validation.links.anchors` ignored by Zensical; whether MkDocs tolerates both key sets; exact pin; review of the post-end-of-life exposure no later than P4 (Material reached end of life on 2026-11-05) | Steps 5, 6 |
| G2 | Python-Markdown divergences beyond nesting | Step 5 |
| G6 | Scope notes: "an RFC before P3" | Step 9 |
| G11 | Licence check covers the installed environment only; adds the site groups | Step 4 |
| G18 | `config.yml` links `GOVERNANCE.md`, which does not exist | Step 8 |
| G21 | `github` mode builds no archive; `release.yml` closes it | Step 10 |
| G25 | `init_library.py` does not touch `mkdocs.yml`; self-test cannot build the site | Step 7 |
| G27 | The scheduled `stale-report.yml` has not run (it ran on 2026-11-09, success; to be read) | Step 12 |
| G30 | The template's `.idea/` folder is tracked | Step 9 |
| G33 | Leak-removal runbook not rehearsed | Step 12 |
| V-07 residue | Immutable releases and Release upload on a repository the owner controls | Steps 10, 11 |
| P2 todo | "Sandbox repositories and Apps cleaned up or archived (OD-11)" | Step 13 |
| `../testing/` | AT cases marked `pending P3` (FR7.1-01, FR7.3-03, FR8.1 to FR8.5); `strategy.md` "P3 adds" | Step 13 |
| P2 close-out | P3 estimate "5 to 7 days, owner about 2 hours, plus the leak rehearsal and first scheduled run" | `plan.md` "Effort" (PP-1) |

Carried to P4 and not P3 work: G23, G32, G35 (the owner's instruction), G3, G12 residue none. G1, G4, G9, G10, G13 to G17, G19, G20, G22, G26, G28 to G29, G31, G34, G36 are unchanged unless a step says so.

## Quality bar and conventions

- `../constraints.md` applies in full and is not weakened. The Site row (`mkdocs build --strict` passes, Zensical non-blocking) becomes enforced by `site.yml`. A limit that a P3 job cannot meet is a proposed entry, not a relaxed limit.
- `../conventions.md` governs: standard library preferred; no new `validate` dependency; site dependencies stay in their own groups (NFR6); Google-style docstrings; `--json` on every script; one change per pull request; tooling and content in separate pull requests; branch `<kind>/<slug>`.
- `../testing/`: tests use no network; site tests need the site groups and skip with a notice where they are not installed; the CI job installs them. A behaviour that cannot be tested goes to `known-gaps.md`.
- Workflows follow SDD §10: actions pinned by full SHA, read-only default token, per-job permissions, no `pull_request_target`, jobs call only `uv run poe <task>` (AD-20).
- Skills follow ADR-002 and I-14: only the six specification fields; nothing in a skill names a concept type, `uid` prefix or tag namespace (AT-FR7.1-01).

## Done when

1. `uv run poe check` and `uv run poe test` pass locally on Python 3.11 and 3.14 and in CI on three systems, with `constraints.md` changed only by an approved entry.
2. `uv run poe docs-build` passes strict on the template and on an instantiated library in both modes (the self-test); `git status --porcelain knowledge/` is empty afterwards (FR8.1).
3. The six FR8.2 checks pass on MkDocs; the result on Zensical is recorded per check by configuration alone, with each failure a known gap or a proposed entry; the G2 divergences are listed (AT-FR8.2-01 to -04).
4. `site.yml` runs green on the template and in a sandbox repository: preview artifact built from a tag, the site manifest names that tag (FR8.3), "Suggest an edit" and the issue link work on the preview (FR8.4), and no Pages site exists unless the owner enabled one for a v1.0.0 tag in the sandbox (FR8.5).
5. `release.yml` on a sandbox repository publishes a Release from a tag with archive, checksum, manifest and notes; an edit to an asset is refused where immutability is on; the gate fails on a deleted revision line and passes when restored (FR7.3, FR7.4; AT-FR7.3-03, AT-FR7.4-01); the archive rebuilt from the tag reproduces its tar digest on all three systems.
6. The archive holds `use-bundle`, `AGENTS.md`, `README.md`, the licence files, `NOTICE` and a release-identity file, and is readable with `ls`, `cat` and `grep` (NFR1, FR7.3).
7. `.agents/skills/author-concept` and `.agents/skills/use-bundle` pass the static checks; one agent, given only the release archive and `AGENTS.md`, answers five questions as `use-bundle` directs and one agent drafts a concept with `author-concept` that validates (single-provider smoke test, labelled **[Test]**; second runtime not tested, ADR-002).
8. `AGENTS.md` is library-facing, `GOVERNANCE.md` and `README.md` are current, `NOTICE` is reviewed; an instantiated library has no template text or unresolved placeholder in them (W-10).
9. The leak-removal runbook ran on a synthetic repository with a tag and a Release and is corrected by what the run showed (G33).
10. The scheduled `stale-report.yml` run of 2026-11-09 is read and recorded, and the run after the P3 merges is green.
11. `testing/` documents are updated (G2, G11, G18, G21, G25, G27, G33 closed or narrowed; new gaps listed); proposed entries are decided; the P4 estimate is proposed from P3 actuals.
12. The owner has tagged `v0.5.0` (beta) and the release workflow ran on it (OD-9).

## Interpretations the owner should confirm

1. **Skills are proved statically plus one smoke run in P3.** FR7.1's acceptance names the pilot library, so the full check is P4 (SDD §14 P4 row). ADR-002 left unverified whether each runtime reads `AGENTS.md` and follows a skill pointer; P3 tests one provider and says so.
2. **The switch to Zensical is not P3.** ADR-001's criterion is "all six checks on the pilot bundle by configuration alone, licences allowed". P3 measures it on the fixture bundle and the template example; the decision and its ADR follow in P4.
3. **`release.yml` runs on the template.** The owner's v0.5.0 tag creates a GitHub Release on `open-renewables/okf-library-template` marked as a pre-release (OD-9). The release gate compares with `v0.2.0`.
4. **No public site, ever, for the template** (FR8.5, SRS T5). The deploy job exists, is off unless `library.site_url` is set and the tag is v1.0.0 or later (`poe site-deploy-check`), and is proved only on a synthetic public sandbox repository (OD-6).
5. **The consuming skill needs the release tag from inside the archive.** I-12 lists no file that carries it, so an agent given only the archive cannot report it (FR7.2). PP-3 adds a small release-identity file; without it the agent must be told the tag.
6. **`site` is not a required status check.** `validate` stays the only required check (SDD §11) because a path-filtered required check never reports on other pull requests (OD-7).
7. **The first scheduled `stale-report.yml` run is already done** (Monday 2026-11-09, success). P3 reads its output and observes the next one; it does not wait on a schedule.
8. **The template has no `CITATION.cff`, `DECISIONS.md` or `GOVERNANCE.md` today.** `init_library.py` generates the first two; P3 adds `GOVERNANCE.md` and the builder tolerates a missing `CITATION.cff` in the template's own archive (OD-10).

## Exit

SPEC "Done when" 1 to 12: pull requests merged by squash, tag `v0.5.0` pushed by the owner, proposed entries decided, then, on the owner's instruction, the three plan files move to `plan/archive/2026-11-p3-site-release-skills/` and the SRS status is left unchanged.
