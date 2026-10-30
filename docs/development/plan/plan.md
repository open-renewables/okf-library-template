# Plan: build phase P0

Status: **Draft for owner approval.** No spike has started. What is built and why: `SPEC.md` (abbreviations are defined there). Checklist: `todo.md`. Effort figures are indicative, in person-days **[Inf]**; SDD §14 allows 2–3 for P0.

**NEEDS YOU** marks a step that needs a person, account, machine or setting that only the owner can supply. Types: *person*, *account*, *machine*, *setting*.

## Guards

Rules for every spike. The GitHub CLI token on this machine has `admin:org` and `repo` scope, and this repository's remote is `open-renewables`, so a `gh` command run from here could reach the wrong organisation.

1. **Sandbox only.** Run `gh` and `git push` only against `open-renewables-sandbox/p0-spikes` (or a further sandbox repository the owner approves, D-1). Always pass the repository explicitly (`-R open-renewables-sandbox/…` or an `api repos/open-renewables-sandbox/…` path). Never rely on the current directory's default repository.
2. **Wrapper.** Before the first write, create `tools/gh-sandbox.sh` in p0-spikes. It refuses any call whose repository or organisation is not `open-renewables-sandbox` and prints the target before running. All `gh` writes go through it. Reads (`gh repo view`, `gh api` GET) may run directly but still name the repository.
3. **Check, then write.** Each write batch starts with `gh repo view open-renewables-sandbox/p0-spikes --json owner --jq .owner.login` and proceeds only on `open-renewables-sandbox`.
4. **Template repository.** No `gh` command and no spike runs there. The one exception is V-10a, read-only, in a fresh session.
5. **No secrets in the repository.** The V-05 App private key and any Cloudflare token stay outside p0-spikes; the owner adds any repository secret. Nothing is pasted into chat.
6. **Public repository.** Spike content is synthetic. No RE-library or other proprietary concept is committed.
7. **Downloads.** The okf-skills clone, the Zensical and Docusaurus installs and the Docusaurus npm tree go in their own new directories under p0-spikes (git-ignored), pinned by version or commit, with scripts kept elsewhere. Python that reads them runs with `-I`.
8. **Workflows.** Spike workflows follow `../constraints.md` (Workflows row): actions pinned by full SHA, read-only default token, each job declares its own permissions, no `pull_request_target`.
9. **Evidence.** Every result file in p0-spikes records: date, tool and version, exact command, raw output or a link to it, and a label **[Test]**, **[Doc]** or **[Inf]** as in SDD §2.4.

## Order of work

V-03 and V-04 go first because Material for MkDocs ends on 2026-11-05. The shared fixture bundle comes before everything that renders or validates Markdown.

| Wave | Work | Days | Depends on |
| --- | --- | --- | --- |
| 0 | Set up p0-spikes (layout, wrapper, ignore rules); build the shared fixture bundle | 0.25 | Owner approval of D-1 |
| 1 | V-03, V-04 (generator); V-08, V-11 (read-only research); V-02 local part | 1.0 | Wave 0 |
| 2 | V-01, V-02 GitHub part (push, view); V-09; V-12 + V-13 cross-system workflow; V-10b | 1.0 | Wave 0; V-09 and V-10 need fresh sessions |
| 3 | V-05, V-07 (settings and API; App and reviewer from the owner) | 0.5 | D-2, D-3 answered |
| 4 | V-06 (second person), V-10a (fresh session) | 0.25 owner time | Wave 2 notes |
| Exit | Generator recommendation; re-estimate; proposed entries; SDD edits as a diff | 0.5 | All waves |

Waves 1 and 2 have no dependency on each other except for the fixture. Wave 3 waits on the owner.

## Workspace layout in p0-spikes

```
p0-spikes/
├── README.md                    # index of results; one row per V-item
├── tools/gh-sandbox.sh          # guard wrapper (Guards 2)
├── fixtures/bundle/knowledge/   # shared synthetic OKF bundle (Wave 0)
├── spikes/V-NN-slug/RESULT.md   # question, method, evidence, outcome, label, feeds
├── spikes/V-NN-slug/…           # scripts and configs for that item
├── .github/workflows/           # cross-os.yml (V-12, V-13) and per-spike workflows
├── exit/                        # recommendation, re-estimate, proposed entries (drafts)
└── .work/                       # git-ignored: downloads, builds, clones
```

