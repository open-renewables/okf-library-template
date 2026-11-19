# ADR-013: OKF v0.3 and the OKF project's validator

**Status:** Proposed (drafted 2026-11-19 in P4 PR V; decisions D1 to D7 accepted by the owner on 2026-11-19 in [RFC-002](../rfcs/RFC-002-okf-v0.3.md)). **Supersedes:** the okf-skills pin of DDR QA-25 and QA-44. **Amends:** SDD AD-08 (the checker), ADR-012 items 2 and 5 (`OKF121` now replaces `E004`, and the root index no longer counts). **RFC:** RFC-002. **Plan:** P4 step 4b, proposed entry PP-15.

## Context

The template pinned OKF v0.2 at commit `ad30107` in `GoogleCloudPlatform/open-knowledge-format`, checked by the okf-skills validator (AD-08). On 2026-11-18 that repository was marked deprecated and OKF v0.3 was published in `open-knowledge-format/open-knowledge-format`. okf-skills has no v0.3 release; its latest tag, `okf--v0.12.0`, still checks v0.2. The OKF project now ships its own validator, `skills/okf-generate/scripts/validate.py` (Apache-2.0, PyYAML only), which emits stable finding codes. RFC-002 compared moving before or after template `v1.0.0`; the owner chose to move within P4, before the `v0.9.0` release candidate, so the pilot tests the version `v1.0.0` ships.

## Decision

1. **Pin.** The profile declares `okf_version: "0.3"` and `okf_spec_commit: 527e81a` (D1).
2. **Checker.** Check 1 runs the OKF project's validator, vendored unmodified from `527e81aff55992be21507e97004286789126f88c` with its licence, and maps its findings **by code**, not message text (D2). `okfprofile.checks.conformance.CODE_TABLE` lists all 33 codes; a code it does not list maps to `OKF119`, and a test fails when the vendored file can emit such a code.
   - New codes: `OKF105` (error), a `log.md` that breaks §9; `OKF122` (warning), `superseded_by` without `status: deprecated`.
   - `OKF111` (legacy v0.1 constructs) is retired, because the v0.3 validator does not check them.
   - Dropped validator codes, because another check owns them: value shapes (check 2), timestamps (`OKF120`), body links and path fields (check 4), staleness (W-06).
3. **Folder-index headers (D3).** The validator reports a header on a folder index as an error, `E004`. A usable ADR-010 header is the template's recorded departure, so its `E004` errors are replaced by the one bundle-level `OKF121` warning. An unusable header is reported by check 5 (`OKF505`, `OKF506`). ADR-010 and ADR-012 stand.
4. **Root index metadata (D5).** v0.3 §8.1 lets the root index carry `okf_version`, `title`, `description`, `license` and extension keys, and requires a regenerating producer to keep them. The generator keeps every root key and rewrites only `okf_version`; `OKF506` checks only that `title` and `description` are one line and `license` is non-empty. `init_library.py` writes `title` from `library.title` and `license` from the content licence (`CC-BY-4.0` by default; `LicenseRef-proprietary` for a proprietary licence). The root is no longer part of `OKF121`.
5. **Timestamps (D4).** `OKF120` stays: every timestamp-valued key is a date-time with an explicit offset, although v0.3 also accepts a date.
6. **Path fields.** Check 4 resolves the v0.3 §6.2 path fields (`resource`, `superseded_by`, `computation`, `executor.resource`, `attester.resource`, `sources[].resource`) from the concept's own folder, or from the bundle root when they start with `/`. A field that resolves to nothing is `OKF412` (error). URIs and `sources` scope descriptors are not paths. Body links stay relative (ADR-005).
7. **`verified` currency.** A `verified[].at` written by the revision writer is never earlier than the concept's `generated.at`, because v0.3 §5.3 reads an older verification as not current.
8. **Unprefixed keys (D6).** `uid` and `namespace` keep their names. v0.3 §4.1 asks for `x-<producer>-<name>` extension keys (a SHOULD); this is a recorded departure, and check 1 drops the validator's `I203`.
9. **Citations.** v0.3 §5.1 attributes a claim with a footnote whose label is a `sources[].id`. The validator's `W108` (a footnote with no matching id) maps to the existing warning `OKF116`; the template's example concept and the `author-concept` skill follow the v0.3 form.

## Consequences

- The template's bundle is OKF v0.3 conformant except for folder-index headers where a library adds them (G42).
- The check 1 code table replaces 28 message-text rules; findings carry the validator's line numbers.
- Libraries made from an earlier template release that move to v0.3 take the change as a profile migration.
- The vendored validator has no release tag; it is pinned by commit like the specification, and re-pinning follows `scripts/vendor/okf/VENDORED.md`.
- The SRS wording (FR1.2, executive summary, Evidence, constraints, risks) is the owner's and is proposed in the P4 plan as PP-16, not applied here.
