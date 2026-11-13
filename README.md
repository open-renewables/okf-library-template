# OKF library template

[![Licence](https://img.shields.io/github/license/open-renewables/okf-library-template)](LICENSE)

A template for building validated, agent-ready knowledge libraries on the Open Knowledge Format (OKF) v0.2.

Status: beta. The tooling, set-up scripts, CI, agent skills and site build are in place; the template is not yet released as v1.0.0 (see `GOVERNANCE.md` for how releases are made).

okf-library-template is a thin "profile" layer on Google's Open Knowledge Format (OKF) v0.2, not a new format. It is independent of the OKF project and of LF Energy, and is not affiliated with either.

---
- [Features](#features)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Agent skills](#agent-skills)
- [Site and releases](#site-and-releases)
- [Documents](#documents)
- [Licence](#licence)
---

## Features

- **Readable by agents and people** - any domain can stand up a version-controlled library of markdown concepts that an agent can traverse one index level at a time and a person can browse. It needs no server or SDK.
- **Declared structure** - a machine-readable profile declares each concept type's frontmatter schema, body sections and controlled vocabularies, which live inside the bundle.
- **Permanent identifiers, never deleted** - each concept gets a permanent `uid`, tracked in a tool-maintained registry. Concepts are only deprecated.
- **Six validation checks** - OKF conformance, frontmatter, body, links and vocabularies, index freshness, and `uid` and registry integrity. Each has stable finding codes, and the same checks run locally. Content is judged by the base branch's tooling, so a change proposal cannot weaken the checks that judge it.
- **Provenance and trust tiers** - after each merge, CI appends a revision-history line to each touched concept. A trust tier (Unverified, Machine-confirmed or Human-reviewed) is derived from those lines. A `stable` concept needs a cited source and one approval from a human directory owner. A single maintainer's self-approval counts but is shown as `human-reviewed (self)`.
- **Supporting pieces** - generated `index.md` files, issue forms for contributors who do not use git, two Agent Skills (authoring and consuming), immutable semver release archives with checksums, and an optional static site built from the latest release.
- **Quick to start** - a library is created from a copy of the template plus set-up scripts, with a 30-minute target for a newcomer's first merged concept. Git and Python are enough to operate a library; a hosting platform is optional, and the GitHub reference stack on free tiers is one supported choice.

## Quick start

Requirements: Python 3.11 or later, [uv](https://docs.astral.sh/uv/) and git. A hosting platform such as GitHub is optional; the `gh` command line is needed only to configure a GitHub repository.

Start a library by one of three routes:

| Route | When |
| --- | --- |
| **Use this template** on GitHub (or `gh repo create <org>/<name> --template open-renewables/okf-library-template`) | The usual route: an independent repository with one fresh commit |
| Clone the template, then push to a new empty repository or keep it local | A library without a hosting platform (`git-local`), or one that wants to merge later template tags |
| Download a release archive of the template | Files only; then `git init` |

Do not fork the template to start a library: a fork stays linked to the template.

Then, in the new repository:

```bash
uv sync --all-groups
uv run poe init
```

`poe init` asks for the platform (`github` or `git-local`), the library's name and maintainer, and its licences, rewrites the template's names and removes the template-only files. With `platform: github`, run `uv run poe setup-repo` to configure labels, merge methods, permissions and, for a public library, the ruleset. Finish with `uv run poe check`, create a first concept with `uv run python scripts/new_concept.py <Type> <path>` and merge it. The step-by-step run sheet, with timings, is `docs/development/operations/runbook-instantiate-library.md`.

## Commands

Everything CI runs is a task you can run locally (`uv run poe` lists them).

| Command | Does |
| --- | --- |
| `uv run poe check` | Lock check, lint, types, validation, index freshness, skills check |
| `uv run poe test` | The tests, with coverage |
| `uv run poe selftest` | Instantiate the template for each platform in a scratch folder and check the result |
| `uv run poe docs` | Serve the site with live reload (needs `uv sync --group site-mkdocs`) |
| `uv run poe docs-build` | Build the site with MkDocs, strict |
| `uv run poe bundle <tag>` | Build the release archive, checksum and manifest into `dist/` |
| `uv run poe release <tag>` | Release gate and, with `git-local`, the annotated tag |
| `uv run poe revision` | `git-local`: record merged changes as revision-history lines |
| `uv run poe stale` | List concepts past their review date |

## Agent skills

Two skills in `.agents/skills/` follow the Agent Skills format: `use-bundle` navigates the bundle's indexes and cites each concept by `uid` and release tag, and `author-concept` drafts a concept to the profile. `AGENTS.md` names them. To make them visible to Claude Code in your own checkout, run `uv run poe link-skills`; it copies them into the git-ignored `.claude/skills/`.

## Site and releases

- **Site.** One `mkdocs.yml` builds the bundle in place with MkDocs and Material (blocking) and with Zensical (non-blocking). Every change gets a preview artifact; no public site exists before a library's v1.0.0.
- **Releases.** A semver tag cuts a release: an archive of the bundle, the profile, `AGENTS.md` and the `use-bundle` skill, with its SHA-256 and a manifest. A release fails while any merged change lacks its revision-history line.

## Documents

The design documents are in `docs/development/`; start with [docs/development/README.md](docs/development/README.md). The rules for running a library are in [GOVERNANCE.md](GOVERNANCE.md).

| Document | What it covers |
| --- | --- |
| [Software Requirements Spec](docs/development/requirements/OKF%20Library%20Template%20-%20Software%20Requirements%20Spec.md) | What the template must do, with acceptance criteria |
| [Software Design Document](docs/development/architecture/OKF%20Library%20Template%20-%20Software%20Design%20Document.md) | How it is built on the reference stack, and the build plan |
| [Design Decision Record](docs/development/adr/OKF%20Library%20Template%20-%20Design%20Decision%20Record.md) | Why each decision was made, and the change log |
| [Technology stack options](docs/development/architecture/OKF%20library%20technology%20stack%20options.md) | The stack analysis behind the reference stack |

## Licence

Apache 2.0 for the template repository (see `LICENSE` and `NOTICE`). A library created from the template is licensed by its owner: `init_library` writes `LICENSE` (the owner's code and changes), `LICENSE-content` (the knowledge bundle; CC BY 4.0 by default) and, when the code licence is not Apache 2.0, `LICENSE-template` for the files inherited from the template.