**Shared fixture bundle (Wave 0).** About 8 concepts in two folder levels, two types, `index.md` per folder and a root `index.md` with `okf_version`. It follows I-01 and deliberately includes: colon-namespaced tags (`group:…`); a `Revision history` section; footnotes; `<a id>` anchors before and inside headings, duplicate explicit and automatic ids, a non-ASCII term and a parenthesised term; `/`-rooted and relative links; angle brackets and braces in prose; unknown frontmatter keys; the reserved keys named in FR8.2 check 5; nested lists at two and four spaces; a file name and a folder with spaces. It is original synthetic text.

## Steps by item

### V-03 Zensical (Wave 1) — about 0.5 day

1. In `.work/`, create two environments from `uv`: MkDocs 1.6.1 with Material 9.7.x, and the latest Zensical (0.0.72 or later; record the version and PyPI date). Python 3.12, then repeat the six-check run on 3.11 and 3.14.
2. Use the I-13 baseline `mkdocs.yml` with `docs_dir` set to the fixture bundle. Build with each builder from a separate copy (`--site-dir` is not available in Zensical).
3. For each feature listed in V-03, record the builder's exit code **and** the generated HTML. Judge on output, since Zensical skips unsupported settings without warning. Features: `/`-rooted links (retest the 18 October failure); `validation.links.absolute_links`, `anchors`; `strict`; `extra.status`; `extra.social`; `content.action.edit`; footnotes; `attr_list`; `toc` with permalinks; `tags` with colon tags and the generated page URLs.
4. Run the six FR8.2 checks on the Zensical output: the five rendering checks by inspecting HTML, and check 2 by `/`-rooted links. Offline link check by lychee if installed; otherwise a small Python checker over the HTML (not run from inside the downloaded directory).
5. Add one Zensical-only theme key (for example `theme.variant: classic`) to the shared `mkdocs.yml` and build with MkDocs; record whether it is tolerated.
6. For each failure, try a configuration-only fix from Zensical's documentation; record the fix or the blocker. Record licences of the builder and its locked dependencies against the allowlist.

Evidence: feature × builder matrix; six-check table; versions and dates. **[Test]**.

### V-04 Docusaurus (Wave 1) — about 0.25 day

1. Node 24 is installed. In `.work/`, create a Docusaurus 3.10.x site with `markdown.format: 'detect'`, `docs` pointed at the fixture's `knowledge/`.
2. Build three concepts and the index files. Check: raw `<a id>` kept; unknown frontmatter keys tolerated; `<!-- Maintained by CI -->` comment survives; `/`-rooted links; `index.md` as category landing page; colon-tag permalinks; generation of `tags.yml` from vocabulary; angle brackets, braces and footnotes unchanged; then the six FR8.2 checks.
3. Record build time, the size of the dependency tree, and the licences of direct dependencies. Note that this adds a Node toolchain (SPEC, criterion 3).

Evidence: six-check table; footprint. **[Test]**. Concepts are synthetic unless the owner supplies others (D-5).

### V-02 Nested lists (Wave 1 local, Wave 2 GitHub)

1. Fixture lists: unordered, ordered, mixed, at two and four spaces, with continuation paragraphs and code spans.
2. Render with Python-Markdown at the versions MkDocs and Zensical use; record nesting depth from the HTML. Wave 2: push the fixture and read the rendered view on github.com; corroborate with GitHub's `POST /markdown` endpoint (stateless).
3. Compare. Confirm the four-space rule in I-01, or state the rule that gives equal depth everywhere (for example a sane-lists extension, stack report open item 2).

### V-01 Anchors on GitHub (Wave 2)

1. Push the anchor fixtures. In the browser, open the rendered file and test each case: anchor before a heading, inside it, explicit id equal to GitHub's automatic slug (duplicate ids), non-ASCII term, parenthesised term.
2. For each, record the rendered `id` (GitHub prefixes `user-content-`; note it), whether a `#fragment` link scrolls to the right place, and whether the automatic heading id is still produced.
3. Confirm AD-14's placement and duplicate-id rule or state the rule that holds. Check the same fixture's output in MkDocs, Zensical and Docusaurus (from V-03 and V-04) so FR8.2 check 4 has all four views.

