# ADR-005: Relative links only

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** none; amends SDD I-01 and W-04 check 4, and the wording of SRS FR8.2 check 2. **RFC:** none.

## Context

I-01 allowed bundle-root-relative (`/path/to/concept.md#anchor`) and relative links. V-10: GitHub resolves a `/` link from the repository root, so in a template whose bundle is `knowledge/` it points at a path that does not exist (the 404 is inferred from the path). V-03: Zensical 0.0.73 leaves `/` links unresolved, which fails FR8.2 check 2. MkDocs resolves them. Relative links resolve on GitHub, MkDocs, Zensical and Docusaurus; `%20` or angle brackets handle spaces.

## Decision

Internal links are relative only. The validator rejects root-relative links; `new_concept.py` and the skills emit relative links.

## Consequences

- Removes the Zensical check-2 blocker and is a precondition of the switch in ADR-001.
- **Requirement-level change, made by the owner on 2026-10-30:** SRS FR8.2 check 2 read "links starting with `/` resolve to site routes" and now reads "relative links between concepts resolve to site routes". FR2.10 does not name a link form and is unchanged.
- P1 link check: the root-relative handling is dropped (slightly less code).

## Alternatives

Keep both forms and fix per platform (GitHub cannot be configured); rewrite root-relative links at build time (hides the GitHub 404).
