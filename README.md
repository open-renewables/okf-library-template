# OKF library template

[![Licence](https://img.shields.io/github/license/open-renewables/okf-library-template)](LICENSE)

A template for building validated, agent-ready knowledge libraries on the Open Knowledge Format (OKF) v0.2.

Status: in development (build phase P0). This README describes the planned design; the tooling, set-up scripts and agent skills are not built yet.

okf-library-template is a thin "profile" layer on Google's Open Knowledge Format (OKF) v0.2, not a new format. It is independent of the OKF project and of LF Energy, and is not affiliated with either.

---
- [Features](#features)
- [Requirements](#requirements-planned)
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

## Requirements (planned)

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- git; a hosting platform such as GitHub is optional

## Documents

The design documents are in `docs/development/`; start with [docs/development/README.md](docs/development/README.md).

| Document | What it covers |
| --- | --- |
| [Software Requirements Spec](docs/development/requirements/OKF%20Library%20Template%20-%20Software%20Requirements%20Spec.md) | What the template must do, with acceptance criteria |
| [Software Design Document](docs/development/architecture/OKF%20Library%20Template%20-%20Software%20Design%20Document.md) | How it is built on the reference stack, and the build plan |
| [Design Decision Record](docs/development/adr/OKF%20Library%20Template%20-%20Design%20Decision%20Record.md) | Why each decision was made, and the change log |
| [Technology stack options](docs/development/architecture/OKF%20library%20technology%20stack%20options.md) | The stack analysis behind the reference stack |


## Licence

Apache 2.0 (see `LICENSE` and `NOTICE`).
