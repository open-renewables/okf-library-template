# ADR-010: Folder scope as a header on the folder index

**Status:** Accepted (owner, 2026-11-14). **Supersedes:** none; settles known gap G6 and amends the intent of SDD I-07 and FR4.3. **RFC:** [RFC-001](../rfcs/RFC-001-scope-notes.md). **Plan:** P3 step 9; implementation in P4.

## Context

SDD I-07 says a generated folder line shows "scope from the folder's scope note", but defines no scope-note type or location (G6). An agent that navigates one index level at a time needs more than a folder title to choose a folder. RFC-001 compared a scope-note concept type, a hand-written folder page and nothing. The owner chose nothing new in the concept model, plus a YAML header on `index.md`.

## Decision

1. A folder's `index.md` may open with a YAML header whose `description` key is the folder's scope, one sentence. The root index keeps its `okf_version` header; the two coexist.
2. `build_indexes.py` keeps an existing header when it regenerates an index, rewrites the body, and writes the `description` on the folder's line in the parent index (`- [Title](folder/index.md) — <description>`). A folder with no header, or no `description`, shows its title only, as today.
3. The freshness check (check 5) compares the generated body and treats the header as input, not as a difference. Everything else in an index stays generated and is never edited by hand.
4. No scope-note concept type is added, so a scope has no `uid`, revision history or trust tier.

## Consequences

- One small exception to "index files are never edited by hand" (FR4.3). The SRS wording is the owner's to change; the exception is limited to the header.
- Scope text is unreviewed by the provenance mechanism. A library that wants scope under review can use the same text in its `GOVERNANCE.md` or put it through the pull-request review it already has.
- Known gap G6 is closed by this decision; the implementation is a P4 task (about 2 to 3 agent hours): `build_indexes.py`, the check 5 comparison, fixtures, SDD I-07 and the index golden files.
- Needs, before P4 builds it: the SRS FR4.3 wording, SDD I-07 and I-02 text, and `author-concept` guidance, proposed as a plan entry for the owner.
