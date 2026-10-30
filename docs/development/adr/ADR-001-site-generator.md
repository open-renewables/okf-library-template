# ADR-001: Site generator

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** none; confirms AD-13 and settles the review item in QA-38. **RFC:** none.

## Context

AD-13 and QA-38 require the generator decision at the P0 exit because Material for MkDocs reaches end of life on 2026-11-05. V-03 and V-04 (2026-10-27; Zensical 0.0.73, Docusaurus 3.10.2) found that Zensical fails FR8.2 check 2 by configuration alone (it emits `/`-rooted links verbatim) and that Docusaurus fails check 5 (`slug` and `id` change URLs). Evidence: `open-renewables-sandbox/p0-spikes`, `spikes/V-03-zensical`, `spikes/V-04-docusaurus`, `exit/generator-recommendation.md`.

## Decision

Confirm AD-13. MkDocs 1.6.1 with Material 9.7.x is the blocking build (`mkdocs<2`). Zensical, exact-pinned, builds the same `mkdocs.yml` non-blocking, with an offline link check and a page-list comparison on its output. The expected release site is Zensical. Zensical becomes blocking, and MkDocs non-blocking, when it passes all six FR8.2 checks on the pilot bundle by configuration alone and its dependency licences are on the allowlist or recorded as exceptions. The switch is recorded in a later ADR. Docusaurus is not adopted. The Zensical checks are not rerun in P0; the known issues below are carried and re-tested by the parallel job from P3.

## Consequences

- The blocking build depends on software past its end of life from 2026-11-05. The exposure is accepted while sites are previews, with review no later than the pilot (P4) and at the switch.
- The link rule (ADR-005) is a precondition of the switch, since check 2 cannot pass with `/`-rooted links.
- `constraints.md` row "Site" now reads "until the switch criterion in ADR-001 is met".
- MPL-2.0 exceptions (`pathspec`, `certifi`) are recorded under ADR-006.
- Known issues carried: `validation.links.anchors` is ignored by Zensical, whose own keys are `invalid_links` and `invalid_link_anchors`; whether MkDocs tolerates both sets in one file is untested beyond `theme.variant: classic` (P3). Zensical skips unsupported settings without warning, so judge its output, not its exit code. Non-ASCII automatic slugs differ from GitHub's (AD-14 already requires explicit anchors). Zensical is alpha software: exact pin and a review on each bump. No `gh-deploy`, no `--site-dir`, no `tags.json`: publishing is host-specific.

## Alternatives

- Zensical blocking now: fails check 2.
- Docusaurus: fails check 5; adds a Node toolchain (1,274 packages) and licences off the allowlist.
- Wait for a later Zensical release: does not remove the post-end-of-life exposure and delays the decision past its due date.
