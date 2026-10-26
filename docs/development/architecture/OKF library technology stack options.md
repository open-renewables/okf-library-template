---
name: OKF library technology stack options
description: Research report comparing Python-centred, Node/TypeScript-centred and minimal (Hugo and Go) reference stacks for the OKF library template, with site-generator compatibility tests, GitHub free-tier platform findings, delivery and supply-chain analysis.
author: Richard Gledhill
type: report
created: 2026-10-18
modified: 2026-10-25
draft: false
confidential: false
tags:
aliases:
  - Technology stack options report
---
# Python scripts lead; the site generator stays open

The best reference stack for the OKF library template and the RE risk library is **Python-centred**. The profile scripts would be single-file Python 3.11+ scripts (PEP 723, run with `uv` or plain `python3`) using markdown-it-py, jsonschema and a YAML 1.2 loader. The external checker, okf-skills, would be pinned by commit SHA. Instantiation would use a GitHub template repository with a small init and setup script. **The site generator decision would wait until the v1.0.0 site.** MkDocs 1.6.1 with Material 9.7.x would be used for local previews now, because it is the only generator that has passed all six OKF compatibility checks in a test build. Zensical, Material's successor, would build the same project in parallel from the same `mkdocs.yml`, which the Zensical project documents as its recommended migration path, so the switch can be made when Zensical's output matches. Python wins on ecosystem fit rather than capability. The pinned conformance checker, Google's reference tooling and the most portable Agent Skills script language are all Python, and the core of the work is bespoke in every stack: body-section, vocabulary, uid-registry, index and revision logic, about 2–3 weeks. The Node/TypeScript stack is a credible alternative: it has the best Markdown AST, the largest OKF package pool and the best-fitting Docusaurus. It carries the heaviest supply-chain exposure after the 2025–2026 npm compromises, and it still needs Python in CI for okf-skills. The minimal-dependency stack (Hugo, lychee and a Go profile tool) has the smallest supply chain, but it moves most of the work into verbose bespoke Go and Go templates. Hugo's `index.md` leaf-bundle rule also needs a pre-build workaround, which works in testing. The research also settles several platform questions the design left open:

- **No GitHub author, of any role, can approve their own pull request.** QA-29 resolves against the owner's understanding.
- **Protected branches, rulesets and code owners are public-only on GitHub Free.** QA-16 is confirmed.
- **The post-merge bot needs a GitHub App** on a ruleset bypass list once `main` is protected (QA-17).
- **`{#id}` heading IDs cannot satisfy DR-10.** Only inline HTML anchors are documented to work on GitHub and the candidate generators.
- **OKF now requires timestamps to be datetimes with a UTC offset.** This changes `stale_after` and `verified.at`.
- **An access-controlled alpha or beta site is not possible on GitHub Pages** without Enterprise Cloud.

*Updated 20 October 2026: section "MkDocs and Zensical can run in parallel from one configuration" added, with matching changes to the recommended stack, open items and implied design changes.*

*Updated 25 October 2026 (DDR QA-38, QA-50): frontmatter added; a note on how the recommendation was adopted; Material for MkDocs end-of-life date added; a paragraph on PyPI supply-chain incidents added to the supply-chain comparison. The report is otherwise kept as evidence at its original date.*

*Updated 25 October 2026, later (DDR QA-52 to QA-65, QA-74): a note on developer tooling, local-only operation and template engines, below. The tables are kept as evidence at their original date.*

