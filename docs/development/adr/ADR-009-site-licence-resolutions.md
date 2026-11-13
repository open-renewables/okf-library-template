# ADR-009: Site-group licence metadata resolutions

**Status:** Proposed (P3 plan PP-8, fired by step 4; awaiting the owner). **Supersedes:** none; extends ADR-007's method and edits the metadata table in `constraints.md`. **RFC:** none. **Plan:** P3 step 4.

## Context

P3 step 4 added the `site-mkdocs` and `site-zensical` dependency groups (MkDocs 1.6.1 with Material 9.7.7, and Zensical 0.1.1) and extended the licence check to them (known gap G11). With both groups installed, `poe licences` checks 62 packages and reports three whose metadata is not an allowlisted SPDX identifier. The licence text of each was read in the installed wheel. ADR-006 had listed `python-dateutil` and `mergedeep` as open until the site groups arrived; `python-dateutil` 4.0.0 now carries SPDX metadata and passes, and `certifi` and `pathspec` are already recorded as MPL-2.0 exceptions (ADR-006, ADR-007).

| Package | Version | Reached through | Metadata | Licence text read from the installed wheel |
| --- | --- | --- | --- | --- |
| `ghp-import` | 2.1.0 | `mkdocs` | `License: Apache Software License`; classifier "Apache Software License" | Apache License, Version 2.0 |
| `jinja2` | 3.1.6 | `mkdocs`, `mkdocs-material` | classifier "BSD License" only | Pallets text, three conditions, standard BSD-3-Clause |
| `mergedeep` | 1.3.4 | `mkdocs` | `License: UNKNOWN`; classifier "MIT License" | The MIT License, standard text |

All three are in the site groups only: none is in the `validate` group and none enters the release archive (I-12).

## Decision

Resolve the three to SPDX identifiers and record each as a metadata resolution in `constraints.md`, keyed by package and version as ADR-007 decided: `ghp-import` 2.1.0 as `Apache-2.0`, `jinja2` 3.1.6 as `BSD-3-Clause`, `mergedeep` 1.3.4 as `MIT`. All three identifiers are already on the allowlist, so the allowlist does not change.

## Consequences

- `constraints.md` gains three rows in "Metadata resolutions". A new version of any of the three is a finding until its text is read again.
- Nothing is added to the release archive, so no third-party notice changes.
- The site groups are checked wherever they are installed; a system that does not install them lists them as not checked (G11 narrows to that).

## Alternatives

- Leave the three as findings: blocks CI on a known-benign result.
- Accept a looser rule (any "OSI Approved" classifier): admits MPL, LGPL and GPL classifiers, contrary to the 25 October allowlist decision.
