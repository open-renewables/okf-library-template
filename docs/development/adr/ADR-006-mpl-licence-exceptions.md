# ADR-006: MPL-2.0 licence exceptions

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** none; edits the exception table in `constraints.md`. **RFC:** none.

## Context

`constraints.md` allows MPL-2.0 only by recorded exception. V-03: `pathspec` 1.1.1 (both site stacks) and `certifi` (the MkDocs stack) are MPL-2.0. Two further metadata gaps: `python-dateutil` reports "Dual License" and `mergedeep` reports none.

## Decision

Record exceptions for `pathspec` and `certifi`: site dependencies, unmodified, not part of the `validate` group. Review by 2027-04-30. The licence check reads SPDX or classifier metadata and treats a missing or non-SPDX value, including the two gaps above, as a finding to resolve explicitly.

## Consequences

- `constraints.md` lists both exceptions and the metadata rule.
- If the site generator switches (ADR-001), `certifi` may drop out; the review date covers that.

## Alternatives

Remove the dependencies (not possible; they come with the site stacks); widen the allowlist to MPL-2.0 (rejected by the owner's 25 October allowlist decision).