### V-08 okf-skills (Wave 1) — about 0.25 day

1. Clone `okf-skills` at `a8b96420de90d102c43cda1693d01ec4f925f2ab` (the SDD's `okf--v0.10.3` pin) into its own directory under `.work/`; confirm the commit hash and the MIT licence file.
2. Run its validator script outside the Action, locally, against the fixture bundle plus one deliberately broken file per rule it checks. Record each finding's text and exit behaviour.
3. Draft the finding-to-`OKF1xx` mapping for I-09. Record its behaviour on the generated `index.md` files (root index with `okf_version`; folder indexes without frontmatter).
4. Check vendoring: single script or package, its only dependency (PyYAML, per C-03), licence texts to carry, and any network or Action-only assumption.

### V-11 `verified` and tiers (Wave 1) — about 0.1 day

1. Read OKF v0.2 at specification commit `ad30107` and the okf-skills source from V-08. Find where a tier is derived from `verified`, whether from the latest entry or any entry, and the actor prefix for a non-human confirmation.
2. Compare with I-08's `human:<login>` and `ci:<bot>` mapping. Quote at most a short phrase with file and line; summarise the rest.
3. If the specification is silent, say so and describe what okf-skills does instead.

### V-09 Skill symlinks (Wave 2) — about 0.25 day

1. In p0-spikes, add `.agents/skills/demo/SKILL.md` (six specification fields only) and `.claude/skills/demo` as a symlink to `../../.agents/skills/demo`. Commit with the symlink mode (`120000`; check `git ls-files -s`).
2. **Discovery.** Open a fresh Claude Code session with p0-spikes as the working directory and ask for the skill by name. Record whether it is listed and used. Repeat with the symlink replaced by a plain copy, as the control.
3. **Windows.** On this machine `core.symlinks` is `false` (Git for Windows default). Clone p0-spikes freshly and record what the symlink becomes (a text file holding the target) and whether Claude Code still finds the skill. **NEEDS YOU (setting)** for the second case: enabling Windows Developer Mode, or an elevated shell, so `core.symlinks=true` works. It is a system setting, so the owner changes it.
4. **"Use this template".** Mark a sandbox repository as a template and create a repository from it; check `git ls-files -s` in the result. **NEEDS YOU (account)** for the extra repository if D-1 is not already approved.
5. **Release archive.** Build the I-12 style archive and GitHub's own source tarball and zip from a tag; record whether the symlink entry survives in each. (I-12 lists only `.agents/skills/use-bundle/`, so the question is what a template release archive does with `.claude/skills/`.)
6. Linux behaviour comes from the V-12 workflow's checkout. If symlinks fail on any route, specify the AD-16 fallback (`init_library.py` copies the skills) as a proposed entry.

### V-10 Spaces in file names (Wave 2 and 4)

- **10a, read-only, in this repository. NEEDS YOU (person):** open a fresh Claude Code session with `okf-library-template` as the working directory and ask it to summarise the SRS, then to list which of the four `@…` design-document imports in `CLAUDE.md` it loaded (the existing comment in that file anticipates this check). No file is changed. The owner opens the session, or approves one being started once the plan is accepted. This session cannot serve as the check because it did not start there.
- **10b, in p0-spikes:** create a folder tree mirroring `docs/development/` with space-named files. From a nested folder, test: `@path with spaces`, an escaped-space form, a quoted form and an alias file with a hyphenated name, as `CLAUDE.md` imports in a fresh session; and `%20`, angle-bracket and relative link forms in Markdown, viewed on github.com and in the MkDocs and Zensical builds from V-03. Name the form to use. If no import form works, the proposed entry covers the file naming in §6 (QA-36, QA-67).

### V-05 Rulesets and approvals (Wave 3) — about 0.5 day

The sandbox is a free organisation; p0-spikes is public, so rulesets are available. Settings changes are sandbox writes under Guards 1–3.

| Sub-item | Method | Needs |
| --- | --- | --- |
| 5a Bypass modes | Ruleset on `main`: require pull request, 1 approval with code-owner review, squash only. Bypass: repository admin "for pull requests only"; a GitHub App "always". Test: admin merges a pull request without approval; admin direct push is refused; the App pushes to `main` directly | **NEEDS YOU (account):** create the App in the sandbox organisation (browser, about 10 minutes, one repository, `contents: write` and `pull_requests: read` as C-06), keep the private key outside the repository, add it as a repository secret |
| 5b Check naming | Workflow `validate.yml` with job `validate` triggered by `pull_request` and `pull_request_review`; make `validate` required. Record the check-run names for both triggers and whether the required check is satisfied by either | — |
| 5c API shape | For a pull request merged by admin bypass: record `merged_by`, `/reviews` (state, `commit_id`), PR `head.sha`, `merge_commit_sha`, and `commits/{sha}/pulls`. Repeat with an approval given, then a new commit pushed (stale approval) | **NEEDS YOU (account):** a non-author reviewer. Option 1, a second GitHub account of the owner. Option 2, the Actions `GITHUB_TOKEN` approving (needs the sandbox's "allow Actions to create and approve pull requests" setting, currently off). Option 2 shows the API shape but the reviewer is a bot, so option 1 is the faithful test |
| 5d Concurrency | A workflow with a `concurrency` group and `cancel-in-progress: false`; push three commits quickly; record which runs run, queue and cancel. Confirms the "one running, one pending" inference | — |
| 5e Fork privacy | Documentation first **[Doc]**. Empirical only if a fork can be made outside the sandbox organisation | **NEEDS YOU (account):** a second user or organisation to hold a fork, or accept a documentation-only answer (D-3) |

Result confirms or corrects §11, AD-11/AD-12 and W-05 steps 1–6 as worded.

### V-07 Releases and Cloudflare (Wave 3) — about 0.25 day plus waiting

1. **Immutable releases.** In p0-spikes, enable immutable releases (setting write, sandbox only; record the exact setting and whether it is available on Free). Publish a release with assets, then try to edit an asset, delete an asset, move the tag and delete the release; record each result and the error text.
2. **Cloudflare Pages access policy.** Read Cloudflare's documentation for the free plan (Pages previews, Access policy, seat limits) and record the limits and the accessed date **[Doc]**. **NEEDS YOU (account):** a deployment test needs the owner's Cloudflare account and a token kept outside the repository. Without it, the item closes as documentation-only.

### V-12 Reproducible archive and V-13 tasks (Wave 2) — about 0.5 day together

One workflow, `cross-os.yml`, a matrix of ubuntu, macos and windows hosted runners × Python 3.11 and 3.14 (six jobs), plus local runs on this machine (Windows, Python 3.11, 3.12 and 3.14 are installed). **NEEDS YOU (machine):** choose hosted runners only, or add real macOS and Linux machines as a cross-check (D-4). No Docker is installed locally.

- **V-12.** Write a throwaway `build_archive.py` to the I-12 rules: entries sorted by path, modes normalised, owner and group 0 with empty names, modification times set to the tagged commit's timestamp, gzip with no file name and a zero timestamp. Build from the tagged tree objects (`git archive` or `git ls-tree`), not the working tree, so line-ending conversion cannot enter. Tag once; upload each job's SHA-256 as an artifact; a final job compares all six and the local runs. Variables to test deliberately, since each could break equality: line endings (`core.autocrlf` on Windows); file modes without an executable bit on Windows; `tarfile` default format across 3.11 and 3.14; compressor differences between the zlib builds shipped with each Python. If the digests differ, find the smallest settings change that makes them equal, or show that the compressed bytes cannot be equal and state what can be (for example the checksum of the uncompressed tar).
- **V-13.** Throwaway `pyproject.toml` with `[tool.poe.tasks]` mirroring I-16 (`install`, `check`, `test` as stubs that run real tools: `uv lock --locked`, `ruff`, `pytest`) and `.pre-commit-config.yaml` with `repo: local` hooks calling `uv run`. Each job: fresh clone, `uv sync --all-groups`, `uv run poe install`, `uv run poe check`, then a commit that triggers the hooks. Record, per system and version, the first failing command. Watch for shell differences in task definitions (`cmd` versus `shell`), path separators, quoting, and hooks run through Git for Windows' shell. Locally test in PowerShell and in Git Bash.

### V-06 Second person (Wave 4) — owner time

**NEEDS YOU (person).** Write `spikes/V-06-w01/runsheet.md` from SDD W-01 steps 1, 2, 4 (manual equivalent) and 5, with stopwatch fields. The second person follows it on a fresh sandbox repository (D-1) and in the organisation's App settings. Steps 3 and 6 depend on `init_library.py` and CI that do not exist yet, and are marked "not measurable in P0" (SPEC, interpretation 1). Compare the measured steps with W-01's indicative times.

## Needs from you: summary

| Item | Need | Type | Blocks |
| --- | --- | --- | --- |
| All | Approve this plan; D-1 (commits, pushes, settings and extra repositories in the sandbox) | decision | Every spike |
| V-05 | Create the GitHub App; add its secret; non-author reviewer | account | 5a, 5c |
| V-05 | Second user or organisation for the fork | account | 5e |
| V-06 | A second person and about 30 minutes | person | V-06 |
| V-07 | Cloudflare account and token (optional) | account | Cloudflare test |
| V-09 | Enable Windows symlinks (Developer Mode), optional | setting | Windows second case |
| V-09, V-10 | Open or approve fresh Claude Code sessions | person | V-09 step 2, V-10a, V-10b |
| V-12, V-13 | macOS and Linux: hosted runners, or your own machines | machine | Cross-system results |

## Proposed decision entries

Nothing below is written until the owner approves its text. Each is a **proposal** that exists only if the stated outcome occurs; the first two always do. Drafts are held in `p0-spikes/exit/` and presented at the exit. IDs are assigned on approval (next ADR number is ADR-001; the QA- and DR- series is frozen, QA-68).

| # | Trigger | Would change | Form |
| --- | --- | --- | --- |
| P-1 | Always: generator decision from V-03 and V-04 | AD-13, C-07, I-13; QA-26, QA-28, QA-38; `../constraints.md` "Site" row; SRS risk row on tool end of life (wording only if the owner agrees) | ADR-001 (Proposed), superseding or confirming AD-13 |
| P-2 | Always: re-estimate | SDD §14 effort column and §1; QA-45's ranges | DDR change-log row; SDD edit |
| P-3 | V-01 rejects AD-14 placement or duplicate-id rule | AD-14, QA-42; I-01 link rule; FR2.10 and FR8.2 check 4 acceptance wording (a requirement change, so it goes to the owner as a request, not an edit) | ADR superseding AD-14 |
| P-4 | V-02 shows four-space nesting differs | I-01 indentation rule | SDD edit with change-log row; ADR only if two options compete |
| P-5 | V-05 contradicts any of §11, AD-11, AD-12, W-05 or the W-01 fork row | AD-01, AD-11, AD-12; §11; W-04, W-05; W-01 | ADR per decision changed |
| P-6 | V-07 shows immutable releases unavailable on Free, or Cloudflare limits exclude the options | C-10, AD-15, §11 release row and site row | ADR amending AD-15 |
| P-7 | V-08 shows the validator cannot be vendored or runs differently from the Action | AD-08, QA-44, I-09 | ADR amending AD-08 |
| P-8 | V-09 shows symlinks do not survive a route; owner principle 2026-10-30: provider-agnostic core | AD-16, §6 layout, W-10; `init_library.py` scope; V-09 carried item | ADR superseding AD-16 (neutral `AGENTS.md` entry; Claude Code discovery as an optional adapter), or amending it (copy fallback) |
| P-9 | V-10 shows imports or links fail with spaces | `CLAUDE.md` import form; `docs/development/` file naming; QA-36, QA-67, AD-21; SRS "Location" line | ADR superseding the naming decision; SRS edits go to the owner |
| P-10 | V-11 shows OKF derives tiers differently from I-08 | I-08 `verified` mapping; FR3.8 acceptance | SDD edit and ADR |
| P-11 | V-12 shows archives differ across systems | I-12, W-12 step 5, QA-61; FR6.6 and FR7.3 acceptance wording (owner request) | ADR amending QA-61 |
| P-12 | V-13 shows tasks or hooks fail on a system | I-16, I-17, AD-20; FR2.11 | SDD edit; ADR if the tool choice (poethepoet) changes |
| P-13 | V-06 platform steps alone exceed the share of 30 minutes W-01 allows | FR6.1 feasibility; W-01 times | Report to the owner; no entry unless the owner asks |
| P-15 | Added 2026-10-27 from V-10b and V-03: GitHub resolves `/`-rooted links from the repository root, and Zensical leaves them unresolved | I-01 link rule; W-04 check 4; FR2.10 and FR8.2 check 2 wording (requirement-level: goes to the owner as a request, not an edit) | ADR amending I-01 (for example relative links only) |
| P-16 | Added 2026-10-28: V-05 5a and 5c, V-06, V-07 (Cloudflare) and V-09 (real symlink, template flow) carried past P0 with gates | SDD §14 (carried-items table); the v1.0.0 gate still requires them closed | SDD edit in the §14 diff |
| P-17 | Added 2026-10-28 from V-03: MPL-2.0 packages (`pathspec`, `certifi`) in the site stacks | `constraints.md` exception table; licence check wording | ADR |
| P-18 | Added 2026-10-28 from V-13: Windows line endings | SDD §6 layout and P1 deliverables (`.gitattributes`) | SDD edit |
| P-14 | Always: V-01 to V-13 outcomes | SDD §15 outcome column; DDR change log | Change-log rows and a §15 diff, as SDD §14's gate says "recorded in the DDR" (SPEC, interpretation 5) |

## Exit steps

1. Collect `RESULT.md` files into the p0-spikes `README.md` index; check every V-item is answered or has a named reason it cannot be.
2. Write the generator recommendation against the SPEC criteria. Owner direction, 2026-10-28: keep MkDocs blocking with Zensical built in parallel (option A, AD-13 as written), expecting the release site to be Zensical later; the Zensical checks are not rerun in P0, and the known issues are carried as a list (`p0-spikes/exit/generator-recommendation.md`).
3. Re-estimate P1 to P4 from observed effort and findings.
4. Draft the proposed entries (P-1, P-2, P-14 and any triggered), plus the SDD §15 and §14 edits as a diff. Do not apply them.
5. Present to the owner. Apply only what is approved, each as its own ADR file or documented edit, in a docs-only pull request (`../conventions.md`, Git).
6. On the owner's instruction: move `SPEC.md`, `plan.md` and `todo.md` to `plan/archive/2026-10-p0-verification/`. Do not ask for the SRS status to change.

## Risks

| Risk | Effect | Response |
| --- | --- | --- |
| Zensical changes between the spike and the P0 exit | Stale evidence (0.0.73 is dated 2026-10-26; 0.0.72 to 0.0.73 took one day) | No P0 rerun (owner, 2026-10-28). Version and date are recorded; the parallel non-blocking Zensical job with output checks (W-08) re-tests every change from P3 |
| Zensical ignores unsupported settings silently | A pass on exit code is false | Judge on HTML output (V-03 step 3) |
| Material ends on 2026-11-05 before the decision | Pressure to decide early | V-03 and V-04 first; the decision still waits for all evidence |
| Owner-dependent steps (V-05 App and reviewer, V-06 person) stall | P0 overruns the 2–3 days | Do all other waves first; ask for the App and reviewer at the start |
| The token on this machine reaches both organisations | A write lands in `open-renewables` | Guards 1 to 3 |
| p0-spikes is public | Disclosure of proprietary text | Synthetic content only (Guards 6) |
| Hosted-runner results differ from the owner's hardware | Missed local-only failures | Optional real-machine cross-check (D-4) |

## Decisions needed from the owner

| ID | Question | Default if not answered |
| --- | --- | --- |
| D-1 | May spikes commit and push to p0-spikes, change its settings, and create further throwaway repositories in `open-renewables-sandbox` (V-06, V-09 template flow)? | Commits and settings in p0-spikes only; no extra repositories, so V-06 and V-09 step 4 wait |
| D-2 | V-05 reviewer: second account, or the Actions token approving? | Actions token for API shape; second account later |
| D-3 | V-05 fork: supply a second user or organisation, or accept documentation only? | Documentation only |
| D-4 | V-12 and V-13: hosted runners only, or also your own macOS and Linux machines? | Hosted runners only |
| D-5 | V-04 concepts: synthetic, or supply three public-safe real concepts? | Synthetic |
| D-6 | V-06: accept the reduced P0 scope (SPEC, interpretation 1)? | Reduced scope |
| D-7 | Accept the proposed generator criteria in the SPEC, and outcome recording as change-log rows (interpretation 5)? | Both as written |
