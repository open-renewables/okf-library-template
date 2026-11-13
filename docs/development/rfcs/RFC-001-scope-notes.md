Status: Draft

ADRs produced: none yet.

# RFC-001: Folder scope notes

## Problem

SDD I-07 says a generated folder line reads "scope from the folder's scope note", for example `- [Example category](example-category/index.md) — scope from the folder's scope note`. The SDD defines no scope-note type and no location. Today a generated folder line carries the folder title only (known gap G6). An agent that navigates one index level at a time has nothing to decide which folder to open except its title, and the P4 pilot needs scope notes (SDD §14: the pilot library authors scope notes with its concepts). The decision is wanted before P4 starts.

Constraints that any answer must respect:

- Every non-reserved `.md` file in the bundle is a concept with frontmatter and a `type` (OKF §4, §11); `index.md` and `log.md` are reserved names.
- `index.md` files are generated and never edited by hand (FR4.3, check 5), so a scope note cannot live in them.
- Concepts get a permanent `uid`, are never deleted and carry provenance (FR1.3, FR1.7, FR3).
- The tooling holds no domain rule (FR2.1): the mechanism must be declared in the profile, and a library chooses whether to use it.

## Options

**A. A scope-note concept type, one per folder.** The template adds a declared type `Scope` (prefix chosen by the library, for example `SCN`) with a fixed file name in each folder, for example `scope.md`. Its frontmatter `description` is the one-sentence scope; its body can say what belongs in the folder and what does not. `build_indexes.py` reads the folder's scope note and writes its description on the folder line, as I-07 describes. Scope notes are concepts: they have a `uid`, a status, a revision history and a trust tier, and the validator checks them like any concept.

**B. Frontmatter on a hand-written folder page.** The folder's landing page is written by hand with frontmatter. This conflicts with generated `index.md` (FR4.3) and with the reserved name, so it needs either a second landing-page file or an exception to "indexes are never edited by hand". It also gives the page no `uid`.

**C. None.** Folder lines keep the folder title. Libraries that want a scope put it in their root `glossary.md` or in the folder name.

## Comparison

| Criterion | A. Scope-note type | B. Hand-written page | C. None |
| --- | --- | --- | --- |
| Agent can choose a folder from its index line | Yes | Yes | Title only |
| Consistent with FR1.3, FR3, FR4.3 | Yes: an ordinary concept | No: needs an exception | Yes |
| Tooling change | `build_indexes` reads one declared type; profile declares the file name | An exception in `build_indexes` and the validator | None |
| Domain rule in the tooling (FR2.1) | None: the type and file name are in the profile | Likely | None |
| Cost to a library | One small concept per folder | One page per folder, outside provenance | None |
| Fits the P4 pilot | Yes | Awkward | Pilot has no scope notes |

## Recommendation

Option A, declared by the profile, optional per library: a library that declares no scope type gets today's behaviour, so option C remains available without a template change. In the profile, a new optional key names the type and file name that supply a folder's scope (for example `index.scope_note: {type: Scope, file: scope.md}`); `build_indexes.py` uses the note's `description` when present and the folder title otherwise; a missing note is a warning, not an error, so a library can adopt it folder by folder.

This is a recommendation only. Nothing is built in P3 (plan OD-4).

## What a decision needs

- The owner chooses A, B or C before P4.
- If A: an ADR records it, SDD I-02 (the profile key) and I-07 (the folder line) are edited, the template ships the type's schema and one example scope note, and `build_indexes.py`, `new_concept.py` and the validator are changed with tests. The effort is about 2 to 3 agent hours and is added to the P4 plan.
- If C: close known gap G6 as "decided: none" and amend I-07's example line.
