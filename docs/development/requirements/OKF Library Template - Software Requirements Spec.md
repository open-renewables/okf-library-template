---
name: OKF Library Template - Software Requirements Spec
description: "This document sets out the requirements of the reusable OKF library template: a thin profile layer on the Open Knowledge Format for building validated, agent-ready knowledge libraries in any domain."
author: Richard Gledhill
type: reference
created: 2026-10-17T09:06
modified: 2026-10-25
draft: false
confidential: false
tags:
aliases:
  - OKF Library Template - Software Requirements Specification
  - OKF Library Template - Design and Requirements
  - OKF Profile Template - Requirements and design
---
> This document sets out the requirements of the reusable OKF library template: a thin profile layer on the Open Knowledge Format (OKF) v0.2 that lets any domain build a validated knowledge library which an agent can traverse selectively and a person can browse. The profile declares each concept type's frontmatter and body sections, controlled vocabularies travel with the knowledge bundle, provenance is recorded by CI from merged pull requests, and every concept carries a permanent identifier. Requirements are technology-neutral; how they are met on the reference stack is set out in `OKF Library Template - Software Design Document.md`, and the decisions behind both are in `OKF Library Template - Design Decision Record.md`. Libraries built from the template are downstream of this document and are not described here.

---
# OKF Library Template: Software Requirements Spec

**Location.** In the template repository this document is `docs/development/requirements/OKF Library Template - Software Requirements Spec.md` (DDR QA-67).

**Abbreviations.** SRS: this Software Requirements Spec. SDD: `OKF Library Template - Software Design Document.md`. DDR: `OKF Library Template - Design Decision Record.md`. OKF: Open Knowledge Format. CI: continuous integration.

## Executive summary

The template should adopt the existing Open Knowledge Format (OKF) v0.2 and publish a thin domain-profile template on top of it, not build a new format from scratch. OKF was released by Google Cloud on 12 June 2026 under Apache 2.0, and at least five community templates and a conformance checker already exist.

The gap is not the format. It is the absence of a convention for declaring a domain's concept types, required fields, body structure and vocabularies, and of shared tooling to validate them. This document states what that convention and tooling must do. Domain content and domain-specific agent workflows belong to each library built from the template.

Proposed plan:

1. **OKF library template.** A template repository containing an OKF bundle skeleton, a machine-readable profile (a schema per concept type for frontmatter, plus a declared body structure), controlled vocabularies inside the bundle, generated `index.md` files, CI validation, a CI-written revision history on each concept, issue forms for contributors who do not use git, and agent skills for authoring and consuming the bundle. The template is built and released as stable v1.0.0 before any library is built from it.
2. **Pilot library.** A throwaway library instantiated from the template, used to test the template before v1.0.0.

The main template risks are spec churn (OKF is v0.x), quality drift if agent-generated content is not human-verified, and libraries whose repositories cannot enforce branch protection. Each has a proportionate control, set out in the risks section.

### What the template owns and what each library owns

| The template defines | Each library declares in its profile and content |
| --- | --- |
| The profile mechanism (`profile.yaml`, frontmatter schemas, body declarations, section formats) | Its concept types, fields, body sections and section formats |
| The vocabulary mechanism (`knowledge/vocab/`) | Its vocabularies and their values |
| The validation pipeline and warning levels | Its rules and warnings |
| The `uid` mechanism and registry | Its `uid` prefixes |
| The provenance options, approval rule and trust-tier derivation | Which provenance option it uses and any extra `status` values |
| Revision history, index generation, decision record and release process | Its folder depth, glossary terms and decisions |
| A technology-agnostic set of requirements | Its technology stack (hosting, CI, scripting language, website generator) |
| The starting scripts and workflows, under Apache 2.0 | Any customisation of them: a library may diverge from the template after instantiation |
| — | Its licences for content and code, which need not be open source, and whether it publishes a site or accepts outside contributions |

## Assumptions review

Owner reviews settled the assumptions below. Assumptions specific to a library are recorded by that library.

