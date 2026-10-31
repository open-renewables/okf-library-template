# Constraints: the measured quality bar

These limits are enforced by tools, locally through `uv run poe check` and `uv run poe test` and in CI through the same tasks (SDD AD-20 and C-05; DDR QA-62). They apply to the whole template repository. Never weaken a limit to make a change pass: a change to this file needs an ADR in `../adr/`.

Each row names its source. Rows marked **To fill** are not yet decided; the maintainer completes them before build phase P2.

## Dependencies and environment

| Constraint | Limit | Enforced by | Source |
| --- | --- | --- | --- |
| Lock file matches `pyproject.toml` | `uv lock --locked` passes | `poe check` | QA-55 |
| Supported Python | 3.11 minimum; CI tests 3.11 and 3.14; `.python-version` pins 3.12 | CI matrix | QA-65 |
| Validation dependency set | ruamel.yaml, markdown-it-py, mdit-py-plugins, jsonschema, plus the vendored okf-skills validator and their dependencies; nothing else in the `validate` group | Review; licence check | SDD AD-04, §12 |
| Installs in CI | `requirements/validate.txt` installed with `--require-hashes` | `validate.yml` | SDD §10 |

## Code

| Constraint | Limit | Enforced by | Source |
| --- | --- | --- | --- |
| Lint | Zero ruff findings with rules YTT, S, B, A, C4, T10, SIM, I, C90, E, W, F, PGH, UP, RUF, TRY; ignored E501, E731; S101 allowed in `tests/`; line length 120 | `ruff check scripts tests` | QA-55, QA-73 |
| Format | `ruff format --check scripts tests` passes | `poe check` | QA-55 |
| Types | `mypy --strict` on `scripts/okfprofile` with zero errors; `scripts/*.py` and `tests/` in default mode with zero errors; every `type: ignore` names its error code and carries a comment | `poe check` | QA-72 |

`scripts/vendor/` (verbatim third-party code, hash recorded) is excluded from ruff check and format (ADR-008). Nothing else is excluded.

## Tests

| Constraint | Limit | Enforced by | Source |
| --- | --- | --- | --- |
| Test suite | All tests pass on Python 3.11 and 3.14 | `poe test`; CI matrix | QA-57, QA-65 |
| Coverage | At least 85 % for `scripts/okfprofile`, measured by coverage.py with branch coverage on (`fail_under = 85`); thin scripts excluded | `poe test` | SDD §12; QA-71 |
| Finding codes | Every validation finding code has at least one failing fixture | `tests/template/` | SDD §12 |
| Network | No test reaches the network; GitHub API calls are replayed from recorded fixtures | Test design | conventions.md |

## Content tooling

| Constraint | Limit | Enforced by | Source |
| --- | --- | --- | --- |
| Bundle validation | Zero errors from `validate_profile.py` on `knowledge/` and on `tests/library/fixtures/pass/` | `poe check` | SDD W-04 |
| Generated indexes | `build_indexes.py --check` reports no difference | `poe check` | SDD W-04 check 5 |
| Validation speed | 600 concepts in under 10 s locally; `validate` job under 3 min | Timed in P2 | SDD §12 |
| Site | `mkdocs build --strict` passes (blocking); Zensical build non-blocking until the switch criterion in ADR-001 is met | `poe docs-build` | SDD AD-13; ADR-001 |

## Security

| Constraint | Limit | Enforced by | Source |
| --- | --- | --- | --- |
| Secrets | Zero gitleaks findings on every pull request and push to `main` (CLI at a pinned version, checksum verified); locally the hook runs only if gitleaks is installed | CI; pre-commit | QA-74 |
| Confidentiality markers | Zero findings from `scripts/scan.py` | pre-commit; CI | QA-56 |
| Known vulnerabilities | Zero pip-audit findings on the locked set, except exceptions listed below; run on every pull request that changes `uv.lock` and weekly; manual `poe audit` in git-local mode | CI; `poe audit` | QA-74 |
| Licences | Every locked dependency's licence is on the allowlist below | `template-tests.yml` | SDD §10 |
| Workflows | Actions pinned by full commit SHA; default `GITHUB_TOKEN` permissions read-only, each job declares its own; no `pull_request_target` | Review; organisation SHA-pinning policy where available | SDD AD-02, §10 |

### Licence allowlist

Allowed SPDX identifiers (owner decision, 25 October 2026):

`MIT`, `MIT-0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Apache-2.0`, `PSF-2.0`, `Python-2.0`, `Unlicense`, `0BSD`, `Zlib`.

`MPL-2.0` is allowed only by a recorded exception below. GPL, LGPL and AGPL licences are not allowed in the locked dependency set. The licence check reads SPDX or classifier metadata and treats a missing or non-SPDX value (for example `python-dateutil` "Dual License", `mergedeep` none) as a finding to resolve explicitly. Tools run outside the lock with `uvx` (for example Copier or pip-audit) are not covered by this list.

| Exception | Package | Licence | Reason | Review by |
| --- | --- | --- | --- | --- |
| ADR-006 | `pathspec` | MPL-2.0 | Site dependency of MkDocs and Zensical; unmodified; not part of the `validate` group | 2027-04-30 |
| ADR-006 | `certifi` | MPL-2.0 | Site dependency of the MkDocs stack; unmodified; not part of the `validate` group | 2027-04-30 |
| ADR-007 | `pathspec` (`dev` group) | MPL-2.0 | Dependency of `mypy` in the `dev` group, as well as of the site stacks; unmodified; not in the `validate` group; not in the release archive | 2027-04-30 |

### Metadata resolutions

Packages whose metadata is not an allowlisted SPDX identifier, resolved by reading the licence text (ADR-007). A resolution applies to the version shown; a new version is a finding until re-read.

| ADR | Package | Version | Metadata | Resolved as | Basis |
| --- | --- | --- | --- | --- | --- |
| ADR-007 | `colorama` | 0.4.6 | classifier "BSD License" | `BSD-3-Clause` | Licence text is the standard BSD-3-Clause |
| ADR-007 | `nodeenv` | 1.11.1 | `License: BSD` | `BSD-3-Clause` | Three BSD conditions; endorsement clause worded differently from the SPDX text; accepted by the owner |

### pip-audit exceptions

| Advisory | Package | Reason | Review by |
| --- | --- | --- | --- |
| — | — | None recorded | — |

### Pinned tool versions

**To fill at the start of P2** (owner decision, 25 October 2026): the gitleaks version and the SHA-256 of its release asset, taken from the release's checksums file when the CI job is written; the lychee version (optional local tool). For reference, the latest tags on 25 October 2026 were gitleaks v8.30.1 and lychee v0.24.2.
