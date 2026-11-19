# Getting started

<!-- template-only:start -->
This page is the template's. When a library is created, `init_library.py` turns this guide into the library's own guide (the `guide: morph` answer) and replaces this page with *How this library was created* and *Working on this library*; `guide: copy` keeps the guide as written, and `guide: remove` deletes it.

## Choose how the library runs

| Platform | What you need | What you get |
| --- | --- | --- |
| `github` | A GitHub organisation, `gh` signed in | Pull requests, labels, issue forms, CI, the revision bot, Releases, an optional Pages site |
| `git-local` | `git`, Python 3.11 or later and `uv` | The same checks, revision history, trust tiers, releases and local site, run as `uv run poe` tasks; approvals and labels are commit trailers |

A `git-local` library can move to GitHub later without rewriting history ([runbook](runbooks.md#move-a-git-local-library-to-github)).

## Create the library

Three routes, all supported:

1. **"Use this template"** on GitHub (`github`): a new repository with one fresh commit.
2. **Clone** the template and push it to an empty repository, or keep it local (`git-local`). The template's history comes along, so a later template tag can be merged.
3. **Unpack a release archive** and run `git init`.

Forking is not a way to create a library. Then follow the step-by-step sheet, [Instantiate a library](runbooks.md#instantiate-a-library): `uv sync`, `uv run python scripts/init_library.py`, `uv run poe check`, a first concept, merge. With answers prepared it takes under 30 minutes.

`init_library.py` asks for the platform, the library's name, title and description, the maintainer, the licences (content default CC BY 4.0; code default Apache 2.0; proprietary allowed), the site generator (MkDocs by default, or Zensical), whether to keep the example concepts and the template's tests, and what to do with this guide. It writes the licence files, `README.md`, `CITATION.cff`, `DECISIONS.md` and the root index's `title` and `license`, and removes the template-only files.

To give the primary type (`Item`, prefix `ITM`) the library's own name, rename it before the first commit ([Customising the profile](customising.md#rename-the-primary-type)).
<!-- template-only:end -->

## Working on a clone

```bash
uv sync --all-groups
uv run poe install
uv run poe check
uv run poe test
```

`poe install` also installs the pre-commit hooks, which validate changed files, check the indexes and scan for secrets on every commit.

Create a concept with `uv run python scripts/new_concept.py <Type> <path>`, where `<path>` is the concept's location under `knowledge/` without `.md`. Fill its sections, cite its sources (see [Maintaining a library](maintaining.md#writing-a-concept)), then run `uv run python scripts/build_indexes.py` and `uv run poe check`. Agents use the `author-concept` skill for the same steps.

<!-- platform:github:start -->
On GitHub, open a pull request. CI validates it with the base branch's tooling, and the revision bot records the change after you merge.
<!-- platform:github:end -->
<!-- platform:git-local:start -->
With `git-local`, squash the change into one commit on `main` with its trailers (see [Reference](reference.md#commit-trailers-git-local)) after `uv run poe ci-validate --base main` passes, then run `uv run poe revision`.
<!-- platform:git-local:end -->
