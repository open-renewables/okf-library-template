# Test strategy

What is tested at which level, and why. The measured limits (coverage, matrix) are in [constraints.md](../constraints.md); what each fixture proves is in [fixtures.md](fixtures.md); what is not covered is in [known-gaps.md](known-gaps.md). Written at the end of build phase P1.

## Levels

| Level | Where | What it proves | Run by |
| --- | --- | --- | --- |
| Unit | `tests/template/test_*.py` | One module behaves as specified: reader (YAML 1.2 strings, CRLF, nesting, footnotes, anchors), each check, registry numbering, change classification, code owners, tier derivation, scaffolding, command-line exit codes and `--json` | `uv run poe test` |
| Fixture bundle | `tests/library/fixtures/`, driven by `tests/library/test_fixtures.py` | A whole small bundle (with optional base, change proposal and owners) raises exactly the finding code named by its `fail/` folder, or no error for a `pass/` folder. This is the proof behind "every finding code has a failing fixture" | `uv run poe test` |
| Golden file | `tests/template/golden/` | Generated output stays byte-identical: the four index shapes and every I-08 revision-tier case (`tiers.json`) | `uv run poe test` |
| Self-validation | `knowledge/` and `tests/library/fixtures/pass/` | The shipped example bundle has zero errors and its indexes are current | `uv run poe check` |
| Local CI-style parity | `tests/template/test_cli.py` | A plain local run and a `--tooling-from <ref> --base <ref>` run on the same commit give identical JSON (FR2.8, FR2.11); FR2.5 is exercised in a real scratch git repository | `uv run poe test` |
| Catalogue | `tests/template/test_catalogue.py` | Every code in `scripts/okfprofile/codes.py` has a row in [finding-codes.md](../architecture/finding-codes.md), every row names a code that exists, and every fixture or test path listed exists | `uv run poe test` |

Tests use no network. Tooling tests that need git build a scratch repository under `tmp_path`.

## Rules the levels follow

- A new finding code needs a registry entry, a catalogue row and a `fail/<code>/` fixture in the same change. The catalogue test fails otherwise. A code that cannot be reached through the template profile is proved by a unit test and listed in [known-gaps.md](known-gaps.md).
- A fixture raises one code only. If it raises another, fix the fixture, not the assertion.
- Behaviour that cannot be tested yet is written down as a known gap, not skipped.

## Running the gate

```bash
uv run poe check
uv run poe test
```

`check` runs the lock check, ruff, mypy strict on `scripts/okfprofile`, then `validate_profile.py` and `build_indexes.py --check` on the repository. `test` runs pytest with branch coverage and fails under 85 %. Timing of the validator on a generated 600-concept bundle is in [performance.md](performance.md).

### Version matrix on Windows

`uv run --python 3.11 poe test` fails on Windows because one shared `.venv` cannot serve several interpreters. Give each version its own environment and name the interpreter:

```powershell
$env:UV_PYTHON = "3.11"
$env:UV_PROJECT_ENVIRONMENT = ".venv-3.11"
uv sync --all-groups
uv run poe check
uv run poe test
```

Repeat for `3.12` and `3.14`. Hosted CI runs the 3.11 and 3.14 jobs in P2.

## What P2 adds

| Addition | Why it is not in P1 |
| --- | --- |
| Hosted CI on Linux, macOS and Windows, Python 3.11 and 3.14 | P1 ran on one machine (plan OD-9) |
| `tests/template/instantiation/` and the W-10 self-test, with and without a platform | `init_library.py` is P2 |
| Recorded platform API responses as fixtures for the platform adapters and the revision writer: golden revision lines for each approval case, a dropped run, catch-up, `verified` mapping | The revision writer and adapters are P2 |
| `OKF9xx` fixtures (revision completeness) | Declared with `write_revision.py --check-since` |
| Validation-speed gate on a 600-concept bundle (the constraint is timed in P2) | P1 records a figure for information only |
| `scan.py`, gitleaks, pip-audit and licence-check jobs, and their tests | Plan OD-2, OD-3 |
| Planted-secret test (NFR6) | Needs the scan jobs |

P3 adds the six site compatibility checks on the pilot bundle (FR8.2) and a skills run from the release archive; P4 adds the second-person timing (FR6.1) and the traced agent run (FR7.2).
