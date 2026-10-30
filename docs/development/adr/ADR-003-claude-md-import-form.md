# ADR-003: `CLAUDE.md` import form

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** none; amends the wording of QA-36 (file names unchanged). **RFC:** none.

## Context

The design documents have spaces in their file names (QA-36, QA-67). V-10 (fresh Claude Code sessions in `p0-spikes`, round 2 included): the four `@docs/development/…` imports with unescaped spaces do not load; only the backslash-escaped form loads, also with hyphens, nested folders and nested imports.

## Decision

Keep the file names. In `CLAUDE.md`, write imports with backslash-escaped spaces, for example `@docs/development/requirements/OKF\ Library\ Template\ -\ Software\ Requirements\ Spec.md`. Markdown links keep `%20` or angle brackets (ADR-005).

## Consequences

- `CLAUDE.md` is edited accordingly and its comment now cites this ADR.
- Verified for Claude Code only; the file is template-only and is removed at instantiation (ADR-002).

## Alternatives

Rename the files without spaces (rejected by QA-36 and QA-67); keep the unescaped imports (do not load).
