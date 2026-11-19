# Vendored: the OKF project's validator

`validate.py` is a verbatim copy of the OKF v0.3 conformance validator from the Open Knowledge Format project. It is not edited here (SDD AD-08 as amended by ADR-013); `okfprofile` runs it for check 1 and maps its finding codes (`okfprofile.checks.conformance.CODE_TABLE`). It replaces the okf-skills validator, which has no v0.3 release (RFC-002 D2).

| Item | Value |
| --- | --- |
| Source | https://github.com/open-knowledge-format/open-knowledge-format, path `skills/okf-generate/scripts/validate.py` |
| Commit | `527e81aff55992be21507e97004286789126f88c` (2026-11-18), the same commit as the pinned specification |
| SHA-256 of the file (LF line endings) | `7f92df7d6a2118a5b7e5c388aa97de48f6ad31b942abc9e2fc7d344830661f49` |
| Licence | Apache-2.0, Google LLC: `LICENSE.md` in this folder (the upstream repository's licence file) |
| Dependency | PyYAML (MIT), in the `validate` group of `pyproject.toml` |
| Vendored | 2026-11-19 |

## Changing the pin

1. Copy the new file from the new commit (`skills/okf-generate/scripts/validate.py`) and the repository's `LICENSE.md`.
2. Update the table above, including the hash, and `okf_spec_commit` in `profile/profile.yaml` if the specification moved with it.
3. Run `tests/template/test_conformance.py`: a code the vendored file can emit that `CODE_TABLE` does not list fails it until the table maps it.
4. Record the change in the decision record. A patch to the file is not allowed without an ADR amending AD-08.
