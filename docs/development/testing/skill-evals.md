# Skill evaluations

Prompts and expected behaviour for the two agent skills, for the agent runs in build phase P4 (AT-FR7.1-02, AT-FR7.1-03, AT-FR7.2-01, AT-FR7.2-02) and for the single-provider smoke runs in P3 (plan step 11). Data only: nothing here runs in CI, because triggering a skill needs a model (P3 plan OD-14). Provider-neutral (ADR-002): a run gives the agent the files named, the prompt, and nothing else.

Static checks that do run in CI are in `scripts/check_skills.py` (frontmatter, name, size, links, no profile-specific term). A run passes when every "expect" line holds; wording differs between runs and providers.

## use-bundle

Setup: an unpacked release archive (or a clone), with `AGENTS.md` and `.agents/skills/use-bundle/`.

### Should trigger

| # | Prompt | Expect |
| --- | --- | --- |
| U1 | "What does this library say about `<topic the reviewer chose>`?" | Starts at `knowledge/index.md`, follows folder indexes one level at a time, opens only concepts whose index line fits, reads sections by heading |
| U2 | "Using the knowledge bundle, which concepts apply to `<scenario>`?" | As U1; lists each concept as `<uid> · <title> · <status> · <tier> · <tag> · <path>` |
| U3 | "Explain the tag `<namespace:value>` used on `<concept>`" | Reads the definition in the vocabulary concept before answering |
| U4 | "Is `<concept>` reviewed?" | States the tier exactly as the index line shows it, including `(self)`; explains what it means |

### Should not trigger

| # | Prompt | Expect |
| --- | --- | --- |
| N1 | "Add a concept about `<topic>`" | Uses `author-concept`, not this skill |
| N2 | "Fix the typo in the README" | Neither skill |
| N3 | "How do I install uv?" | Neither skill |

### Behaviour that must hold

- The release tag is taken from the archive's `RELEASE` file (once it exists, P3 plan PP-3), else from the user; an unknown tag is reported as unknown, never invented.
- A concept that is `draft`, `deprecated`, Unverified or Machine-confirmed is never called reviewed, approved or current (AT-FR7.2-02).
- No bundle file is changed.
- A question the bundle does not answer is reported as unanswered; general knowledge, if added, is labelled.
- Every citation resolves: the `uid` exists at that tag (AT-FR7.2-01 pass line: 100 %).

## author-concept

Setup: a clone of a library (or scratch library) with Python 3.11 or later and `uv`, `AGENTS.md`, `.agents/skills/author-concept/`.

### Should trigger

| # | Prompt | Expect |
| --- | --- | --- |
| A1 | "Write a concept about `<topic>` with these sources: `<links>`" | Reads the profile, picks the declared type, runs `new_concept.py`, fills declared sections in order, cites footnotes, `status: draft`, indexes rebuilt, validation exits 0 |
| A2 | "Draft one concept of each declared type" | One concept per type that validates; vocabulary and glossary special cases handled by hand as the skill says |
| A3 | "Add this note to the library: `<text>`" | Same as A1; does not paste the text without citing |

### Should not trigger

| # | Prompt | Expect |
| --- | --- | --- |
| N4 | "What does the library say about `<topic>`?" | Uses `use-bundle` |
| N5 | "Change the profile so a section is optional" | Neither skill; tooling change, separate pull request, an owner's decision |

### Behaviour that must hold

- Tags come only from the vocabulary concepts; a missing value is reported, not added.
- The draft is marked agent-drafted: the label in `github` mode, the `Agent-Drafted: yes` trailer in `git-local` mode.
- No hand edit to a *Revision history* section, an `index.md` or the registry.
- Nothing is marked `stable` or reviewed; no `verified` field added.
- No check, schema or profile rule is weakened to make the draft pass.
- `uv run poe check` passes before hand-over.