| # | Assumption | Original proposal | Outcome of review | Status |
| --- | --- | --- | --- | --- |
| T1 | Licences | CC BY 4.0 content, Apache 2.0 code | The template repository, including its example content and design documents, is Apache 2.0. Each library's owner chooses the licences for its content and code, which need not be open source; CC BY 4.0 is offered as the default content licence. Files inherited from the template keep their Apache 2.0 terms when distributed | Revised |
| T2 | Team | 1–3 maintainers plus part-time discipline owners | Single maintainer initially, expanding to a small team over time. While there is one maintainer, the maintainer's recorded self-approval meets the approval rule | Revised |
| T3 | Re-review interval | `stale_after` two years | Two years, measured from the last revision-history entry, with an optional `stale_after` field that can only bring review forward | Revised |
| T4 | Timeline | Template in weeks 1–6, library MVP by week 18 | No fixed dates; stages and their gates retained | Revised |
| T5 | Website | Not in original design | A library may publish a static website built from the bundle. Where it does, the site shows the latest release only, offers "Suggest an edit" on each concept page and a site-wide link to raise an issue; pre-filled per-page issue links are deferred until after template v1.0.0. No public site until a library's v1.0.0; a library may publish an alpha or beta site before then, or have no public site at all | Revised |
| T6 | Budget | Not stated | Free tiers of the hosting and CI platform only | Confirmed |

## Background and problem statement

Agents apply curated knowledge reliably only when it is structured, validated and carries provenance. Each domain that wants this currently has to invent its own conventions on top of OKF: which concept types exist, which fields and body sections they need, how they are validated, and how agents should navigate and cite them.

**Problem statement.** Industry stakeholders need a repeatable way to stand up version-controlled knowledge libraries, built on an open format, that an agent can traverse selectively and a person can browse in a repository, with provenance and review status on every entry.

## Evidence: what already exists

The format and generic templates exist; a domain-profile convention does not. Repositories below were cloned and inspected on 16 October 2026.

### The OKF specification

[OKF v0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format) represents knowledge as a directory of markdown files with YAML frontmatter. Its canonical repository moved from `knowledge-catalog/okf`, which is now a frozen snapshot. The specification has no release tags, so it is pinned by commit (`ad30107`). Key properties relevant to this project:

- **Atomic unit.** One concept per file; the concept ID is the file path without `.md`.
- **Minimal conformance.** Every non-reserved `.md` file needs parseable frontmatter, opening on the first line of the file, with a non-empty `type` (§4, §11). Consumers must tolerate unknown types, extra keys, broken links and missing indexes. `index.md` and `log.md` are reserved names (§3.1).
- **Timestamps.** Since 21 August 2026, every timestamp-valued frontmatter key is an ISO 8601 datetime with an explicit UTC offset, so `stale_after` is an absolute instant.
- **Navigation.** Optional `index.md` per directory for progressive disclosure, `log.md` for change history, and plain markdown links between concepts. Links are untyped.
- **Trust.** Optional `sources` (with per-claim footnotes), `generated`, `verified`, `status` (draft, stable, deprecated) and `stale_after`. A trust tier (unverified, machine-confirmed, human-reviewed) is derived from `verified`, keyed on the `human:` actor prefix.
- **No taxonomy.** Defining concept types is an explicit non-goal, so each domain must define its own.
- **Governance.** Apache 2.0; spec changes require an issue before a pull request, plus a Google CLA.

### Templates and tooling

