# Agent instructions

<!-- template-only:start -->
> **Building the template itself?** Read `docs/development/AGENTS.md` first. This block and the `docs/` folder are removed by `init_library.py` when a library is instantiated.
<!-- template-only:end -->

This repository is a library of knowledge in the Open Knowledge Format (OKF) v0.2: one Markdown file per concept in `knowledge/`, a machine-readable profile in `profile/`, and tooling in `scripts/`. Read this file first. Nothing here depends on the library's subject.

## Where things are

| Path | What it is |
| --- | --- |
| `knowledge/` | The bundle. Every `.md` file is a concept or a generated `index.md` |
| `knowledge/index.md` | Root index; each folder has its own `index.md` |
| `profile/profile.yaml` | Concept types, `uid` prefixes, body sections, vocabularies, status values, rules |
| `profile/types/`, `profile/formats/` | Frontmatter schemas and section formats |
| `knowledge/vocab/` | Controlled vocabularies, as concepts. The authoritative list of tag values |
| `profile/uid-registry.yaml` | Which `uid` is at which path. Maintained by tools |
| `GOVERNANCE.md` | Who approves what, what makes a concept `stable`, how releases work |
| `.agents/skills/` | Agent skills: `use-bundle` and `author-concept` |

## Reading the bundle

Use the `use-bundle` skill. In short: read `profile/profile.yaml`, start at `knowledge/index.md`, follow indexes one folder at a time, open a concept only when its index line fits, and read its sections by heading. Do not read the whole bundle.

**Cite** every concept you use by its `uid` and the release tag, for example `<uid>@<tag>`. A release archive names its tag in the `RELEASE` file; in a clone, use `git describe --tags` or the tag the user gives. If the tag is unknown, say so.

**Trust tier.** Each index line ends with a status and a trust tier. Report them as written.

| Tier | Meaning |
| --- | --- |
| Unverified | No review recorded. Not reviewed |
| Machine-confirmed | Drafted or checked by an agent, or approved without an owner's review. Not human-reviewed |
| Human-reviewed | A human directory owner approved it |
| `human-reviewed (self)` | Reviewed only by its author, who owns it. Say so |

Never present Unverified or Machine-confirmed content, or a `draft` or `deprecated` concept, as reviewed or current.

## Writing to the bundle

Use the `author-concept` skill from a clone. The rules that matter:

- Create concepts with `uv run scripts/new_concept.py`; never copy a file and edit its `uid`.
- Never edit by hand: any `index.md` (run `uv run scripts/build_indexes.py`), `profile/uid-registry.yaml`, or a concept's *Revision history* section. CI writes them, and validation rejects hand edits.
- Never delete a concept; deprecate it by `status: deprecated`.
- Leave new concepts `status: draft`; a human owner makes one `stable`. A `stable` concept cites a source.
- Tag values must exist in the vocabulary concepts. Adding one is a reviewed change.
- Mark agent-drafted work: the label named by `rules.agent_label` in the profile, or the commit trailer `Agent-Drafted: yes` when `platform: git-local`.
- A change to `scripts/`, `profile/` or `.github/` is a separate pull request from a change to `knowledge/`, unless it carries the profile-migration label.
- Before you finish: `uv run poe check` and `uv run poe test` pass.

## Commands

| Command | Does |
| --- | --- |
| `uv sync` | Install the locked tools |
| `uv run poe check` | Lint, types, validation, index freshness, skills |
| `uv run poe test` | The tests |
| `uv run scripts/validate_profile.py` | Validate the bundle (six checks) |
| `uv run scripts/build_indexes.py` | Regenerate the indexes |
| `uv run poe link-skills` | Optional: make the skills visible to Claude Code in your own checkout (copies into `.claude/skills/`, which is git-ignored) |

The profile's `platform` is `github` (pull requests, labels, CI on the host) or `git-local` (git and Python only; approvals and labels are commit trailers, and `uv run poe revision` writes the revision history). Both are described in `GOVERNANCE.md`.
