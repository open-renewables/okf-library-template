# ADR-007: Dev-group licence exception and metadata resolutions

**Status:** Accepted (owner, 2026-10-31). **Supersedes:** none; amends ADR-006 and edits the licence tables in `constraints.md`. **RFC:** none. **Plan:** P1 step 1, proposed entry PP-3.

## Context

P1 step 1 locked the dependency set (`uv.lock`, 36 packages) and read each package's licence metadata. `constraints.md` allows only the listed SPDX identifiers, allows `MPL-2.0` only by recorded exception, and treats a missing or non-SPDX value as a finding to resolve explicitly. Three packages need a decision. All three are in the `dev` group only; none is in `validate`.

| Package | Version | Reached through | Metadata | Licence text read from the installed wheel |
| --- | --- | --- | --- | --- |
| `pathspec` | 1.1.1 | `mypy` | classifier "Mozilla Public License 2.0 (MPL 2.0)" | MPL-2.0 |
| `nodeenv` | 1.11.1 | `pre-commit` | `License: BSD`; classifier "BSD License" | Three conditions (source and binary redistribution notices; no endorsement by contributor names) with the BSD warranty disclaimer: BSD-3-Clause in substance, with different wording in the third condition ("The names of the contributors may not be used…") |
| `colorama` | 0.4.6 | `pytest` (Windows) | classifier "BSD License" only | BSD-3-Clause, wording unchanged |

ADR-006 recorded `pathspec` as an exception because it is a dependency of the MkDocs and Zensical site stacks, and says it is "not part of the `validate` group". It did not anticipate that `mypy`, required by `constraints.md` (Types row), brings the same package into `dev`.

## Decision

1. **`pathspec` (MPL-2.0).** Extend the ADR-006 exception to the `dev` group. The reason becomes: dependency of `mypy` (`dev`) and of the site stacks; unmodified; not in the `validate` group; not distributed in the release archive. Review by 2027-04-30, the existing date.
2. **`colorama` and `nodeenv`.** Resolve to SPDX `BSD-3-Clause` and record each as a metadata resolution in `constraints.md`, with the reason that the licence text was read and matches. `nodeenv`'s wording is not the SPDX text verbatim; the resolution says so, and the owner accepts it as BSD-3-Clause for this purpose. `BSD-3-Clause` is already on the allowlist, so the allowlist does not change.
3. **Checker rule.** The licence check (P2, `template-tests.yml`) reads SPDX or classifier metadata. A resolution in `constraints.md` is keyed by package and version, so a new version of either package is a finding again until someone re-reads it.

## Consequences

- `constraints.md` gains one row in the exception table (`pathspec`, `dev`, via this ADR) and a new "Metadata resolutions" table with the two BSD packages. The ADR-006 rows stay as written.
- The release archive carries no `dev` or `validate` packages, only the files listed in I-12, so no third-party notice is added for these three.
- `python-dateutil` and `mergedeep` (ADR-006) are still open; they enter only with the site groups in P3.
- If `mypy` later drops `pathspec`, the exception row is removed at its review date.

## Alternatives

- Widen the allowlist to MPL-2.0 (rejected by the owner's 25 October allowlist decision).
- Replace `mypy` (the Types row names `mypy --strict`, so this needs its own ADR and is out of proportion for one transitive dependency).
- Run `mypy` outside the lock with `uvx`, as pip-audit is (the allowlist already excludes `uvx` tools). This removes `pathspec` from the lock but breaks the `poe check` parity between local and CI environments that AD-20 and QA-55 rely on.
- Leave `colorama` and `nodeenv` unresolved and let the P2 check fail on them: it would block CI on a known-benign result.