| Repository | What it provides | Licence | Last commit | Fit |
| --- | --- | --- | --- | --- |
| [scaccogatto/okf-skills](https://github.com/scaccogatto/okf-skills) | Agent skills, Claude Code plugin, MCP server, graph viewer and a GitHub Action that checks v0.2 conformance | MIT | 2026-10-13 | Reuse the validator and viewer |
| [open-science-pillars/knowledge-template](https://github.com/open-science-pillars/knowledge-template) | Conformant bundle with one annotated example per concept type, CITATION.cff, CODEOWNERS, governance YAML | Apache 2.0 | 2026-09-20 | Closest pattern; tied to its own gate tooling |
| [Movida/okf-bundle-template](https://github.com/Movida/okf-bundle-template) | Manifest, GOVERNANCE.md, frontmatter `schema.yaml` (documentation only, not enforced), agent-run instantiation questionnaire | Apache 2.0 | 2026-10-13 | Good governance pattern; French-language |
| [allenday/agent-skills-template](https://github.com/allenday/agent-skills-template) | GitHub template for a collection of portable Agent Skills packaged as one Codex plugin: `skills/<name>/` folders that must be self-contained, `scripts/new-skill` scaffolder, dependency-free `scripts/validate` with stable error codes, positive and negative trigger evals per skill, THIRD\_PARTY\_NOTICES format, CI workflow and unit tests | Apache 2.0 | 2026-08-28 | Reference pattern for skill scaffolding and trigger evals; not OKF-aware, and plugin packaging is Codex-specific |
| [ayhansipahi/OKF-starter-bundle](https://github.com/ayhansipahi/OKF-starter-bundle) | Small example bundle (systems, decisions, playbooks) | Not stated | 2026-09-29 | Illustrative only |
| [supachai-j/open-knowledge-format-starter](https://github.com/supachai-j/open-knowledge-format-starter) | Book-style site, Docker deploy, CI examples | MIT | 2026-06-16 | Publishing ideas; heavier than needed |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills), [mattpocock/skills](https://github.com/mattpocock/skills) | Mature Agent Skills collections (about 30 and 100+ skills) with plugin packaging for several agents, evals (addyosmani) and ADRs, scope and changelog practice (mattpocock) | MIT | 2026-10-13, 2026-10-09 | Examples of how a skills repository grows and is governed; not derived from the template above |

**Lineage check (17 October 2026).** The assumption that addyosmani/agent-skills and mattpocock/skills were built from allenday/agent-skills-template is not supported. Both were started six months before it (3 and 15 February 2026, against 25 August 2026), and none of the three references the others. They share conventions instead: the Agent Skills `SKILL.md` format, and the Codex plugin files `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`, which addyosmani/agent-skills added on 8 July 2026. The template is best read as a later, minimal distillation of those conventions, not their source.

Adjacent standard: [Agent Skills](https://agentskills.io/) (`SKILL.md` folders with name and description frontmatter) is the open format most agent products use to load procedures on demand. It is the natural packaging for authoring and consuming workflows, which OKF deliberately leaves out of scope.

### Gap

No template enforces a domain profile: Movida documents its schema without validating it, and open-science-pillars validates against its own organisation's rules. None declares or validates the body structure of a concept, which is where agents find the content they act on.

## Requirements

The binding requirement is that the same files serve an agent working within a limited context window and a person browsing the repository, with no server or SDK.

Requirements are grouped FR1 to FR8 and numbered within each group. Each has an acceptance criterion; the SDD traces each group to its components, workflows and verification (SDD §13). "Change proposal" means a pull request or the platform's equivalent. "Directory owner" means a person named for a folder in the platform's code-owners file.

### Functional

#### FR1 Knowledge bundle and identifiers

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR1.1 | Each concept is one Markdown file with YAML frontmatter in the bundle root folder; its concept ID is its path without `.md` | The pinned OKF conformance checker reports no error on the template's example bundle |
| FR1.2 | The bundle conforms to OKF v0.2 at the pinned specification commit, including frontmatter on the first line and timestamp-valued frontmatter keys as ISO 8601 datetimes with an explicit offset | A fixture for each rule fails validation with its own finding code |
| FR1.3 | Every concept carries a permanent `uid` in its frontmatter, formed from a type prefix declared in the profile and a four-digit sequence. Prefixes and numbers are never reused, even after a concept is deprecated or a type is retired. Each prefix is capped at 9,999 numbers; widening the sequence is a breaking profile change | Fixtures with a missing, malformed, duplicated or changed `uid` fail |
| FR1.4 | A registry maps each `uid` to its concept type, current path and earlier paths. It is maintained by tooling, never by hand, and does not duplicate other frontmatter such as `status` | A hand edit that puts the registry out of step with the files fails |
| FR1.5 | Validation fails when a `uid` is missing, duplicated, changed or no longer present, and when a concept's path differs from the registry, unless the change proposal carries an approved-move label and the registry records the old path | One fixture per case fails with its own code |
| FR1.6 | Two open change proposals that take the same `uid` are detected at the latest by validation of the main branch after the second merges, and a tool renumbers the later concept | Merging two proposals with the same number produces a reported failure on the main branch, which the renumber tool clears |
| FR1.7 | Concepts are never deleted; a concept leaves use by `status: deprecated` | Deleting a concept file fails validation |

#### FR2 Profile and validation

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR2.1 | A machine-readable profile declares the concept types, `uid` prefixes, frontmatter schemas, body sections (heading, order, required flag, empty placeholder, format, CI-managed), vocabularies, path rules, status values, publishing rules and warnings. The tooling contains no domain rule | A new concept type added by profile changes only passes validation; review finds no domain rule in the tooling |
| FR2.2 | Validation runs six checks: (1) OKF conformance with a pinned external checker, plus the frontmatter-first and datetime-offset rules in the profile validator; (2) frontmatter against the type's schema; (3) body sections, order, placeholders, formats and CI-managed sections; (4) internal links, heading anchors, vocabulary membership and path rules; (5) index freshness; (6) identifier and registry integrity | Each check has at least one failing fixture |
| FR2.3 | Each finding has a stable code, a level (error or warning), a file and a line. Errors block merge where the platform can enforce it | Output in a machine-readable form lists code, level, file and line |
| FR2.4 | Validation runs on every change proposal, again when a review is submitted, and on the main branch after every merge, where failures are reported as an issue | A failing commit on the main branch opens or updates one tracking issue |
| FR2.5 | Concept changes are validated with the tooling and profile from the base branch, not from the change proposal | A change proposal that relaxes the profile and adds a non-conforming concept fails |
| FR2.6 | A change proposal that changes both tooling or profile files and concept content fails, unless it carries a profile-migration label. A profile-migration change proposal is validated with its own tooling, needs a maintainer's approval and a decision-record entry, and is released as a major version | A mixed change proposal without the label fails; with the label and without an approval it fails the publishing check |
| FR2.7 | A profile may reject unknown frontmatter fields for its own contributions; OKF's standard optional fields are always accepted | A concept carrying OKF `verified` passes when unknown fields are rejected |
| FR2.8 | Authors can run the same six checks locally as CI runs | A local run and a CI run on the same commit produce the same findings |
| FR2.9 | Each tag namespace or other controlled list is one vocabulary concept inside the bundle. Each value has a one-line definition; where values are grouped by kind, they are unique across kinds. The vocabulary concept is the authoritative list, and values are added by an approved change proposal | A tag value missing from its vocabulary fails check 4 |
| FR2.10 | A library may hold common terms in one root glossary concept, one heading per term, with an aliases line and a source line. Each term has an explicit anchor equal to the platform's automatic slug of the term when it is created; the anchor never changes, and a term is renamed only by adding the old name as an alias | A link to a glossary anchor resolves on the hosting platform and on the site; a changed anchor fails |
| FR2.11 | Every check, test, scan and site build that CI runs can be run locally with the same command, on Windows, macOS and Linux | Each CI job invokes only commands documented for local use; a local run and a CI run on the same commit give the same findings |

#### FR3 Provenance and trust

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR3.1 | By default, after each merge an automated commit appends one revision-history line to each concept the change proposal touched, recording merge date, author, approval outcome, approver and owner status, change-proposal number, and any agent-drafted or full-review label | Golden files cover each approval case |
| FR3.2 | Each run of the revision writer records every change proposal merged since the last recorded one, so a dropped or failed run is recovered by the next | With one run suppressed between two merges, the next run records both |
| FR3.3 | The revision commit regenerates the indexes it affects, so the main branch never fails the index freshness check because of a revision write | Check 5 passes on the main branch after each revision commit |
| FR3.4 | Revision lines are inserted at the end of the *Revision history* section. The section is CI-managed and manual edits to it fail validation | A hand edit to the section fails check 3; footnote definitions after the section are left in place |
| FR3.5 | A `stable` concept needs one approval by a human directory owner of that concept. Approval is determined at and after merge from the reviews and the identity of the merger, because a platform may not let authors approve their own change proposals. While a library has one maintainer, the maintainer's merge of their own change proposal is recorded as self-approved and counts as the approval, unless the library requires a non-author approver | Each approval case is recorded correctly in a scratch library |
| FR3.6 | An approval given on a commit other than the merged head is recorded as stale | A change proposal approved and then changed before merge records a stale approval |
| FR3.7 | Each revision has a tier: Machine-confirmed if agent-drafted, approved by a non-owner, approved on a stale commit or merged without approval; otherwise Human-reviewed. A concept's trust tier is the lowest tier of its revisions since the latest revision labelled full-review that a directory owner approved, or of all its revisions if there is none; Unverified if it has no revision. Where self-approval contributes to a Human-reviewed tier, the tier is shown as `human-reviewed (self)` | Golden files cover each case, including a one-line owner-approved fix to an agent-drafted concept, which stays Machine-confirmed |
| FR3.8 | A profile may also have CI write the OKF `verified` field, mapped so that a generic OKF tool derives the same tier as the library | For each tier case, an OKF tool's derived tier equals the library's |
| FR3.9 | `status` takes OKF's `draft`, `stable` and `deprecated`, plus any extension the profile declares with its tier and publishing rules; undeclared values are rejected | A concept with an undeclared status fails |
| FR3.10 | A `stable` concept cites at least one source in its body, as a footnote or an external link | A stable concept without a citation fails |
| FR3.11 | A concept is stale at the earlier of its `stale_after` instant and the profile's default interval after its last revision. A scheduled job reports stale concepts | A fixture past each limit appears in the report |

#### FR4 Indexes

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR4.1 | Every folder in the bundle has a generated `index.md` with one line per subfolder and per concept, so agents can navigate one level at a time | Golden index files match the generator's output |
| FR4.2 | Each concept line shows the concept's status and trust tier, including the self-approval qualifier | Golden files show each tier |
| FR4.3 | Index files are never edited by hand; validation checks that committed indexes match the generator's output | A stale or hand-edited index fails check 5 |

#### FR5 Contribution workflow

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR5.1 | Content changes arrive as change proposals using a template that prompts for the agent-drafted, full-review, approved-move and profile-migration labels | The template lists each label |
| FR5.2 | Validation warns when agent markers are found and the agent-drafted label is missing | A fixture with an agent commit trailer and no label raises the warning |
| FR5.3 | The template provides issue forms for new concepts, corrections and feedback, so people who do not use git can contribute; a maintainer or an agent turns accepted issues into change proposals. A library may switch the forms off | A pilot contribution goes from issue form to merged concept |
| FR5.4 | Directory owners are declared per folder; ownership is assessed per concept file | A change proposal touching two folders records each concept's owner status separately |
| FR5.5 | Each library keeps a decision record for changes to its profile or structure | The instantiated library contains the decision record with an instantiation entry |

#### FR6 Instantiation

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR6.1 | A person new to the template can create a library and merge a first validated concept in under 30 minutes | Timed by a second person in the pilot |
| FR6.2 | Instantiation asks for the library's licences: content (default CC BY 4.0) and the owner's own code and changes, with proprietary licences allowed. The template's Apache 2.0 licence text and notices are kept for the inherited files | An instantiated library contains the chosen licence files, the Apache 2.0 text and the notice file |
| FR6.3 | Template-only files, including the template's development documentation, are removed at instantiation, and instantiation is tested automatically on every change to the template, with and without a hosting platform | The self-test fails if a placeholder or template-only file remains |
| FR6.4 | A library may diverge from the template after instantiation; no update path from the template is required | — (constraint on design, not tested) |
| FR6.5 | A library can be operated with git and Python only, without a hosting platform: validation, indexes, revision history and trust tiers, the staleness report, releases and a local site all work locally. Platform features (issue forms, labels, protected branches, hosted CI, hosted site, hosted releases) are optional | The instantiation self-test creates a library with no hosting platform, records revision lines from local commits and makes a release, without calling any platform API |
| FR6.6 | A library operated without a hosting platform can move to one later without rewriting its history, revision lines or releases | In a rehearsal, commit identifiers and revision lines are unchanged after the move, and each earlier release archive rebuilt from its tag matches its recorded checksum |

#### FR7 Agent skills and delivery

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR7.1 | Two skills in the Agent Skills format, using only the specification's frontmatter fields: one for authoring a concept to the profile, one for consuming the bundle. Both read the profile's declarations and the bundle's vocabularies rather than hard-coding structure | Both skills work on the pilot library without edits |
| FR7.2 | The consuming skill navigates indexes one level at a time, reads declared sections by heading, and reports for each concept used its `uid`, status, trust tier and the release tag; it never treats unverified content as reviewed | A reviewer traces the pilot agent's outputs to `uid`s and a release tag |
| FR7.3 | Each release is a semantic-version tag with an immutable archive, its checksum and a manifest. The archive contains the bundle, the profile, the agent entry point, the licence and notice files and the consuming skill | The archive is readable without tooling and its checksum verifies |
| FR7.4 | A release fails if any change proposal merged since the previous release lacks its revision line | A release attempted with a missing line fails |

#### FR8 Website

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| FR8.1 | A library may publish a static site built from the bundle without changing any source file; the generator can be replaced without moving concept files | The site build reads the bundle in place |
| FR8.2 | The generator passes six compatibility checks: (1) `index.md` becomes the folder's landing page; (2) links starting with `/` resolve to site routes; (3) non-standard frontmatter keys are ignored but kept; (4) heading anchors match the hosting platform's, using explicit anchors where needed; (5) keys the generator reserves (for example `id`, `title`, `description`, `tags`, `slug`, `status`) do not change the profile's meaning, and colon-namespaced tags produce valid pages and URLs; (6) angle brackets and braces in prose, and footnotes, render unchanged | A test build on the pilot bundle passes each check |
| FR8.3 | The site is rebuilt from each release tag and shows the latest release only; earlier releases are cited by tag and archive | The deployed site's manifest matches the latest tag |
| FR8.4 | Each concept page offers "Suggest an edit", opening the file in the platform's editor; the site carries a link to raise an issue through the issue forms. Pre-filled per-page issue links are deferred until after template v1.0.0 | Both links work on a preview build |
| FR8.5 | No public site is published before a library's v1.0.0; previews are local or build artifacts. A library may publish an alpha or beta site before then at the owner's discretion, within the free-tier budget, or have no public site | — (governance rule) |

### Non-functional

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| NFR1 Portability | The bundle is readable with `cat`, renders on common repository hosting platforms, and needs no runtime dependency for agents | A release archive is usable with file tools only |
| NFR2 Technology neutrality | The requirements rely only on capabilities common to mainstream platforms and tools; named products are examples, and each library records its chosen stack in its decision record. A library does not need a hosting platform at all (FR6.5) | Review of this document finds no requirement met by only one product |
| NFR3 Cost | The reference stack runs on free tiers of the hosting and CI platform | The pilot runs on a free organisation account |
| NFR4 Licensing | The template is Apache 2.0 throughout. Each library's content and code licences are the owner's choice, recorded at instantiation; inherited files keep Apache 2.0 terms and notices | Licence files and the notice file are present; a dependency licence check passes against an allowlist compatible with Apache 2.0 |
| NFR5 Content style | Plain English, SI units, standards cited by number and edition. Site accessibility conformance (for example WCAG) is not required, because the template serves AI agents first; the site generator's defaults are accepted | — (authoring rule, enforced by review) |
| NFR6 Security | CI runs with least-privilege, per-job permissions; third-party CI components are pinned to immutable versions; no secret is exposed to change proposals from untrusted sources; every change and every push to the main branch is scanned for secrets, natively where the platform offers it and by a CI scanner otherwise, and locally before commit where the scanner is installed; locked dependencies are checked for known vulnerabilities whenever the lock file changes and at least weekly; validation dependencies are kept separate from site dependencies and installed from a hash-locked set | Review of the workflow configuration; a planted test secret is detected |
| NFR7 Recovery | The repository is the system of record. A missed revision line is recovered by the next revision run (FR3.2); repository settings, labels and rules can be recreated by a rerunnable set-up script; tooling installs reproducibly from a lock file; release archives are immutable and checksummed | Rerunning the set-up script on a scratch repository restores its settings; a clean install from the lock file passes the test suite |

### Constraints and assumptions

- Single maintainer initially, expanding to a small team; directory owners recruited as content grows. Automation (CI, generated indexes, revision history, authoring skill) must keep the review load manageable for one person.
- The library is held in a git repository. A hosting platform that provides change proposals with approvals and labels, issue forms, code owners, protected branches, CI and scheduled jobs (for example GitHub with GitHub Actions) is optional: without one, the same checks and records are produced locally (FR6.5), and the library can move to a platform later (FR6.6). Support for platforms other than GitHub is planned after template v1.0.0.
- **Reference stack.** The template and its first library use GitHub with GitHub Actions on a free organisation account. Platform behaviour confirmed in the stack analysis (DDR DR-23):
  - No pull request author can approve their own pull request, whatever their role; repository administrators can merge without an approving review.
  - On GitHub Free, protected branches, rulesets and code-owner enforcement apply to public repositories only.
  - Native secret scanning is free on public repositories only.
  - GitHub Pages cannot host an access-controlled site on free plans.
- The template repository is public from the start. A library may be private until v1.0.0, or permanently, for example when its content is proprietary. A private library on free tiers relies on CI checks only: it re-validates on every push to the main branch and runs a CI secret scanner.
- OKF is pre-1.0 and may change; the profile must be able to track minor versions, and the profile validator, not the external checker, is the authority on what a library accepts.

## Design overview

The template is an OKF v0.2 bundle plus a profile layer that OKF leaves undefined: declared concept types, enforced frontmatter fields and body sections, controlled vocabularies, provenance, generated indexes and agent skills. A new library is created from the template repository with set-up scripts, by answering a short questionnaire and adding content. The design, including the repository layout, the profile file format, the revision-line grammar, the trust-tier derivation and the workflows, is in the SDD:

| Topic | SDD section |
| --- | --- |
| Architecture decisions and reference stack | §4 |
| Repository layout | §6 |
| Profile declaration, schemas, formats, vocabularies, registry, indexes, revision lines, findings | §8 (I-01 to I-15) |
| Validation, revision writing, release, site, instantiation and promotion workflows | §9 (W-01 to W-11) |
| Security, permissions and repository configuration | §10, §11 |
| Requirements traceability | §13 |

`log.md` is not used: per-concept revision history records who changed what and when, the decision record records why the profile or structure changed, and release notes are published with each release.

## Trade-offs and key decisions

Each decision favours plain files and existing tools over custom infrastructure, accepting some loss of query power in exchange for portability and a low maintenance load. Decisions specific to a library are recorded in that library's decision record. The decisions behind this table are in the DDR.

| Decision | Chosen | Alternatives considered | Why | Cost of the choice |
| --- | --- | --- | --- | --- |
| Knowledge format | OKF v0.2 | Custom YAML or JSON database; Obsidian vault conventions; graph database | Published, vendor-neutral, git-native and readable without tools; existing validator and viewer | Pre-1.0 spec may change; no query language |
| Build vs adopt template | New thin profile template that reuses an existing OKF conformance checker | Fork open-science-pillars or Movida | Neither enforces an arbitrary domain profile; forking inherits unrelated tooling or French-language docs | Profile tooling to build and maintain (estimate in the SDD build plan) |
| Instantiation | A copy of the template (the platform's template-repository option, a clone or a release archive) plus set-up scripts, tested on every template change | Engine with an update path (e.g. Copier); generate-only engine (e.g. cookiecutter); tooling as a shared versioned package | Libraries may diverge, so an update path is not required; the template stays a working library that tests itself; no hosting platform is needed to start | Fixes to the template's scripts reach existing libraries only by manual porting, or by merging template tags into a library created by clone |
| Hosting platform | Optional; GitHub supported, plus a git-only mode | Platform required; several platforms supported from v1.0.0 | Lets a library start, and stay, on one machine; adds no dependency on a provider | Without a platform, approvals are declared by the committer and not independently recorded, so a single user's work is shown as self-approved |
| Relationship typing | Declared body sections: the heading under which content or a link appears gives its meaning | Typed frontmatter fields mirrored as body links; prose-only links (OKF default); separate graph file | One place to maintain each item; humans and generic viewers read the same text; agents extract sections from the profile declaration | Heading names become an interface and change only through a profile change; agents and CI must parse by heading |
| Provenance | CI-written revision history in the body, written by a bot commit after merge with catch-up processing, with optional CI-written OKF `verified` | Author-maintained `generated` and `verified` frontmatter; revision line written to the change-proposal branch before merge | Authors maintain nothing; works with fork change proposals and without an approval event; dropped runs are recovered | Generic OKF tools under-rate trust unless `verified` writing is enabled; a bot must be allowed to write to the main branch |
| Approval and tier | One approval by a directory owner; a single maintainer's recorded self-approval counts but is shown as such; the tier is the lowest since the last full review | Two-level review; independent second reviewer before any concept is stable; tier from the latest revision only | Lets a single maintainer publish while keeping an honest record of the review behind each concept | Self-approved content has no independent review; a full review is needed to raise an agent-drafted concept's tier |
| Validation authority | Content is validated with the base branch's tooling and profile; tooling and content change separately except for profile migrations | Change proposal validates itself | A change proposal cannot weaken the checks that judge it, even where branch protection is unavailable | Profile changes and the content that depends on them need two change proposals, or a migration label |
| Contribution route | Issue forms, turned into change proposals by a maintainer or an agent | CI that corrects web-editor change proposals | Contributors without git need no knowledge of `uid`s, tags or the registry; CI never writes to contributors' branches | Each contribution needs maintainer or agent effort to convert |
| Vocabulary location | Inside the bundle (`knowledge/vocab/`), as OKF concepts; section formats stay in the profile | All in `profile/`; vocabularies merged into the glossary | Vocabularies are domain language agents need and travel with the bundle; formats are tooling | Each vocabulary needs frontmatter, a `uid` and an index entry; the validator reads rules from inside the bundle |
| Licensing | Template Apache 2.0; libraries choose their own licences, default CC BY 4.0 for content | CC BY 4.0 content and Apache 2.0 code for every library | Lets proprietary and open libraries both use the template | Libraries must track Apache 2.0 obligations for inherited files |
| Retrieval | Indexes and file reads by the agent | Vector search service; query service (e.g. an MCP server) | No infrastructure; fits libraries of a few thousand concepts with directory caps | Weaker on fuzzy queries; a search index or query service can be added later without changing the format |

## Risks, governance and what to revisit

The template's risks concern specification change, unreviewed content and weak enforcement; content risks belong to each library.

| Risk | Likelihood | Impact | Control |
| --- | --- | --- | --- |
| Agent-generated content published without expert review | High | High | `stable` requires an approval by a human directory owner; agent-drafted revisions derive the machine-confirmed tier until an owner-approved full review; stale approvals are recorded; self-approval is shown as `human-reviewed (self)`; status and tier shown in every index line |
| Checks weakened or bypassed where branch protection is unavailable (private libraries on free tiers) | Medium | High | Content validated with base-branch tooling; tooling and content in separate change proposals; re-validation on every push to the main branch with failures reported as an issue; CI secret scanning |
| Provenance gaps from missed or failed revision runs | Medium | Medium | Catch-up processing; release blocked while any merged change lacks its revision line |
| OKF spec changes break the profile | Medium | Medium | Pin `okf_version`, the specification commit and the OKF conformance checker; profile tracks OKF minors; validator enforces the frontmatter-first and datetime rules itself; follow upstream issues |
| A tool in the reference stack reaches end of life | Medium | Medium | Pinned versions; site generator replaceable without moving content (FR8.1); decision recorded per library |
| Template tied to one platform or toolchain | Low | Medium | Requirements use only common platform capabilities; named tools are examples; each library records its stack in its decision record |

### Governance

- **Roles.** Maintainers own the profile and CI. Directory owners named in the code-owners file approve changes in their directories.
- **Definition of stable.** Written in own words, at least one source cited in the body, approved by a human directory owner (one approval; a single maintainer's recorded self-approval counts), all internal links and anchors resolving, all declared sections present.
- **Decisions.** Changes to the profile or structure are recorded in the decision record before or with the change.
- **Releases.** Semver tags. Minor releases add or revise concepts; major releases change the profile in a breaking way, including renaming a declared body heading, any profile-migration change and widening the `uid` sequence. Release notes are published with each release. Downstream citations cite the `uid` and the tag.

### What to revisit as it grows

- **Above about 3,000 concepts,** or when users ask fuzzy questions, add a search index or a read-only query service over the same files.
- **When OKF reaches 1.0** or adds typed links or a body-structure convention, align the profile's body declarations with it.
- **When a second library exists,** consider moving the profile scripts into a versioned package; libraries may still diverge and customise them.
- **When a second directory owner joins,** decide whether `stable` should require an approver other than the author.

## Next steps

The template is built to the SDD build plan (SDD §14): verification spikes (P0), core tooling (P1), CI and governance (P2), site, release and skills (P3), then a pilot of about 20 concepts (P4). This document's alignment with the SDD on 25 October 2026 is the gate for P1 (DDR QA-35).

Template v1.0.0 gate: CI passes; a second person instantiates a library in under 30 minutes (FR6.1); an agent using the bundle produces outputs that a reviewer can trace to concept `uid`s and a release tag (FR7.2).

Upstream engagement: open an issue on the OKF repository proposing a profile declaration convention, covering body sections and vocabularies as well as frontmatter, and contribute the profile validator back as a standalone tool.

## Related documents

- `OKF Library Template - Software Design Document.md`
- `OKF Library Template - Design Decision Record.md`
- `OKF library technology stack options.md`

## Sources

All accessed 16 October 2026 unless stated.

- [Open Knowledge Format, specification v0.2 (Google Cloud)](https://github.com/GoogleCloudPlatform/open-knowledge-format); [SPEC.md §3.1, §4, §4.1, §11](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md) (accessed 17 October 2026); [SPEC.md history](https://github.com/GoogleCloudPlatform/open-knowledge-format/commits/main/SPEC.md) (datetime rule; accessed 18 October 2026, via the stack options report)
- [How the Open Knowledge Format can improve data sharing (Google Cloud blog, June 2026)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [scaccogatto/okf-skills](https://github.com/scaccogatto/okf-skills)
- [open-science-pillars/knowledge-template](https://github.com/open-science-pillars/knowledge-template)
- [Movida/okf-bundle-template](https://github.com/Movida/okf-bundle-template)
- [ayhansipahi/OKF-starter-bundle](https://github.com/ayhansipahi/OKF-starter-bundle)
- [supachai-j/open-knowledge-format-starter](https://github.com/supachai-j/open-knowledge-format-starter)
- [Agent Skills overview](https://agentskills.io/)
- [allenday/agent-skills-template](https://github.com/allenday/agent-skills-template) (accessed 17 October 2026)
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (accessed 17 October 2026)
- [mattpocock/skills](https://github.com/mattpocock/skills) (accessed 17 October 2026)
- Platform behaviour (DR-23): primary sources are cited in `OKF library technology stack options.md`.
