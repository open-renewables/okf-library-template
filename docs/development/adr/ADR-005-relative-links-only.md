# ADR-005: Relative links only

**Status:** Accepted (owner, 2026-10-30), **conditional on the SRS wording change below**, which is the owner's to make. **Supersedes:** none; amends SDD I-01 and W-04 check 4. **RFC:** none.

## Context

I-01 allowed bundle-root-relative (`/path/to/concept.md#anchor`) and relative links. V-10: GitHub resolves a `/` link from the repository root, so in a template whose bundle is `knowledge/` it points at a path that does not exist (the 404 is inferred from the path). V-03: Zensical 0.0.73 leaves `/` links unresolved, which fails FR8.2 check 2. MkDocs resolves them. Relative links resolve on GitHub, MkDocs, Zensical and Docusaurus; `%20` or angle brackets handle spaces.

## Decision

Internal links are relative only. The validator rejects root-relative links; `new_concept.py` and the skills emit relative links.

## Consequences

- Removes the Zensical check-2 blocker and is a precondition of the switch in ADR-001.
- **Requirement-level change, owner to make:** FR2.10 ("a link … resolves on the hosting platform and on the site") and FR8.2 check 2 ("links starting with `/` resolve to site routes") are written around root-relative links. Under this ADR check 2 reads "relative links resolve to site routes" and root-relative links are not permitted. Until the SRS is edited, the SRS and this ADR disagree; this record is not applied to the SRS.
- P1 link check: the root-relative handling is dropped (slightly less code).

## Alternatives

Keep both forms and fix per platform (GitHub cannot be configured); rewrite root-relative links at build time (hides the GitHub 404).
