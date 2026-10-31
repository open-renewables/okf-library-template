# ADR-008: Lint exemption for vendored third-party code

**Status:** Accepted (owner, 2026-10-31). **Supersedes:** none; edits the Code row of `constraints.md`. **RFC:** none. **Plan:** P1 step 4, proposed entry PP-1.

## Context

SDD AD-08 vendors okf-skills' `okf_validate.py` at a pinned commit so that check 1 gives the same result locally and in CI, and QA-44 requires it to run in `validate_profile.py`. The file is 600 lines of third-party code that follows its own repository's style. It does not meet the project's ruff rule set in `constraints.md` (Code row: zero findings under `ruff check scripts tests` and `ruff format --check scripts tests`). Editing it to pass would change it from the pinned commit, which defeats the purpose of pinning and the recorded hash.

The other two limits in the same rows are not affected: `mypy --strict` targets `scripts/okfprofile` only, and coverage is measured on `scripts/okfprofile` only. The vendored file is loaded by path at run time, not imported statically.

## Decision

1. Exclude `scripts/vendor/` from `ruff check` and `ruff format` (`extend-exclude` in `pyproject.toml`). Nothing else under `scripts/` or `tests/` is excluded.
2. Compensating controls, all in the repository: the file is verbatim and its SHA-256 is recorded in `scripts/vendor/okf-skills/VENDORED.md` and checked by a test; the licence and notice texts are carried; every message the file emits is mapped by `okfprofile.checks.conformance` and a test fails on an unmapped message; a patch to the file needs an ADR amending AD-08.
3. `constraints.md` gains a note under the Code table: "`scripts/vendor/` is excluded from ruff (ADR-008)".

## Consequences

- A new vendored file would need to be listed under `scripts/vendor/` with its own `VENDORED.md`; the exemption covers the folder, so adding a file there is a reviewed change.
- The Site, Types and Tests rows of `constraints.md` are unchanged.

## Alternatives

- Per-file ruff ignores for the rules the file breaks: a longer list in `pyproject.toml` that changes whenever the pin does, with the same effect.
- Patch the file until it passes: breaks the verbatim copy and the hash; rejected by AD-08.
- Run the upstream script as a subprocess from outside the repository tree: needs a download at install time, which the hash-locked, offline-capable set (NFR6, NFR7) avoids.
