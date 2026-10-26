# Conventions

Judgement calls that tools can't check. The measured bar is in `constraints.md`; the design is in `../architecture/`. The commit and writing rules were set as defaults (DDR QA-75, QA-76) and confirmed by the owner on 25 October 2026, together with the docstring and branch rules.

## Design

- The profile declares everything that differs between libraries. Code holds no domain rules (SDD C-03).
- One shared module, `scripts/okfprofile/`, with thin command-line scripts over it (SDD AD-04; QA-53).
- Platform-specific behaviour lives only in a platform adapter selected by `platform` in `profile.yaml` (`github` or `git-local`). Core modules never call a platform API directly (SDD AD-19).
- Generated files (`index.md`, registry entries, revision-history lines) are written only by tooling, never by hand.
- Prefer the standard library. A new runtime dependency in the `validate` group needs an ADR.

## Code

- Python 3.11 syntax; type hints on every function (mypy strict for `okfprofile`).
- YAML is parsed with ruamel.yaml (YAML 1.2), keeping scalar values as strings; Markdown with markdown-it-py. No regular-expression parsing of Markdown structure (SDD AD-05, AD-06).
- Each validation finding has a stable code (SDD I-09); codes are never reused.
- Every script supports `--json`, exits non-zero on error and writes human-readable output to stderr.
- The GitHub REST API is reached only through `okfprofile.github`; no third-party API client.
- Docstrings: Google style, required on public modules, classes and functions in `okfprofile` (a one-line summary, then `Args:`, `Returns:` and `Raises:` where they apply). Not required on private helpers, thin scripts or tests. Checked in review, not by ruff (the `D` rules stay off).

## Module layout

- `scripts/okfprofile/<module>.py`, one responsibility per module as listed in SDD C-03; platform adapters in `scripts/okfprofile/platforms/`.
- `scripts/<verb>_<noun>.py` for entry points, each a thin wrapper.
- Tasks are declared in `pyproject.toml` under `[tool.poe.tasks]`; CI calls tasks, never inline logic (QA-54, QA-62).

## Tests

- `tests/template/` tests the tooling and instantiation and is removed at instantiation unless `--keep-tests`; `tests/library/` tests a library's own profile rules and is always kept (QA-57).
- Fixtures: `tests/library/fixtures/pass/<type>/…` must validate; `tests/library/fixtures/fail/<code>/…` must raise exactly the named finding code.
- Golden files for generated indexes, revision lines, trust tiers and `verified` mappings.
- No network access; platform API responses are recorded fixtures.
- A gap that can't be tested yet is recorded in `../testing/` as a known gap, not skipped silently.

## Docs

- British English (licence, organisation), sentence-case headings, and the project's engineering tone: evidence-based, no marketing language.
- Cross-references use exact file names; each document defines its abbreviations once.
- Dates in prose as `YYYY-MM-DD` or "25 October 2026"; timestamps in frontmatter as ISO 8601 with an explicit offset (OKF rule).
- Decision IDs are cited as written (AD-, QA-, DR-, ADR-NNN); IDs are never renumbered.

## Git

- Squash merges only; the pull request title becomes the commit subject (SDD AD-17).
- One change per pull request: tooling (including `docs/`) or content, not both, unless labelled `profile-migration` (SDD AD-18; QA-70).
- Commit subject: imperative mood, 72 characters or fewer; the body says why.
- Provenance trailers where they apply: `Approved-by:`, `Full-Review: yes`, `Agent-Drafted: yes` (required in git-local mode; QA-59).
- No force-pushes to `main`; history is rewritten only by the leak-removal runbook in `../operations/`.
- Branch names: `<kind>/<short-slug>`, lowercase hyphenated, where `<kind>` is `concept`, `fix`, `tooling`, `profile`, `docs` or `release`; for example `concept/pid-bifacial`, `tooling/git-local-adapter`. The kind shows which side of the tooling and content split the branch is on.
