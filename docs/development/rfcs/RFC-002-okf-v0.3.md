Status: Accepted (owner, 2026-11-19, in Q&A; option (b), see "Decision" at the end)

ADRs produced: ADR-013 (OKF v0.3 and the OKF project's validator), to be written with the change. ADR-012 stays the index-header ADR ([ADR-012](../adr/ADR-012-index-headers-and-okf-conformance.md), merged in #49); the generator ADR that the P4 plan names for PR 6 takes the next free number (D7).

# RFC-002: Moving from OKF v0.2 to OKF v0.3

## Problem

The template pins OKF v0.2 at commit `ad30107` of `GoogleCloudPlatform/open-knowledge-format` (`profile/profile.yaml`, SRS FR1.2 and Evidence, SDD AD-08 and §3). On 2026-11-18 that repository was marked deprecated (commit `8a8ff87`, a README banner pointing to the new home), and OKF v0.3 is the current specification at `open-knowledge-format/open-knowledge-format`. The template is in P4 and heading for `v1.0.0`. The owner needs to decide whether to move before or after `v1.0.0`.

[ADR-012](../adr/ADR-012-index-headers-and-okf-conformance.md) (merged to `main` in #49, `a699ccf`) already records one v0.3 consequence: a folder-index header breaks §8 in both versions, and a root `description` is allowed from v0.3.

This RFC proposes no change. It does not alter a requirement, decision, profile, schema or script.

## Sources

| Source | Location | Read |
| --- | --- | --- |
| OKF v0.2 | `GoogleCloudPlatform/open-knowledge-format`, `SPEC.md` at `ad30107c31c06aec8a7d5636e0d1058118604e6f` (2026-08-21); repository head `8a8ff87` (deprecation notice, 2026-11-18) | git clone, 2026-11-19 |
| OKF v0.3 | `open-knowledge-format/open-knowledge-format`, `SPEC.md` at `main` = `527e81aff55992be21507e97004286789126f88c` (2026-11-18). The repository has no tags | git clone, 2026-11-19 |
| v0.3 reference validator | same repository, `skills/okf-generate/scripts/validate.py` at `527e81a` (Apache-2.0, Google LLC; only dependency PyYAML) | git clone, 2026-11-19, read only |
| okf-skills | `scaccogatto/okf-skills`, tags `okf--v0.10.3` (`a8b96420`), `okf--v0.11.0`, `okf--v0.12.0` (`49f8fb4`), `main` (`c6591ec`, 2026-11-04), `CHANGELOG.md` | git clone, 2026-11-19, read only |

v0.3 §13 lists its own changes from v0.2. The table below is checked against the text of both versions, not only against §13. Neither validator was run here: the session was not permitted to run downloaded code. Statements about what they report come from reading their source.

## 1. Section-by-section differences and what they touch

"No effect" means the template already meets v0.3 or does not use the feature.

| § | v0.2 at `ad30107` | v0.3 at `527e81a` | Touches in the template |
| --- | --- | --- | --- |
| 2 | No defined terms for bundle root, producer, consumer, asset, path field | Defines them; only the directory tree gives parent and child, and links are untyped (wording fix) | No effect. The SDD already treats links as untyped (SRS trade-offs, "Relationship typing") |
| 3.1, 3.2 | "All other `.md` files are concept documents" | New §3.2: a `.md` file with no frontmatter or no `type` is **not a concept** and does not affect conformance (validators SHOULD warn); non-`.md` files are assets; dot-paths are outside the bundle; symlinks out of the root are not followed | No change needed. The template's own rule is stricter (SDD §6: everything under `knowledge/` is a concept or an index), and check 2 still requires `type`. The `OKF101` and `OKF104` mapping changes, because v0.3 makes a missing `type` a warning (`W120`), not a conformance error (see §2 below) |
| 4 | Delimiters; YAML not further specified | Frontmatter MUST be a YAML 1.2 core-schema mapping; no duplicate keys; quote number-like values; no custom tags; do not re-serialise unchanged values | No change needed: `okfprofile` already reads YAML 1.2 with ruamel.yaml and writes by text (AD-05). One check to add as a fixture: a duplicate key is reported (ruamel rejects duplicates by default; not tested here) |
| 4.1 | Extensions: "SHOULD preserve unknown keys"; `title` etc. "Recommended" | Extension keys allowed at every level, including inside `sources`, `generated`, `verified`; a modifying producer **MUST keep** unknown keys; future versions will not define `x-` keys, and producers SHOULD name their own `x-<producer>-<name>`; `title`, `description`, `resource`, `tags` become "Optional" | **`profile/types/okf-base.schema.json`**: nested mappings already accept extra keys (no `additionalProperties: false` inside them), so no schema change. **`uid` and `namespace`** are profile keys without `x-`: a SHOULD, not a MUST. Renaming them would be a breaking profile change for no consumer benefit; the proposal keeps them and records the departure. The v0.3 reference validator reports them as info `I203` on every concept, which check 1 should drop. The revision writer already edits by text and keeps unknown keys |
| 4.2 | Body sections conventional | Body dialect stated: CommonMark with GFM tables and `[^label]` footnotes; producers SHOULD NOT depend on other extensions. "Do not use a list of citations in the body" | No change. I-01 and AD-06 already parse CommonMark with footnotes and tables. FR3.10 allows an external link as the citation of a `stable` concept; that is a link, not a citations list, so it stays valid |
| 5 (timestamps) | Every timestamp key is an ISO 8601 datetime with an explicit UTC offset (added 2026-08-21, okf#24) | Lists the six timestamp keys; accepts **two RFC 3339 forms**: date-time with offset, or date only (start of that UTC day). Consumers accept quoted and YAML-native values. Producers SHOULD use date-time for `generated.at` and `verified[].at`. A date-time without an offset stays invalid | **Timestamps:** the template's `OKF120` (`conformance.py`) and the `datetime` definition in `okf-base.schema.json` reject date-only values. That is stricter than v0.3 but still produces conformant bundles, so no change is required. Decision for the owner (D4): keep the stricter rule (recommended: one form, and the revision writer and `stale_after` comparisons stay simple), or accept date-only for `stale_after`, `sources[].last_modified` and `usage_window` |
| 5.1 | `sources[].author` not defined | `author` uses the actor convention (§7) | No effect: the base schema already types `author` as an actor |
| 5.2 | `verified` "is independent of `generated.at`" | `generated.at` is the last meaningful change; `verified` events need both `by` and `at`, else ignored | No effect on the schema (both already required in `verification`) |
| 5.3 | Tier from any `verified` entry | **Breaking.** Only **current** events count: an event is current when its `at` is at or after `generated.at`, or `generated` is absent | **SDD I-08 `verified` mapping** (`rules.write_okf_verified`, `revision_writer.set_verified`): the writer stamps `at` with the merge datetime and never writes `generated`, so its entries are current. A concept whose author wrote `generated.at` later than an approval would now read lower in a generic tool than in the library. The library's own tier rule (lowest since the last `full-review`) already has the same intent. Proposed: I-08 states that a written `at` is never earlier than `generated.at`, with a golden-file case; V-11 is re-read against §5.3 |
| 5.4 | `status`: draft, stable, deprecated; absent ⇒ stable | Adds `superseded_by` (one path field, meaningful only with `deprecated`); an **unknown `status` is not `stable`** and is excluded from current knowledge; informative guidance to keep a deprecated stub at a moved concept's old path | **`okf-base.schema.json`**: add `superseded_by` (string). **FR3.9 status extensions:** a profile-declared extension such as `reviewed` is read by every generic v0.3 consumer as not current; the SDD I-02 `status.extensions` row should say so. **Moves:** the template moves a concept with the `approved-move` label and `moved_from` in the registry (FR1.5), and keeps no stub; v0.3's stub guidance is informative, so no change, but check 4 could check that `superseded_by` resolves (additive) |
| 5.5 | `stale_after` absolute instant | Adds: stale means "check again"; omit when unknown; empty means absent; an unparsable value is never fresh | No effect: `stale_report.py` and FR3.11 already treat `stale_after` this way, and the schema rejects an unparsable value |
| 6, 6.1 | Links: `/`-rooted form **recommended**, relative supported | One resolution rule for links and path fields: a URI scheme is external, a leading `/` is from the bundle root, anything else is from the file's directory. Both in-bundle forms are valid, neither recommended. Values outside the root are external; targets are percent-encoded URI references; paths are case-sensitive | No change. ADR-005 already allows relative links only and I-01 requires `%20` or angle brackets for spaces. v0.3 removes the recommendation that ADR-005 departed from |
| 6.2 | Path fields accept an absolute URL, a `/` path or a relative path, without saying relative to what | **Breaking.** A path field without a leading `/` resolves from **the directory of its file**. Fallback (§6.2, §12.1): a consumer MAY try the bundle root when the bundle declares v0.2 or no version. `superseded_by` joins the list | **Path-field resolution:** the template's example concepts carry no path fields, and check 4 resolves body links only. A library that writes `resource: references/x.md` meaning "from the root" would silently point elsewhere under v0.3, and the reference validator warns `W119` when only the v0.2 fallback resolves it. Proposed: check 4 resolves path fields by the v0.3 rule (`resource`, `sources[].resource` when it looks like a path, `superseded_by`), with the author guidance to write `/`-rooted path fields, as v0.3's examples do. ADR-005 is about links and does not forbid `/` in path fields; the SDD should say so |
| 6.4 | — | Bundle graph: links and path fields that resolve to a concept are edges | No effect |
| 7 | `<producer>/<version>`, `human:`, `process:` | General `<scheme>:<id>`; adds `team:`; unknown schemes are non-human; `team:` gives machine-confirmed | No effect: the base schema's `actor` is any non-empty string, and I-08 writes `human:` and `process:` only. `OKF113` mapping changes (reference validator `W103`) |
| 8 | **Index files contain no frontmatter**, except a root `okf_version` | A subdirectory index **has no frontmatter**. A root index MAY have frontmatter (§8.1) | **ADR-012** unchanged for folder headers: still non-conformant under v0.3, and the reference validator makes it an **error** (`E004`), where okf-skills warned (see §2) |
| 8.1 | — | Root index MAY carry `okf_version`, `title`, `description`, `license` (SPDX expression or a path to a licence file in the bundle) and extension keys. A producer that regenerates `index.md` **MUST keep** the root frontmatter. Producers SHOULD put a root `index.md` with `okf_version` in each bundle | **Root index header** (`scripts/okfprofile/indexes.py` since #49: `ROOT_KEYS` is `okf_version` and `description`, and the generator writes `okf_version` from the profile). Needed: keep **every** root key, including unknown and `x-` keys; ADR-012's `OKF506` must then stop rejecting `title`, `license` and extension keys on the root; the root `description` drops out of `OKF121` (ADR-012 item 5). `init_library.py` writes `title` from `library.title` and `license` from the content licence (`CC-BY-4.0` by default), so the archive (I-12) says its licence in OKF terms (D5). `okf_version` becomes `"0.3"` |
| 9 | `log.md` format; frontmatter not addressed | `log.md` has no frontmatter | No effect: the template does not use `log.md` (SRS, Design overview) |
| 10 | `parameters` entries `{ name, type, required }`, all listed | `name` and `type` REQUIRED, `required` optional (default `false`); common parameter types listed; locator rule for the inline computation; consumers MUST NOT show a value as attested without `runtime` and `attester`; attester verdict has `ok` and optional `reason` | **`okf-base.schema.json`**: `parameters.items.required` becomes `["name", "type"]` (today it also requires `required`, which v0.3 makes optional). No template type uses Attested Computation |
| 11 | Conformance: (1) every non-reserved `.md` has parseable frontmatter, (2) with a non-empty `type`, (3) reserved files follow §8 and §9 | **11.1:** (1) every frontmatter block parses as a YAML mapping, (2) reserved files follow §8 and §9. A `.md` without frontmatter or `type` does not make the bundle non-conformant. **11.2:** consumer rules (resolve both link forms; never read outside the root; null, empty and absent are the same; one item may stand for a list; ignore family entries missing a REQUIRED key; keep out-of-vocabulary values) | **Conformance (check 1):** the profile validator stays the authority (SRS constraints), and check 2 keeps requiring `type`. The `OKF1xx` mapping is rebuilt (see §2). A folder-index header is a §11.1 item 2 failure in both versions |
| 12 | Minor bump = backward-compatible | **Before 1.0 a minor version MAY break**, with each breaking change listed and a fallback; after release, normative text changes only with a new version. §12.1 v0.2 fallbacks | **`okf_version` and `okf_spec_commit`** in `profile/profile.yaml`: `"0.3"` and `527e81a`. The new repository has no tags, so the pin stays a commit. The §12 rule that a released version's text does not change makes the commit pin safe. Also the profile meta-schema accepts both values already (`^[0-9]+\.[0-9]+$`, a 7–40 hex commit) |
| 13, App. B | Changes from v0.1 | Changes from v0.2 (§13); v0.1 to v0.2 moved to Appendix B | Reference only |

What does not change: `type` is still the only required key; `index.md` and `log.md` are still reserved; `description` still feeds index lines; trust tiers are still keyed on `human:`; `stale_after` is still an absolute instant.

## 2. The checker

**okf-skills has no v0.3 release.** The latest tag is `okf--v0.12.0` (`49f8fb4`, changelog date 2026-10-19), and `main` at `c6591ec` (2026-11-04) is the same validator. Both still say `OKF_VERSION = "0.2"` and "Deterministic conformance checker for Open Knowledge Format (OKF) v0.2". The validator file is byte-identical from `okf--v0.10.3` to `okf--v0.11.0`; `okf--v0.12.0` changes one rule only (the root index may also carry `recursive`). Re-pinning okf-skills today gains nothing for v0.3.

**The OKF project now ships its own validator.** `skills/okf-generate/scripts/validate.py` in the new repository (605 lines, Apache-2.0, PyYAML only, added 2026-10-27) checks v0.3 and, unlike okf-skills (V-08), emits **stable codes**: errors `E002`, `E004` to `E007`; 24 warnings `W101` to `W126`; info `I201`, `I203` to `I205`, with line numbers, `--json` and `--strict`. Its errors are exactly §11.1 failures.

Checker options:

| | Checker for v0.3 | Licence | Mapping | Risk |
| --- | --- | --- | --- | --- |
| K1 | Official `validate.py` at `527e81a`, vendored with `LICENSE.md` and a `NOTICE` entry | Apache-2.0, same as the template | By **code**, not by message text: a table `E004 → OKF117`, `W119 → OKF118`, … | New script, one month old, no release tag; pinned by commit like the spec |
| K2 | Wait for okf-skills v0.3 | MIT | By message text, as today | No date; one maintainer (96 of 100 commits); blocks the move |
| K3 | okf-skills v0.12.0 against a v0.3 bundle | MIT | As today | Warns on a root `title`, `description`, `license` and on `okf_version: "0.3"` (`§12`), so it reports v0.3 bundles as departures; not a v0.3 checker |

Recommendation: **K1.** It amends AD-08 (checker changes from okf-skills to the OKF project's validator), so it needs its own ADR, which can be the same ADR as the version move.

**What re-pinning means for `scripts/okfprofile/checks/conformance.py`:**

- `VENDORED` points at `scripts/vendor/okf/validate.py` (or the folder keeps its name and `VENDORED.md` records the new source). `load_vendored` calls its `Validator` class instead of `validate()`; the report shape changes from `errors` and `warnings` string lists to records with level, code, file and line.
- `MESSAGE_RULES` (28 text rules) is replaced by a code table over 33 codes. Most map one to one onto the existing `OKF1xx` codes; the drops stay the same in kind (checks 2 and 4 own schema shape and links). New drops: `I203` (extension keys without `x-`, which `uid`, `namespace` and the profile's own fields trigger on every concept), `W120` for files the template's check 2 already reports, and the `W115` broken-link warning, which check 4 owns.
- `OKF104` (missing `type`) and `OKF101` (no frontmatter) stop coming from the checker, because v0.3 makes them warnings (`W120`); the reader and check 2 already report both, so the codes stay and their source note changes.
- Findings now carry the checker's line numbers instead of `0`.
- `OKF120` stays as the profile's stricter rule (D4).
- `tests/template/test_conformance.py` (21 `OKF1` references today) is rewritten around the code table; the message-mapping test becomes a code-coverage test that fails when the vendored file emits a code the table does not know.

**What it means for ADR-012's `OKF121`:** in `conformance.py` on `main` (since #49), `_index_header_findings` collects okf-skills' per-index `OKF117` warnings whose text is `"§8 index.md should contain no frontmatter"` or `"§12 root index.md frontmatter may only carry"`, and replaces them with one `OKF121` warning. Under K1:

- **Folder headers:** the reference validator reports each as an **error**, `E004` ("an index.md below the bundle root has no frontmatter (section 8)"). `OKF121` must collect `E004` instead of the two message texts, and the template must decide that a usable ADR-010 header is downgraded to the one `OKF121` warning, not left as an error (D3). Without that decision, every library using ADR-010 headers would fail check 1.
- **Root header:** no finding any more for `description`, `title`, `license` or extension keys, so the root drops out of `OKF121`, as ADR-012 item 5 expects. `OKF506` must then allow those root keys, because §8.1 requires a regenerating producer to keep them.
- The `OKF121` message changes from "allows only as `okf_version` on the root index (§8, §12)" to "a subdirectory index has no frontmatter (§8, §11.1)".

## 3. Options

Effort is stated as the P4 plan states it: agent hours, owner hours, calendar days **[Inf]**. The work list common to (b), and to (a) later, is:

1. Vendor the K1 checker and rebuild the check 1 code table and its tests (4–6 agent hours).
2. `profile.yaml` pin; `okf-base.schema.json` (`superseded_by`, `parameters.required`); profile meta-schema unchanged (1 agent hour).
3. Root index header: keep all root keys, relax `OKF506`, update `OKF121` to `E004`; `title` and `license` from `init_library.py`, with a W-10 self-test assertion (2–3 agent hours).
4. Check 4 path-field resolution by §6.2, with fixtures (2–3 agent hours).
5. I-08 `verified` currency rule and a golden case (1 agent hour).
6. Documents: SRS proposals, SDD, ADR, DDR change log, `AGENTS.md`, `README.md`, the two skills, `VENDORED.md`, `NOTICE`, finding-code catalogue, known gaps (3–4 agent hours).

Total 13–18 agent hours for the change itself.

| | (a) Stay on v0.2 for `v1.0.0`, move afterwards | (b) Move before `v1.0.0`, within P4 | (c) Support both, keyed on `okf_version` |
| --- | --- | --- | --- |
| Now | Record a known gap and an SRS Evidence note that the pinned repository is deprecated: 0.5 agent hours, 0.5 owner hours, same day | Work list above: 13–18 agent hours, 2–3 owner hours (D1 to D4, SRS wording, PR review), 2–3 calendar days | Two vendored checkers, two code tables, two base schemas or a conditional one, fixtures for both, index-header rules for both: 22–32 agent hours, 4–5 owner hours, 4–6 days |
| Later | The same work list after `v1.0.0` (13–18 agent hours), plus porting to each library already made (pilot, then the RE library) and a profile-migration release in each (1–2 agent hours and 0.5 owner hours per library); 3–4 days in all | None | Double maintenance on every check 1 change until v0.2 is dropped |
| Template `v1.0.0` | Ships citing a deprecated repository and a superseded spec; release notes must say so | Ships on the current spec; the pilot exercises it | Ships on both |
| Pilot | Built and timed on v0.2, so the pilot evidence (FR6.1, FR7.2) is for the version the template then leaves | Built on v0.3 if the move lands before the pilot is instantiated from the `v0.9.0` release candidate | Tested on one version only unless the pilot is run twice |
| Risk | Low now; the move later is a breaking profile change for each library | v0.3 is one day old and its validator one month old; errata would come as v0.4, not as silent changes (§12) | Most code, least benefit: a library pins its own `okf_version` at instantiation and diverges anyway (FR6.4), so it never needs both |
| P4 schedule | No change | Adds 2–3 days before the `v0.9.0` release candidate; the P4 estimate (26–37 agent hours) rises to about 39–55 | Adds 4–6 days |

**Recommendation: (b), landing before the `v0.9.0` release candidate and the pilot.** The two breaking changes in v0.3 barely touch the template: links are already relative-only (ADR-005), and the I-08 `verified` mapping already writes current events. Most of the work is the checker, which is needed whenever the move happens, and moving first means the pilot, the second-person timing and the traced agent run all test the version `v1.0.0` ships. A `v1.0.0` that cites a deprecated repository would need the same work as a breaking change in every library made from it. (a) is the fallback if the owner wants no change to the P4 scope; (c) is not recommended.

## 4. Proposed document edits (not applied)

### Under (b)

**New ADR-013, "OKF v0.3 and the OKF project's validator"** (D7), linked both ways with this RFC. Decision: the profile pins OKF v0.3 at `527e81a`; check 1 uses the OKF project's `validate.py` at the same commit, mapped by code (amends AD-08, supersedes the okf-skills pin of QA-25 and QA-44); `OKF120` keeps the offset rule (D4); `init_library.py` writes `title` and `license` into the root index header (D5); ADR-010 folder headers stay a departure, reported as one `OKF121` warning that replaces the checker's `E004` errors (amends ADR-012 items 2 and 5); `uid` and `namespace` stay unprefixed (§4.1 SHOULD).

**SRS** (owner's wording; proposed text only):

- Executive summary, first paragraph: "adopt the existing Open Knowledge Format (OKF) v0.3"; add one sentence: "v0.2, released by Google Cloud on 12 June 2026, was superseded by v0.3 on 18 November 2026, when the specification moved to the `open-knowledge-format` organisation."
- Evidence, "The OKF specification": link `open-knowledge-format/open-knowledge-format`; "The specification has no release tags, so it is pinned by commit (`527e81a`)"; note that `GoogleCloudPlatform/open-knowledge-format` is deprecated and frozen at `8a8ff87`. Bullets: minimal conformance per v0.3 §11.1 (frontmatter parses as a mapping; reserved files follow §8 and §9); timestamps per v0.3 §5 (date-time with offset or date only); trust tier from current events only (§5.3); a root index may carry bundle metadata (§8.1). Add the OKF project's validator to the "Templates and tooling" table. Sources: add v0.3 `SPEC.md` at `527e81a`, accessed 19 November 2026.
- FR1.2: "The bundle conforms to OKF v0.3 at the pinned specification commit. The profile also requires frontmatter on the first line of every concept and timestamp-valued keys as ISO 8601 datetimes with an explicit offset." Acceptance criterion unchanged.
- FR2.2 check 1: "OKF conformance with a pinned external checker, plus the profile's frontmatter-first and datetime-offset rules" (unchanged in substance).
- Constraints, last bullet: "OKF is pre-1.0 and a minor version may break (v0.3 §12); the profile pins a version and commit, tracks minor versions by a profile-migration release, and the profile validator, not the external checker, is the authority."
- Risks table, OKF row: "Pin `okf_version`, the specification commit and the checker commit".
- FR4.3 is unaffected beyond the ADR-010 wording already proposed in the P4 plan.

**SDD:**

- §1 summary and item 1: "OKF v0.3 bundle"; "the pinned OKF checker (the OKF project's validator)".
- §3 drivers: "OKF v0.3 is pre-1.0 | Spec pinned by commit (`527e81a`)"; the timestamp bullet restated as v0.3 §5 with the profile's stricter rule.
- AD-08: new checker, commit, Apache-2.0, mapping by code; status "Accepted (DR-21; amended by QA-44, ADR-013)".
- C-03 `checks`: "check 1 calls the vendored OKF validator"; C-03 note on dependencies unchanged (PyYAML).
- I-01: timestamps sentence; add "path fields without a leading `/` resolve from the file's directory (v0.3 §6.2); write them `/`-rooted".
- I-02: `okf_version` `"0.3"`, `okf_spec_commit` `527e81a`; `status.extensions` row: "a generic v0.3 consumer reads an extension value as not current (§5.4)".
- I-03: base schema adds `superseded_by`; `parameters` entries require `name` and `type`.
- I-07: root index carries `okf_version: "0.3"` and may carry `title`, `description`, `license` and extension keys, all kept on regeneration; folder headers per ADR-010 and ADR-013.
- I-08: "a written `verified[].at` is never earlier than the concept's `generated.at` (v0.3 §5.3)".
- I-09: `OKF1xx` row: "OKF validator findings mapped by code; frontmatter-first; datetime offsets".
- I-12: archive `RELEASE` and manifest record OKF version and spec commit (already); no change.
- §15: V-08 re-answered for the new checker; V-11 re-read against v0.3 §5.3 (current events).
- Sources: v0.3 `SPEC.md` and `validate.py` at `527e81a`, accessed 19 November 2026.

**DDR:** the QA and DR series are frozen (QA-68), so no new row. One change-log row: date of acceptance; documents "SRS; SDD; ADR-013; `profile/`; `scripts/okfprofile/checks/conformance.py`; `scripts/vendor/`"; change "OKF v0.3 adopted at `527e81a`; checker changed to the OKF project's validator; root bundle metadata kept"; decisions "ADR-013, AD-08, QA-25, QA-44, ADR-012". The "Current position" table's Validation row gains "check 1 by the OKF project's validator (ADR-013)".

**Also:** `AGENTS.md` and `README.md` say v0.3; `scripts/vendor/` `VENDORED.md`, `LICENSE`, `NOTICE`; `docs/development/constraints.md` pinned versions table if it lists the checker; the finding-code catalogue; a profile-migration label on the pull request that changes `profile.yaml` together with any `knowledge/` index regeneration (AD-18).

### Under (a)

- Known gap: "OKF v0.2 pin is a deprecated repository; move to v0.3 after `v1.0.0` (RFC-002)".
- SRS Evidence (owner's wording): one sentence that the pinned repository was deprecated on 18 November 2026 and v0.3 published; FR1.2 unchanged.
- SDD §3: the same note on the OKF row. ADR-012 item 5 stands. `v1.0.0` release notes name the v0.2 pin and this RFC.
- After `v1.0.0`: all of the (b) edits, plus a template release note telling libraries the move is a profile-migration (major) release for them.

### Under (c)

All of the (b) edits, plus: I-02 `okf_version` is an enum `"0.2" | "0.3"` and `okf_spec_commit` is chosen from it; AD-08 lists two checker pins; C-03 `checks` selects the checker by `okf_version`; I-09 `OKF1xx` has two code tables; SRS FR1.2 names both versions; W-10 instantiates once per version.

## Decision (owner, 2026-11-19)

The owner settled the seven decisions in Q&A on 2026-11-19 and took the recommendation in each case.

| # | Decision | Recommended | Owner's decision |
| --- | --- | --- | --- |
| D1 | When to move: (a) after `v1.0.0`, (b) within P4 before the `v0.9.0` release candidate, or (c) support both | (b) | **(b)**: move within P4, before the `v0.9.0` release candidate, so the pilot tests v0.3 |
| D2 | Which checker for v0.3: K1 the OKF project's `validate.py` at `527e81a` (Apache-2.0), K2 wait for okf-skills, K3 keep okf-skills v0.12.0 | K1 | **K1**: vendor the OKF project's validator at `527e81a`, mapped by code; amends AD-08 |
| D3 | Under v0.3 a folder-index header is an `E004` error in the reference validator. Downgrade usable ADR-010 headers to the single `OKF121` warning (as ADR-012 does today), or treat them as errors, or drop folder headers | Downgrade to `OKF121`; ADR-012 decision unchanged | **Downgrade**: usable headers give one `OKF121` warning that replaces the `E004` errors; ADR-010 and ADR-012 stand |
| D4 | Timestamps: keep `OKF120` (offset required everywhere), or accept v0.3's date-only form for some keys | Keep `OKF120` | **Keep `OKF120`** |
| D5 | Root bundle metadata: should `init_library.py` write `title` and `license` into the root index header | Yes | **Write both**: `title` from `library.title`, `license` from the content licence (`CC-BY-4.0` by default) |
| D6 | `uid` and `namespace` stay unprefixed (v0.3 §4.1 asks for `x-<producer>-<name>` as a SHOULD) | Keep; record in the ADR | **Keep unprefixed**; the ADR records the departure and check 1 drops `I203` |
| D7 | The ADR number: the P4 plan already names an "ADR-012 default generator" for PR 6 while the index-header ADR, merged in #49, is ADR-012 | Keep ADR-012 for the index header | **ADR-012** stays the index-header ADR; **ADR-013** is this move; the PR 6 generator ADR takes the next free number, and the P4 plan is corrected to say so |

Consequences for the work:

- The (b) work list in §3 and the (b) edits in §4 apply. They are applied with the change, not in this RFC. The SRS wording is still the owner's (FR1.2, Evidence, constraints, risks).
- The P4 plan gains a step before the `v0.9.0` release candidate: the v0.3 move (13–18 agent hours, 2–3 owner hours, 2–3 days), which raises the P4 estimate to about 39–55 agent hours. The step builds on #49 (merged), because it changes the same `conformance.py` code (`OKF121`) and `OKF506`.
- The pull request that changes `profile.yaml` and regenerates `knowledge/index.md` carries the `profile-migration` label (AD-18) and a decision-record entry; for the template it is a pre-1.0 release, so the major-version rule does not yet bite.
