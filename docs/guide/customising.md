# Customising the profile

Everything that makes this library different from another lives in `profile/` and `knowledge/vocab/`; the tooling in `scripts/` holds no domain rule. A change to `profile/` is a tooling change: it goes in its own pull request or commit, apart from concept changes, unless it carries the `profile-migration` label, and it is recorded in `DECISIONS.md`. A change that renames a declared heading or removes a field, value or type breaks existing concepts and is a major release.

Check every change with `uv run poe check` and `uv run poe test`; the library's own fixtures in `tests/library/` show what each rule accepts and rejects.

## Where things are declared

| To change | Edit |
| --- | --- |
| Concept types, `uid` prefixes, where each type may live | `types[]` in `profile/profile.yaml` (`name`, `uid_prefix`, `schema`, `paths`) |
| A type's frontmatter fields | `profile/types/<type>.schema.json` (JSON Schema 2020-12); each references `okf-base.schema.json`, which holds OKF's own keys |
| A type's body sections | `types[].body`: `sections[]` of `heading`, `required`, optional `format`, `managed_by: ci`; `order` is `strict` or `any`; `empty_placeholder` |
| The form of list items in a section | `profile/formats/<format>.md`: a pattern for each item's first line, allowed values, required sub-items |
| Tag namespaces | `vocabularies.namespaces[]` in the profile, plus one vocabulary concept per namespace in `knowledge/vocab/` |
| Tag values | The vocabulary concept: one bullet per value, `` - `value`: definition ``. Adding a value is a reviewed change |
| Rules that tie tags to folders | `path_rules[]`: `tag_equals_segment`, `tag_count`, `tag_required_if_segment_kind`, `tag_not_equal_segment` |
| Warnings | `warnings[]`: `tag_not_equal_segment`, `agent_label_missing`, `stable_section_nonempty`, `directory_size` |
| Status values beyond OKF's `draft`, `stable`, `deprecated` | `status.extensions[]` with their trust tier; a generic OKF reader treats an extension value as not current |
| Approval, provenance and staleness settings | `rules` (for example `require_non_author_approver` once a second directory owner joins, `write_okf_verified`, `stale_after_default`) |
| Index lines and folder size | `index` (`show_status`, `show_tier`, `max_concepts_per_directory`) |
| The site generator | `site.generator`, or `uv run poe site-switch <generator>` |

`profile/schemas/profile.schema.json` validates `profile.yaml` itself; an unknown key or a wrong value is reported when the profile loads.

## Adding a concept type

1. Add the type to `types[]` with a new `uid_prefix` (two to five capital letters, never reused) and its `paths`.
2. Write `profile/types/<type>.schema.json`, referencing `okf-base.schema.json`, with `type` as a `const` and `uid` matching the prefix.
3. Declare its body sections, and any formats they use.
4. Add a passing fixture and a failing one under `tests/library/fixtures/`.
5. `uv run python scripts/new_concept.py <Type> <path>` now creates it.

## Folder scope

A folder's `index.md` may hold a one-sentence `description` header, which the generator keeps and puts on the folder's line in the parent index; agents read it to choose a folder. The root index's header is the bundle's metadata: `okf_version`, `title`, `description`, `license` and any `x-` keys, all kept when the indexes are rebuilt. See [Maintaining a library](maintaining.md#writing-a-concept) for the warning this gives.

## Rename the primary type

The library starts with the template's primary type, `Item` with the prefix `ITM`. Rename it **before the first commit**: once `profile/uid-registry.yaml` is committed, validation against that commit reports every renamed `uid` as changed (`OKF606`) and every old registry entry as removed (`OKF607`). A `uid` is permanent once released, so a released prefix is never renamed.

1. Preview: `uv run python scripts/rename_type.py Item <NewType> <PREFIX> --dry-run`.
2. Rename: `uv run python scripts/rename_type.py Item <NewType> <PREFIX>`. It rewrites the type name and prefix in `profile/`, renames the schema file, rewrites the `type:` and `uid:` lines of the concepts and the registry, does the same in `tests/library/`, and rebuilds the indexes. Prose is not changed. It refuses, changing nothing, if a file is not UTF-8 text or the new schema file exists, and it warns when the registry is already committed.
3. Check with `uv run poe check` and `uv run poe test`, adjust the type's sections, formats and paths, and record the rename in `DECISIONS.md`.
