# Todo: build phase P0

Checklist for `plan.md`; scope and done-when in `SPEC.md`. Tick an item when its `RESULT.md` exists in `open-renewables-sandbox/p0-spikes` and the table row below holds a one-line outcome. **NEEDS YOU** marks a person, account, machine or setting from the owner.

## Before any spike

- [x] Owner reviews `SPEC.md`, `plan.md` and `todo.md`
- [x] Owner answers D-1 to D-7 (`plan.md`, "Decisions needed from the owner")
- [x] Owner accepts or changes the generator criteria (`SPEC.md`, "Site generator decision")

## Wave 0: set up (0.25 day)

- [x] Confirm the target: `gh repo view open-renewables-sandbox/p0-spikes --json owner` returns `open-renewables-sandbox`
- [x] Create `tools/gh-sandbox.sh` and test that it refuses another organisation
- [x] Create the `p0-spikes` layout, `.gitignore` (`.work/`), index `README.md`
- [x] Build the shared synthetic fixture bundle

## Wave 1: local and read-only

- [x] V-03 Zensical: feature × builder matrix; six FR8.2 checks; Zensical-only key in MkDocs; licences
- [x] V-04 Docusaurus `detect` mode: six FR8.2 checks; footprint
- [x] V-08 okf-skills at `a8b96420…`: finding mapping; index files; vendoring check
- [x] V-11 `verified` tier derivation: rule or silence, with file and line
- [x] V-02 nested lists: Python-Markdown part

## Wave 2: GitHub sandbox and fresh sessions

- [x] V-01 anchors rendered on github.com
- [x] V-02 nested lists: GitHub part, compared with Wave 1
- [x] V-09 skill symlinks: discovery in a fresh session; Windows default; release archive. Real-symlink and "Use this template" parts dropped: owner decision 2026-10-30, provider-neutral core (P-8)
- [x] V-10b link and import forms in p0-spikes; form named (round 2 passed)
- [x] V-12 reproducible archive: six matrix digests plus local runs (**NEEDS YOU: machine**, D-4)
- [x] V-13 poethepoet and `repo: local` hooks on the same matrix (**NEEDS YOU: machine**, D-4)

## Wave 3: needs the owner

- [ ] V-05 5a bypass modes (**NEEDS YOU: account**, create App, add secret)
- [x] V-05 5b required-check naming across `pull_request` and `pull_request_review`
- [ ] V-05 5c API shape of bypass merge, review `commit_id`, stale approval (**NEEDS YOU: account**, reviewer, D-2)
- [x] V-05 5d concurrency-group cancellation
- [x] V-05 5e fork privacy (documentation only, D-3 default)
- [x] V-07 immutable releases on Free: edit, delete, retag after publish
- [ ] V-07 Cloudflare Pages free-plan limits: documentation read, free-plan statement and seat limit not found (**NEEDS YOU: account** for a test)

## Wave 4: needs a person

- [ ] V-06 run sheet written (**NEEDS YOU: person**) and second person's times recorded for W-01 steps 1, 2, 4 and 5
- [x] V-10a fresh session in this repository: SRS summary and import check, read-only (**NEEDS YOU: person**)

## Exit

- [x] ~~Rerun the six FR8.2 checks on the then-latest Zensical release~~ Dropped by the owner, 2026-10-28; known issues listed instead
- [x] Generator recommendation written against the SPEC criteria (`p0-spikes/exit/generator-recommendation.md`; ADR-001 draft inside, Proposed)
- [x] Re-estimate of P1 to P4 written (`p0-spikes/exit/re-estimate.md`: 30.5–45.5 remaining, 33–49 programme)
- [x] Proposed entries drafted in `p0-spikes/exit/` (P-1 in the recommendation; P-2, P-5, P-8 to P-11, P-14 to P-18 in `proposed-entries.md`)
- [x] SDD §1, §14 and §15 edits drafted as a diff, not applied (`p0-spikes/exit/sdd-s1-s14-s15.diff`; `git apply --check` passes)
- [x] Present to the owner; owner approved all entries on 2026-10-30 (P-11 and P-15 as recommended). Applied in the working tree, uncommitted: SDD diff plus line edits (P-5, P-8, P-10, P-11, P-15, P-18), ADR-001 to ADR-006, `CLAUDE.md` imports, `constraints.md`, DDR change-log row
- [ ] **NEEDS YOU:** edit SRS FR2.10 and FR8.2 check 2 for relative-only links (ADR-005 is conditional on it)
- [ ] Commit, push and open the docs-only pull request (on the owner's instruction; nothing committed yet)
- [ ] On the owner's instruction, move the three plan files to `plan/archive/2026-10-p0-verification/`

## Outcomes

One line per item when closed: result, label (**[Test]**, **[Doc]**, **[Inf]**), proposed entry if any.

| ID | Outcome | Label | Entry |
| --- | --- | --- | --- |
| V-01 | AD-14 holds on GitHub (explicit ids kept, duplicates accepted, ids lower-cased); scroll to 3 of 9 targets unconfirmed | [Test] | none |
| V-02 | Four-space nesting identical on GitHub, MkDocs, Zensical, Docusaurus; two-space differs | [Test] | none |
| V-03 | Zensical 0.0.73 fails check 2 (`/`-rooted links emitted verbatim; no config fix); other tested features equal to MkDocs; MPL-2.0 packages in both stacks | [Test] | P-1 |
| V-04 | Docusaurus 3.10.2 passes 5 of 6; fails check 5 (`slug`/`id` change URLs); Node toolchain, 1,274 packages, licences off the allowlist | [Test] | P-1 |
| V-05 | Partial: 5a admin half, 5b, 5d, 5e done; App half and 5c approval cases need the owner; commit-to-PR lookup lagged about 20 s | [Test]/[Doc] | P-5 (small) |
| V-06 |  |  |  |
| V-07 | Immutable releases work on Free (public repo): assets, tag and reuse locked; notes editable, release deletable; Cloudflare limits unconfirmed | [Test]/[Doc] | none |
| V-08 | Vendorable single script, same as the Action; no finding codes; tolerates offset-less datetimes | [Test] | none |
| V-09 | Symlinks survive git, archives, Linux/macOS/hosted Windows; symlink-less Windows checkout breaks Claude Code skill discovery. Owner decided 2026-10-30: provider-neutral core, Claude Code discovery as an optional adapter (P-8, ADR pending) | [Test] | P-8 |
| V-10 | Template CLAUDE.md imports do not load; only the escaped-space form worked, confirmed in round 2 with hyphens and nesting; GitHub resolves rooted links from repo root | [Test] | P-9, P-15 |
| V-11 | Tier from any human: entry; ci: accepted, process: is the convention | [Test/Doc] | P-10 (wording only) |
| V-12 | Tar identical on 8 runs; tar.gz differs under zlib-ng (Python 3.14, Windows) | [Test] | P-11 |
| V-13 | Passed on 3 systems x 3.11/3.14; bare poe exits 1; .gitattributes and .python-version needed | [Test] | none |
| Generator | Option A confirmed by the owner (2026-10-28): MkDocs blocking, Zensical parallel and non-blocking, release site expected to be Zensical later; Zensical fails check 2 at 0.0.73, so the switch waits on the link rule (P-15) | [Test] | P-1 (ADR-001 draft) |
| Re-estimate | P1 to P4 remaining 30.5–45.5 person-days (P1 11–16, P2 9.5–14.5, P3 5–7, P4 5–8); programme 33–49, overlapping the review's 35–55 | [Inf] | P-2 |