**Developer tooling and local-only operation (25 October 2026).** A comparison with [osprey-oss/cookiecutter-uv](https://github.com/osprey-oss/cookiecutter-uv) (MIT; tag 0.0.12, 10 April 2026; repository cloned and read) found that the design did not say how tasks, linting, type checks, pre-commit or a local site preview are run. The SDD now adds poethepoet tasks in `pyproject.toml` (poethepoet 0.49.0, MIT, read from the wheel), ruff with cookiecutter-uv's rule set, mypy, `repo: local` pre-commit hooks, a Python 3.11 and 3.14 test matrix, and CI jobs that only call those tasks (AD-20). cookiecutter-uv is a conventions reference only; no files are copied. A `platform: git-local` mode lets a library run without GitHub, with provenance from commit trailers and releases as annotated tags (AD-19). Copier and Cookiecutter were reassessed and not adopted (AD-10 kept). The GPL-3 point below still holds for Copier 9.19.1, which requires `jinja2-ansible-filters` 1.3.2 (GPL3), but it applies only when Copier is a locked dependency, not when it is run as an external tool with `uvx`. Security additions: the gitleaks CLI in CI and, where installed, locally; pip-audit on lock changes and weekly.

**How the recommendation was adopted.** The template's Software Design Document (`OKF Library Template - Software Design Document.md`) adopted this stack as architecture decisions AD-01 to AD-16 (DDR DR-21), with one change: instead of independent single-file PEP 723 scripts, the tooling is one shared Python module, `okfprofile`, with thin command-line scripts, locked with `uv`, to avoid duplicating parsing and profile-loading code. Later amendments are recorded in `OKF Library Template - Design Decision Record.md`.

Evidence labels used throughout: **[Doc]** means verified against primary documentation or registry metadata; **[Test]** means verified by a local test build or execution run by the researchers on 18 October 2026; **[Inf]** means inferred and not verified.

## The bespoke profile layer, not the stack, sets the effort

All three stacks meet every functional requirement (FR1–FR7) on free tiers. None fails a requirement outright. What separates them is how they handle the parts the design actually needs built. Existing CLIs cover only part of the six-check validation pipeline:

- **Check 1 (OKF conformance)** is covered by okf-skills.
- **Check 2 (frontmatter schema)** is covered by JSON Schema tools.
- **Link and anchor resolution in check 4** is covered by lychee or similar.

Everything else is bespoke in every stack:

- **Check 3:** body sections, the nine strictly ordered H2s of the Risk type, the Controls, Evidence and Checks bullet formats, and the Pass/Flag/Automatable sub-bullets.
- **The rest of check 4:** vocabulary membership and path rules.
- **Check 5:** index freshness.
- **Check 6:** the uid registry.
- **The publishing rules.**
- **The four scripts:** `new_concept`, `validate_profile`, `build_indexes` and `write_revision`.

No generic tool validates Markdown body structure against a declaration **[Doc/Inf]** ([okf-skills validator](https://github.com/scaccogatto/okf-skills/blob/main/skills/validate/scripts/okf_validate.py); [check-jsonschema usage](https://check-jsonschema.readthedocs.io/en/stable/usage.html)). The design's estimate of about 2–3 weeks for the profile scripts therefore holds across stacks. The language choice changes how pleasant that work is, not whether it is needed.

**Python is the most direct fit for that work.** markdown-it-py 4.2.0 (MIT, released May 2026) with mdit-py-plugins 0.6.1 exposes a token stream with nesting levels **[Doc]** ([PyPI markdown-it-py](https://pypi.org/project/markdown-it-py/)). In a test against an OKF-shaped bundle mirroring the RE Risk template it did the following **[Test]**:

- returned the H2 sequence in order;
- separated top-level Checks bullets (level 3) from their sub-bullets (level 5);
- exposed `strong_open` and `code_inline` for the Controls and Evidence formats;
- extracted footnote references for the "stable requires citation" rule;
- parsed 600 files in about 0.6 s.

jsonschema 4.26.0 validated the full RE Risk frontmatter schema, including `additionalProperties: false`, the `^RSK-\d{4}$` pattern and colon-tag patterns **[Test]** ([PyPI jsonschema](https://pypi.org/project/jsonschema/)).

The one material pitfall is **PyYAML's YAML 1.1 type coercion**. In testing, `status: no` became `False` and an unquoted `stale_after: 2027-01-01` became a `datetime.date`, which then failed a `type: string` schema check **[Test]**. ruamel.yaml in YAML 1.2 mode kept such values as strings **[Test]**. The validator must load with YAML 1.2 semantics or cast values to strings before validation.

**Node/TypeScript has the stronger AST but the weaker basic packages.** unified/remark gives typed mdast nodes for every check, and it is the same parser family Docusaurus and Astro use internally. That reduces "passes CI, renders differently" risk **[Doc/Inf]** ([npm @docusaurus/mdx-loader](https://registry.npmjs.org/@docusaurus/mdx-loader/latest)). Ajv 8.20.0 is the reference JSON Schema validator **[Doc]** ([npm ajv](https://registry.npmjs.org/ajv)). However, the obvious choices are stale:

- **gray-matter**, the de facto frontmatter parser, has not been released since April 2021. It pulls in js-yaml 3.x, which has 2025–2026 advisories, including prototype pollution and quadratic-CPU issues **[Doc]** ([npm gray-matter](https://registry.npmjs.org/gray-matter); [GHSA-2883-xcg3-v3hh](https://github.com/advisories/GHSA-2883-xcg3-v3hh)).
- **ajv-cli** has not been released since 2021 **[Doc]** ([npm ajv-cli](https://registry.npmjs.org/ajv-cli)).

The `yaml` package (zero dependencies) or `@11ty/gray-matter` are the maintained substitutes **[Doc]**. Docusaurus itself has moved to `@11ty/gray-matter`.

**The minimal-dependency stack is minimal only in tooling.** In testing:

- yq extracted frontmatter and check-jsonschema enforced the Risk schema **[Test]**.
- lychee 0.24.2 resolved `/`-rooted links, auto slugs, `{#id}` and `<a id>` anchors offline, in about 1 ms for 12 links **[Test]** ([lychee root-dir recipe](https://lychee.cli.rs/recipes/root-dir/)).

However, check-jsonschema is Python-only, so Python enters this stack anyway unless a Go schema library replaces it **[Doc]** ([PyPI check-jsonschema](https://pypi.org/project/check-jsonschema/)). The bespoke code would be roughly 1,000–2,000 lines **[Inf]**. Go is realistic for it, sharing Goldmark with Hugo. Shell plus yq is not realistic: H2 sequencing, nested bullet rules and uid-registry diffing are fragile and hard to test in shell **[Inf]**.

The OKF and agent ecosystem tips the balance:

- **okf-skills**, the checker QA-25 pins, is a set of Python ≥3.11 PEP 723 scripts whose only dependency is PyYAML. It ran standalone with `python3` and no `uv` **[Doc/Test]** ([okf-skills README](https://github.com/scaccogatto/okf-skills/blob/main/README.md)).
- **Google's reference tooling** is a Python proof-of-concept producer and viewer, not a validator **[Doc]** ([OKF pyproject.toml](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/pyproject.toml)).
- **The Agent Skills specification** names Python, Bash and JavaScript as the common script languages **[Doc]** ([Agent Skills specification](https://agentskills.io/specification)).
- **By package count, third-party OKF tooling is mostly TypeScript.** About a dozen npm packages exist. One of them, `@okfit/profiles`, is the closest prior art to the template's profile layer, though it hard-codes a single profile **[Doc]** ([npm search](https://registry.npmjs.org/-/v1/search?text=okf%20open%20knowledge%20format&size=15); [okfit](https://github.com/spencerbeggs/okfit)).

Language choice need not follow the checker, because CI can run both. But a Python template runs one runtime end to end, and a TypeScript one cannot avoid Python in CI.

| Criterion (design reference) | Python-centred | Node/TypeScript-centred | Minimal (Hugo + Go/lychee) |
| --- | --- | --- | --- |
| FR1 / QA-25 okf-skills fit | Same language; can vendor (MIT) if it lapses **[Doc]** | Python still needed in CI **[Doc]** | Composite action or Python script **[Doc]** |
| FR2 body/format checks | markdown-it tokens, tested **[Test]** | mdast tree checks **[Inf]** | Bespoke Go; shell unrealistic **[Inf]** |
| FR2 schema (JSON Schema, language-neutral) | jsonschema, tested **[Test]** | Ajv **[Doc]** | check-jsonschema (Python) or Go library (unverified) |
| FR6 instantiation < 30 min | Template repo + script; Copier optional (0.6 s generation) **[Test]** | Template repo + `npm run init` **[Inf]** | Template repo + checklist/script **[Inf]** |
| FR7 skill scripts portability | Highest **[Doc/Inf]** | Requires Node in runtime **[Inf]** | Bash/binary **[Inf]** |
| Best site fit | MkDocs Material: all six checks pass, but frozen lifecycle **[Test]** | Docusaurus (CommonMark mode) **[Doc]** | Hugo with workaround **[Test]** |
| Supply-chain surface | Moderate (69 packages with all tools) **[Test]** | High at the site layer **[Doc]** | Smallest **[Inf]** |
| Main weakness | Site-generator lifecycle | npm compromises; experimental CommonMark mode | Bespoke Go and Go templates; manual binary bumps |

## No generator passes all six compatibility checks without configuration

The design requires the generator to render the bundle unchanged and to pass six checks (Template SRS, Publishing website). **Material for MkDocs is the only candidate that passed all six in a test build.** It used MkDocs 1.6.1 and Material 9.7.7 with this configuration: `docs_dir: knowledge`, `validation.links.absolute_links: relative_to_docs`, footnotes, attr_list/toc, and the tags plugin **[Test]**.

| Check | Result | Notes |
| --- | --- | --- |
| 1. `index.md` as landing page | Pass | `knowledge/index.md` and folder `index.md` files became landing pages |
| 2. `/`-rooted links | Pass with configuration | `/glossary.md#…` was rewritten to a relative route |
| 3. Non-standard keys | Pass | Kept and ignored |
| 4. Anchors | Pass | Explicit anchors were kept; a missing anchor aborted a `--strict` build |
| 5. Reserved keys and colon tags | Pass | `status` became a navigation badge class, without changing its meaning; colon tags produced valid tag pages with lossy anchors (`groupsolar-pv`) |
| 6. Dialect | Pass | `<1000 V and {braces}` rendered literally; footnotes rendered |

The problem with Material is its lifecycle, not its function:

- **Material entered maintenance mode on 11 November 2025.** It promised critical fixes for "12 months at least", which runs to about November 2026 **[Doc]** ([Material blog](https://squidfunk.github.io/mkdocs-material/blog/)). *Update 25 October 2026:* the Material for MkDocs 9.7.7 release notes state that it is scheduled to reach end of life on 5 November 2026, with maintenance limited to critical bug fixes and security updates until then **[Doc]** ([mkdocs-material 9.7.7 release notes, reproduced in a Dependabot pull request](https://github.com/cms-cat/mkdocs-material/pull/229)).
- **MkDocs 1.x has had no release since August 2024.** MkDocs 2.0 pre-releases remove the plugin system and will not run Material **[Doc]** ([PyPI mkdocs](https://pypi.org/project/mkdocs/); [Material blog: MkDocs 2.0](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/)). That account comes from an interested party.
- **Zensical, the declared successor, is not ready.** It is MIT-licensed and very active, with 55 releases in 2026, but still classed Alpha at 0.0.71 **[Doc]** ([PyPI zensical](https://pypi.org/project/zensical/)). In the same test it built the bundle in 0.22 s, but **emitted all `/`-rooted links verbatim and so failed check 2** **[Test]**. *Update 25 October 2026:* the latest release is 0.0.72, published on 23 October 2026 **[Doc]**.

The Node candidates:

- **Docusaurus 3.10 fits the "unchanged files" rule** in most respects, on documentation and source reading only. It points its docs plugin at `knowledge/`, resolves `/`-rooted `.md` links from the content root, and turns `index.md` into category landing pages **[Doc]** ([Docusaurus links](https://docusaurus.io/docs/markdown-features/links)). Colon tags get the permalink `group-solar-pv` through lodash `kebabCase` **[Doc, source inspection]**.
- **Docusaurus must run with `markdown.format: 'detect'`.** By default it parses every `.md` file as MDX, so `<title>`-style placeholders, prose braces and the `<!-- Maintained by CI -->` comment would break the build. CommonMark mode is labelled experimental **[Doc]** ([Docusaurus Markdown features](https://docusaurus.io/docs/markdown-features); [config API](https://docusaurus.io/docs/api/docusaurus-config)).
- **Starlight 0.42 needs the most add-ons.** It is pre-1.0, its loader is fixed to `src/content/docs/`, it requires `title` on every page, it has no native tags, and it does not rewrite `.md` links without a plugin **[Doc, source inspection]** ([npm @astrojs/starlight](https://registry.npmjs.org/@astrojs/starlight); [Starlight frontmatter](https://starlight.astro.build/reference/frontmatter/)).
- **VitePress** passes checks 1, 2 and 4 by default on documentation. It compiles Markdown to Vue, which makes `{{ }}` and tag-like prose a risk **[Doc/Inf]** ([VitePress routing](https://vitepress.dev/guide/routing)).

**Hugo is viable only with a workaround.** OKF's `index.md` makes a Hugo leaf bundle, which suppresses every sibling page. A test confirmed that a root `index.md` rendered only the home and tag pages **[Doc/Test]** ([Hugo page bundles](https://gohugo.io/content-management/page-bundles/)). Two steps fixed this without touching source files **[Test]**:

- a mount filter that excludes `index.md`;
- a pre-build step that copies each `index.md` to `_index.md` in a generated mount.

A six-line custom link render hook made the build fail on unresolved links **[Test]**. Colon tags produced `/tags/groupsolar-pv/` with odd title-casing. The reserved `type` key changes Hugo's content type, which templates can absorb **[Test]**. Because Hugo releases a minor version roughly monthly, some with breaking changes, the version must be pinned exactly **[Doc]** ([Hugo releases](https://github.com/gohugoio/hugo/releases)).

**Check 4 is a design constraint, not a generator choice.** GitHub documents only HTML anchors (`<a name="…"></a>`) for custom anchors. It auto-generates slugs by lower-casing, replacing spaces with hyphens and removing other punctuation **[Doc]** ([GitHub basic formatting](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)). It does not document `{#id}`, and a forum report says `{#id}` shows as literal text **[Doc, secondary; not tested]** ([CommonMark forum](https://talk.commonmark.org/t/how-to-give-a-custom-id-to-a-heading/3766)).

Inline `<a id="term"></a>` works in every candidate that passes raw HTML **[Test for Material and Hugo; Doc for others]**. Hugo additionally needs `renderer.unsafe = true`. GitHub prefixes such ids with `user-content-` and scrolls to them through JavaScript **[Doc, older issue]** ([html-pipeline #135](https://github.com/jch/html-pipeline/issues/135)). Writing the explicit id equal to GitHub's auto-slug of the term makes links work even where HTML is stripped **[Inf]**.

One dialect risk sits with authoring rather than the generator. Bare `<word>` text in prose is treated as raw HTML by every CommonMark parser, GitHub's included, so the authoring lint should require code spans or escapes **[Inf, consistent with the Hugo test]**. Separately, the Risk template's two-space nested sub-bullets under *Checks* may flatten in Python-Markdown, which expects four-space indentation **[Inf; not tested]**.

## MkDocs and Zensical can run in parallel from one configuration

**Zensical is designed to be adopted alongside an existing MkDocs project, not instead of it.** Its migration guide states that "Zensical reads the existing `mkdocs.yml`, so the same project can be built with either command", and that "moving to `zensical.toml` is not required as part of adopting Zensical" **[Doc]** ([Zensical: migrating from MkDocs](https://zensical.org/docs/compatibility/mkdocs/migration/)). The guide recommends a gradual, reversible path:

1. Keep the existing MkDocs build unchanged.
2. Build the same project with Zensical using the current `mkdocs.yml`.
3. Compare representative pages, navigation, search and customisations.
4. Confirm every MkDocs plugin in use is supported.
5. Switch local and CI commands only when confident in the output.

Page paths, directory URLs and navigation stay the same, and `docs_dir` and `site_dir` keep their meaning **[Doc]**. Settings added during the transition should use the `mkdocs.yml` form so that both builders read them **[Doc]**.

**The template's site configuration avoids the features Zensical does not support.** Against the migration guide and the plugin compatibility page **[Doc]** ([Zensical: MkDocs plugins](https://zensical.org/docs/compatibility/mkdocs/plugins/)):

| Feature | Zensical position | Template use |
| --- | --- | --- |
| `docs_dir: knowledge` | Supported; paths and URLs unchanged | Required **[Doc]** |
| `tags` plugin | Supported natively, with legacy options (`tags_file`, `tags_compare`, export) silently ignored | Required for colon tags; legacy options not needed **[Doc/Inf]** |
| `search` plugin | On by default; only `enabled` and `separator` honoured | Default sufficient **[Doc/Inf]** |
| `hooks` | Not supported | Not used **[Inf]** |
| `gen-files` plugin | Not supported | Not needed: `build_indexes` commits `index.md` files before the build **[Inf]** |
| Template overrides | MiniJinja instead of Jinja; Material ≥9.6.18 overrides generally work unchanged | None planned for previews **[Doc/Inf]** |
| Theme | `theme.variant: classic` keeps Material's appearance | Optional **[Doc]** |
| `gh-deploy`, `get-deps`, `--site-dir` | Not provided; use host-specific publishing, `pyproject.toml` and `site_dir` | Not used: no public site before v1.0.0 **[Doc/Inf]** |
| `validation.links.absolute_links`, footnotes, `attr_list`, `toc`, strict mode | Not addressed on either page | Needed for checks 2, 4 and 6; **unverified** |

**Zensical ignores unsupported configuration without warning, so a successful Zensical build does not prove compatibility.** The plugin page states that configuration for unlisted plugins is "silently ignored", and that ignored settings are skipped "without value validation or warnings"; only unknown settings of a supported plugin raise an error **[Doc]**. The 18 October test, in which Zensical emitted `/`-rooted links verbatim and failed check 2, is consistent with `validation.links.absolute_links` being one such ignored setting **[Inf; not confirmed]**. A parallel Zensical build must therefore be judged on its output, not its exit code.

**Proposed parallel set-up** **[Inf, low effort: about half a day]**:

- **One shared `mkdocs.yml`** at the repository root, using only settings documented for both builders where possible; `theme.variant: classic` only if a test shows MkDocs and Material tolerate the key.
- **Two pinned dependency groups** in `pyproject.toml`: `mkdocs==1.6.1` with `mkdocs-material` 9.7.x, and an exact `zensical` 0.0.x version (it is alpha, so every release can change behaviour).
- **Two CI jobs on separate runners**, so both can write the same `site_dir` without collision:
  - MkDocs `build --strict`: the authoritative preview build, and blocking.
  - Zensical `build`: non-blocking (`continue-on-error`), followed by an offline lychee check of the generated HTML for links and anchors and a comparison of the page list against the MkDocs output. These assertions turn silent omissions into visible failures.
- **Locally,** build with one command at a time, or point a second run at a copy, because `--site-dir` is not available in Zensical.
- **Switch criterion:** make Zensical blocking and MkDocs non-blocking when the Zensical job passes all six compatibility checks on the pilot bundle; retire MkDocs at the v1.0.0 site decision.

**The parallel route reduces, but does not remove, the lifecycle risk.** Material's maintenance commitment of "12 months at least" from 11 November 2025 runs to about November 2026, likely before the RE library's v1.0.0 **[Doc/Inf]**. Because the pre-v1.0.0 site is a local or artifact preview and is not public, running a frozen MkDocs build for a few more months carries little exposure; the main residual risks are build-time dependency advisories and Zensical's alpha churn **[Inf]**. Zensical Studio, an authoring tool that works with both MkDocs and Zensical projects and whose beta ends on 5 November with paid editions to follow, is not needed for this route **[Doc]**. *Update 25 October 2026:* with end of life fixed at 5 November 2026, the template's build will start after Material stops receiving fixes, so the SDD moves the generator decision to the end of its verification phase (DDR QA-38).

## GitHub Free confirms the private-library plan and overturns the self-approval assumption

**QA-29 resolves against the owner's understanding.** GitHub states without qualification that "pull request authors cannot approve their own pull requests". Separately, "repository owners and administrators can merge a pull request even if it hasn't received an approving review" **[Doc]** ([GitHub Docs: approving with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)). For a single maintainer, a self-approval is therefore an admin merge past the review rule. No approval event exists, so:

- the "rerun when a review is submitted" path (QA-23) never fires for self-approval;
- CI must determine approval at or after merge, from the review list plus `merged_by` **[Inf]**;
- the maintainer must not enable "Require approval of the most recent reviewable push" or "Do not allow bypassing", or they could not merge their own pull requests **[Doc/Inf]** ([About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)).

**QA-16 is confirmed.** On GitHub Free, protected branches, rulesets and code owners apply only to public repositories **[Doc]** ([About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets); [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)). While the RE library is private, nothing blocks merging a failing pull request. The validator should therefore also run on push to `main` and fail loudly **[Inf]**.

Native secret scanning and CodeQL are free only on public repositories. Private repositories need Secret Protection (USD 19 per active committer per month) or Code Security (USD 30), sold only with Team or Enterprise **[Doc]** ([GitHub changelog 2025-03-04](https://github.blog/changelog/2025-03-04-introducing-github-secret-protection-and-github-code-security/)). The private library therefore needs a CI secret and pattern scanner until v1.0.0. That matters given the RE library SRS's "confidential project data" risk.

Actions minutes are no constraint:

- unlimited on public repositories;
- 2,000 minutes a month on private Free repositories **[Doc]** ([GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions));
- for comparison, 300 three-minute runs use about 900 minutes **[Inf]**.

**QA-17 needs a GitHub App once `main` is protected.** Pushes made with `GITHUB_TOKEN` do not trigger further workflows, which conveniently prevents loops. However, the documented ruleset bypass actors are roles, teams, GitHub Apps and Dependabot, not `GITHUB_TOKEN` **[Doc; exclusion inferred]** ([Triggering a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow); [Creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)). The documented route is a GitHub App token minted with `actions/create-github-app-token` **[Doc]** ([GitHub App in a workflow](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)). The App would be:

- scoped to `contents: write`;
- installed on one repository;
- on the ruleset bypass list.

The App's pushes do trigger workflows, so the revision workflow must skip its own commits. Fork pull requests run with a read-only token and no secrets, so the writer should run on `push` to `main`, not on the pull-request event **[Doc]** ([Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)). While the library is private and unprotected, `GITHUB_TOKEN` is sufficient **[Inf]**. Classic bypass lists are organization-only, so a free organization account is preferable to a personal account **[Doc]**.

**An access-controlled pre-v1.0.0 site is not possible on GitHub Pages.** Pages from private repositories needs Pro or higher, and private (access-controlled) Pages needs Enterprise Cloud **[Doc]** ([What is GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages); [Pages visibility](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)). Netlify's free plan has no password protection **[Doc]** ([Netlify password protection](https://docs.netlify.com/manage/security/secure-access-to-sites/password-protection/)). Cloudflare Pages can restrict *preview* deployments to account members, but the free user limit is unverified **[Doc/unverified]** ([Cloudflare Pages previews](https://developers.cloudflare.com/pages/configuration/preview-deployments/)). The realistic free options for DR-23 / QA-26 are:

- a public site pushed to a separate public repository, which makes the content public;
- a Cloudflare Pages preview with an access policy;
- built HTML shared as a workflow artifact or release asset.

## Agents get the bundle by tag and release archive, not by package

**OKF is still v0.2. It has six commits and no tags, so pin the spec by commit SHA (currently `ad30107`)** **[Doc, git clone]** ([OKF SPEC.md](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)). One normative change post-dates the design: since 21 August 2026, "every timestamp-valued key in OKF is an ISO 8601 datetime with an explicit UTC offset". `stale_after` is now an absolute instant **[Doc]** ([SPEC.md history](https://github.com/GoogleCloudPlatform/open-knowledge-format/commits/main/SPEC.md)). okf-skills still tolerates date-only values, so the profile validator must enforce the rule itself **[Doc]** ([okf_validate.py](https://github.com/scaccogatto/okf-skills/blob/main/skills/validate/scripts/okf_validate.py)).

Pinning okf-skills needs care:

- **The floating `v1` tag moves on every release.** Pin the full commit SHA of `okf--v0.10.3` (`a8b96420…`, 13 October 2026) **[Doc]** ([okf-skills release.yml](https://github.com/scaccogatto/okf-skills/blob/main/.github/workflows/release.yml)).
- **Pass `bundle: knowledge` to the action.** Its default is `.okf` **[Doc]** ([action.yml](https://github.com/scaccogatto/okf-skills/blob/main/action.yml)).
- **Plan for a lapse.** 96 of its 100 commits come from one maintainer **[Doc, git clone]**.

**Delivery (QA-19):** the lowest-complexity channel is a semver tag plus a GitHub Release carrying a CI-built `knowledge-<tag>.tar.gz` and its SHA-256. Immutable releases should be enabled **[Inf]**. GitHub's auto-generated source archives can change compression over time, and GitHub recommends releases instead **[Doc]** ([Downloading source archives](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)). Immutable releases lock both the tag and the assets, and add an attestation **[Doc]** ([Immutable releases](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/immutable-releases)). Their availability on Free is unverified. A package registry would add a toolchain purely to transport Markdown. An MCP server would add the runtime dependency the design rules out, and okf-skills' own decision record calls MCP redundant for agents with file tools **[Doc]** ([okf-skills MCP decision](https://github.com/scaccogatto/okf-skills/blob/main/.okf/decisions/mcp-server.md)).

**Skill packaging (FR7):**

- **Use only the six spec fields** in `SKILL.md` frontmatter. Claude Code's own extensions cause "a hard error" in claude.ai and the Skills API **[Doc]** ([Claude Code skills](https://code.claude.com/docs/en/skills)).
- **Make the skills discoverable.** A root `skills/` folder is not auto-discovered by any runtime. `.agents/skills` is read by Codex, Copilot and Gemini CLI **[Doc]** ([GitHub Docs: agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills); [Gemini CLI skills](https://geminicli.com/docs/cli/skills/)).
- **Add plugin manifests later** for Claude Code and Codex: two to four small JSON files pointing at the existing folder **[Inf]**.

**Supply chain is the decisive argument against a Node-centred template.** Recent npm incidents:

- the chalk/debug compromise of September 2025 **[Doc]** ([Cycode](https://www.cycode.com/blog/npm-debug-chalk-supply-chain-attack/));
- the "Mini Shai-Hulud" wave of August 2026, which hit **2,225 component versions** and whose payload edits `.claude/settings.json`, directly relevant to an agent-authoring workstation **[Doc]** ([Sonatype](https://www.sonatype.com/blog/mini-shai-hulud-npm-attack-more-than-2200-components-impacted)).

npm 12 (July 2026) now blocks dependency install scripts by default **[Doc]** ([InfoQ](https://www.infoq.com/news/2026/08/npm-12-released/)). The risk is manageable but concentrated in the site layer: `@docusaurus/core` alone has 42 direct dependencies **[Doc]**.

PyPI is not immune, and the comparison should not be read as Python being safe. *Added 25 October 2026.* Two examples of legitimate packages being compromised:

- version 0.5.15 of `num2words` was published to PyPI on 28 July 2025 with no matching commits or release activity in its source repository, was flagged as potentially compromised within about two hours, and was removed by PyPI **[Doc]** ([StepSecurity](https://www.stepsecurity.io/blog/supply-chain-security-alert-num2words-pypi-package-shows-signs-of-compromise));
- in January 2026, legitimate dYdX packages on both npm and PyPI were compromised to push versions that stole wallet credentials and enabled remote code execution **[Doc, secondary]** ([The Hacker News, PyPI label](https://thehackernews.com/search/label/PyPI?hl=ja_JP)).

The difference between the ecosystems is one of scale and of where the exposure sits: the Python stack's validation dependency set is small and hash-locked, while a Node template's largest dependency trees sit in the site generator **[Inf]**. The same controls apply in either stack: pinned, hash-locked installs, a small validation set kept separate from site dependencies, and Dependabot or equivalent alerts.

The Python stack is not dependency-free either. Copier pulls a GPL-3 dependency (`jinja2-ansible-filters`) that a licence check would flag **[Test]**. The QA-24 baseline should keep the validation dependency set small and separate from site-build dependencies in any stack.

## Recommended reference stack

| Component | Recommendation | Basis |
| --- | --- | --- |
| Platform | GitHub on a **free organization** account; template public now; RE library private until v1.0.0 | QA-13, QA-14, QA-16 **[Doc]** |
| Scripting | Python ≥3.11 single-file PEP 723 scripts (`uv run`, `python3` fallback); markdown-it-py + mdit-py-plugins; ruamel.yaml (YAML 1.2) or string-cast loading; hash-locked requirements | Ecosystem fit, tested parsing **[Test]** |
| Schema | JSON Schema draft 2020-12 per type, validated by jsonschema; check-jsonschema for `profile.yaml`, `uid-registry.yaml`, issue forms and workflows | Language-neutral profile **[Test/Doc]** |
| Conformance (check 1) | okf-skills pinned by full SHA, `bundle: knowledge`; own frontmatter-first and datetime-offset checks | QA-25 **[Doc]** |
| Second link check | Optional lychee `--offline --root-dir knowledge --include-fragments` | **[Test]** |
| Instantiation | GitHub template repository + idempotent `init_library` script + `gh`-based setup of labels, ruleset and App; Copier only if the questionnaire grows | QA-21 **[Doc/Inf]** |
| Site | One shared `mkdocs.yml`, built in parallel: MkDocs 1.6.1 + Material 9.7.x pinned (`mkdocs<2`, blocking `--strict` build) and Zensical pinned to an exact 0.0.x version (non-blocking build plus lychee and page-list checks on its output). Switch to Zensical when it passes all six checks; final choice at the v1.0.0 site decision, with Docusaurus in `detect` mode as the fallback | Only test-passing generator; vendor-documented parallel migration path; lifecycle risk **[Test/Doc]** |
| Glossary anchors | Inline `<a id="<github-slug>"></a>` on each term heading; `{#id}` banned | DR-10 **[Doc/Test]** |
| Revision bot | `GITHUB_TOKEN` while private and unprotected; GitHub App (`contents: write`, ruleset bypass) from v1.0.0 and on the template; writer runs on `push` to `main`; loop guard | QA-17 **[Doc]** |
| Delivery | Semver tag + immutable GitHub Release with bundle archive and SHA-256; clone at tag as alternative | QA-19 **[Doc/Inf]** |
| Security (QA-24) | SHA-pinned actions with the pinning policy where available; default read-only token; no `pull_request_target`; Dependabot for actions and pip; native secret scanning and CodeQL on public repositories; CI secret scanner on the private library; dependency-licence check | **[Doc]** ([secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use); [SHA-pinning policy](https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/)) |

The strongest case against this recommendation is a **Node stack built around Docusaurus**. It would use one AST family for the validator and the site and fit a catalogue-style landing page, and it would remove the Material lifecycle risk. Adopt it if a test build shows Docusaurus CommonMark mode passing all six checks and the owner accepts the npm controls. The **Hugo hybrid** (Hugo + lychee + Python scripts) is a sound fallback generator if both MkDocs and Docusaurus disappoint. Its pre-build step has been verified.

## Open items to verify by test build

| # | Item | Why it matters |
| --- | --- | --- |
| 1 | GitHub rendering of `<a id>` inside or above a heading, of `{#id}`, and of non-ASCII or parenthesised terms (e.g. "Café", "(PID)") in a scratch repository | DR-10; the GitHub Markdown API was blocked in every session |
| 2 | Two-space nested *Checks* sub-bullets in Python-Markdown (Material/Zensical); fix with a sane-lists extension or change the format | Check 6; Risk template §6 |
| 3 | Zensical support for `/`-rooted links (failed in test): whether `validation.links.absolute_links` is honoured or silently ignored, and what Zensical setting replaces it; also `extra.status`, footnotes, `attr_list`/`toc`, strict mode, and whether MkDocs tolerates `theme.variant` in a shared `mkdocs.yml` | Parallel build and the switch to Zensical |
| 4 | Docusaurus 3.10 in `detect` mode on three real concepts: raw `<a id>` kept, unknown keys tolerated, HTML comment, `tags.yml` generated from vocab | Fallback generator |
| 5 | Ruleset with a GitHub App bypass on the chosen account type; status-check naming across `pull_request` and `pull_request_review` runs; how a bypass merge appears in the API | QA-17, QA-23 |
| 6 | End-to-end FR6 timing by a second person, including labels, ruleset and App set-up (template repositories do not document copying labels or rules) | FR6 pilot gate |
| 7 | Immutable releases on GitHub Free; Cloudflare Pages access policy user limit on the free plan | QA-19, DR-23 |
| 8 | Live GitHub Pro and post-promotion Team prices (USD 4 is from a 2020 FAQ) | QA-13 record only |

## Changes the findings imply for the design documents and decision records

| Document / ID | Change |
| --- | --- |
| Template DDR **QA-29**, QA-15; Template SRS Provenance (Approval); Risk template spec §7 | Resolve: no GitHub author can approve their own pull request; single-maintainer self-approval is an admin merge without an approving review, recorded `self-approved`. Delete "approval of" from "approval of, or merge of"; remove "to be confirmed" from QA-15 |
| QA-23; Template SRS Validation pipeline (publishing rules) | Publishing-rule check derives approval at merge and after merge from the review list and `merged_by`; the review-submitted rerun applies only to reviewers other than the author. Do not enable "require approval of most recent push" or "do not allow bypassing" while one maintainer |
| **QA-16**; Template SRS Constraints (Reference stack); RE library SRS constraints | Mark confirmed for protected branches, rulesets and code owners. Add: validator also runs on push to `main` while private; CI secret and pattern scanner on the private library, because native scanning is unavailable |
| **QA-17**; Template SRS Provenance; Risk template spec §12 open point | Bot identity: repository-scoped GitHub App on the ruleset bypass list; `GITHUB_TOKEN` acceptable while private and unprotected; writer triggered by push to `main`; loop guard. Prefer a free organization account |
| **DR-10**; Template SRS Glossary and website check 4; RE library SRS Glossary | Name the method: inline `<a id="…"></a>` with id equal to GitHub's auto-slug; `{#id}` prohibited; validator checks anchors; decide whether duplicate ids (explicit plus auto) are acceptable |
| **OKF datetime rule**; Risk template spec §4; Template SRS profile example; DR-01 | `stale_after` type changes from date to datetime with offset (e.g. `2027-01-01T00:00:00Z`); `verified: [{…, at: <date>}]` changes to a datetime; validator enforces it because okf-skills tolerates dates; revision-history body lines keep `YYYY-MM-DD`. Record the spec pin as commit `ad30107` |
| **QA-26 / RE DR-23** (alpha/beta site); Template SRS Publishing website | State that GitHub Pages cannot host an access-controlled site on Free; list the options: public site repository, Cloudflare Pages preview with access policy (to verify), or artifacts |
| QA-24 | Adopt the security baseline in the recommended-stack table |
| QA-25 | Pin okf-skills by full commit SHA, not `@v1`; pass `bundle: knowledge` |
| QA-19 | Delivery: tag plus immutable release archive with SHA-256; skills use spec-only frontmatter, exposed through `.agents/skills` or plugin manifests later |
| QA-21; Template SRS Instantiation, trade-offs and layout | Template repository plus init and setup scripts; Copier optional; repository name `okf-library-template` (not `cookiecutter-okf`) |
| DR-19; Template SRS Publishing website table | Update the example comparison: Material is in maintenance mode, Zensical is alpha, Docusaurus requires `detect` mode, Hugo needs the `index.md` workaround. Add the parallel route: one shared `mkdocs.yml` built by MkDocs (blocking) and Zensical (non-blocking, with output checks), switching when Zensical passes the six checks |
| Risk template spec §8 authoring rules | Add a lint rule: angle-bracket text in prose must be in code spans or escaped. Issue-form labels (`agent-drafted`, `approved-move`) are created by the setup script, because forms apply only labels that already exist ([issue forms syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)); issue forms remain public preview |

## Conclusion

The stack question turned out to be narrower than the design assumed. Platform behaviour, not language, drives the hardest decisions: self-approval, bot permissions, private-site hosting and anchors. Those findings apply whichever language is chosen. The scripting language follows ecosystem gravity towards Python, because the bespoke profile layer costs the same everywhere and Python is the only language that keeps okf-skills, the profile scripts and the skill scripts on one runtime. The only genuinely open technical choice is the site generator, and the design's "no public site before v1.0.0" rule turns that into an asset. The template can ship with a tested, pinned generator for previews, build the same configuration with Zensical in parallel, and switch once Zensical's output passes the six checks, without moving any content or rewriting configuration.

Two findings change the design's intent, not just its wording. First, without an approval event, self-approval becomes something CI must infer at merge. The provenance record is therefore only as trustworthy as that inference, which should be tested before the pilot. Second, OKF's move to offset datetimes shows that a pre-1.0 spec can change silently beneath a pinned checker. The profile validator, not okf-skills, must be the authority on what this library accepts.
