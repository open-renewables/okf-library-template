# Vendored: okf-skills validator

`okf_validate.py` is a verbatim copy of the OKF conformance checker from okf-skills. It is not edited here (SDD AD-08, QA-44); `okfprofile` runs it for check 1 and maps its messages to finding codes.

| Item | Value |
| --- | --- |
| Source | https://github.com/scaccogatto/okf-skills, path `skills/validate/scripts/okf_validate.py` |
| Release | `okf--v0.10.3` |
| Commit | `a8b96420de90d102c43cda1693d01ec4f925f2ab` (2026-10-13) |
| SHA-256 of the file (LF line endings) | `d9ad6d4347233cd6402f0336b36c08d54662f2b05b1f46a206d28752bace58f0` |
| Licence | MIT, Marco Boffo: `LICENSE` in this folder |
| Notice | `NOTICE` in this folder: the OKF v0.2 specification text that the upstream repository vendors is Apache-2.0, Google LLC |
| Dependency | PyYAML (MIT), in the `validate` group of `pyproject.toml` |
| Vendored | 2026-10-31 |

## Changing the pin

1. Copy the new file from the new commit's blob (`git show <commit>:skills/validate/scripts/okf_validate.py`), and its `LICENSE` and `NOTICE`.
2. Update the table above, including the hash.
3. Run the message-mapping test (`tests/template/test_conformance.py`); a new or reworded message fails it until `okfprofile.checks.conformance` maps it.
4. Record the change in the decision record. A patch to the file is not allowed without an ADR amending AD-08.
