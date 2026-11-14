# ADR-011: A library chooses its site generator

**Status:** Accepted (owner, 2026-11-14, with the request for plan step 14). **Supersedes:** none; amends ADR-001 and SDD AD-13 (the blocking builder is the library's choice, MkDocs the default). **RFC:** none. **Plan:** P3 step 14, proposed entry PP-14.

## Context

ADR-001 made MkDocs with Material the blocking site build and Zensical a non-blocking build, with the switch to Zensical to follow when it passed the six FR8.2 checks on the pilot bundle. Since then three things changed. Zensical 0.1.1 passes all six checks on the fixture bundle and reads the same `mkdocs.yml` (P3 step 5). Material for MkDocs reached end of life on 5 November 2026. And a 604-concept bundle builds in 4.3 s with Zensical against 7.7 s with MkDocs. A library may reasonably want Zensical as its main builder, while Zensical is still pre-1.0 and silently ignores settings it does not support.

## Decision

1. The profile declares `site.generator`: `mkdocs` or `zensical`. It defaults to `mkdocs` when the key is absent, and `init_library.py` asks for it (answers key `site_generator`, default `mkdocs`).
2. The library's generator is the primary, blocking build: `poe docs`, `poe docs-build` and the `primary` job of `site.yml` use it, and its output goes to `site/`. The other generator builds as a non-blocking comparison (`poe docs-alt`, the `alternate` job, output in `site-alt/`) with the page-list comparison and the lychee check.
3. One `mkdocs.yml` still serves both, and both dependency groups stay in `pyproject.toml` and `uv.lock`; a library installs only the primary's group (`uv sync --group site-<generator>`). No Zensical-only key is added to `mkdocs.yml` (ADR-001's carried issue).
4. The template's own default stays `mkdocs`, the build proven in CI on every change. The default is revisited before `v1.0.0`.

## Consequences

- No second build mechanism: the choice changes which builder is blocking, not how builds are made. The W-10 self-test instantiates both generators (one per platform) and builds the site strictly with each.
- A library that picks Zensical takes on its pre-1.0 risk for the build that gates its pull requests; the MkDocs comparison build still runs and reports page differences.
- Supersedes the "blocking build is MkDocs" wording of ADR-001 and AD-13; the SDD wording (I-02, I-13, C-07, W-01 step 3, W-08, I-16) is edited under PP-14.
