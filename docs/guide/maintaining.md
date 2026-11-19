# Maintaining a library

The rules are in [`GOVERNANCE.md`](../../GOVERNANCE.md); this page says how to carry them out. Commands are in [Reference](reference.md).

## Writing a concept

1. Create it: `uv run python scripts/new_concept.py <Type> <path> --title "<title>" --description "<one sentence>"`. It writes the frontmatter with the next `uid`, the tags its path implies and every declared section with its placeholder, and registers the `uid`. A key the type's schema declares can be set at once with `--set key=value`, for example a vocabulary's `--set namespace=<name>`.
2. Fill the declared sections in their order and formats, in your own words. Keep the placeholder in a section that has nothing yet.
3. Cite each source as a `sources` entry with an `id`, and attribute each claim with a footnote whose label is that id (OKF v0.3 section 5.1):

   ```markdown
   ---
   sources:
     - id: iec-61215
       resource: https://webstore.iec.ch/publication/61215
   ---

   Modules are tested for thermal cycling.[^iec-61215]

   [^iec-61215]: IEC 61215-2:2021, test MQT 11.
   ```

4. Start every list after a blank line and put no list inside a footnote definition; the site renders those two cases differently from the validator.
5. Leave `status: draft`. Only a directory owner makes a concept `stable`, and a `stable` concept cites a source.
6. Run `uv run python scripts/build_indexes.py` and `uv run poe check`.

Never edit by hand an index body, `profile/uid-registry.yaml` or a *Revision history* section; validation rejects it. Never delete a concept: set `status: deprecated`, and point to its replacement with `superseded_by` (a path such as `/group/category/new-concept.md`).

A folder's `index.md` may open with a one-sentence scope, which the generator keeps and shows on the parent's line:

```markdown
---
description: "Risks to module performance and safety in manufacture and operation."
---
```

OKF v0.3 gives a folder index no frontmatter, so validation reports these headers once per bundle as the warning `OKF121`; leave them out if the bundle must be strictly conformant.

## Review, approval and trust tiers

A change gets one revision line per concept it touched, recording the author, the approval and its labels. The trust tier shown on every index line comes from those lines:

| Tier | When |
| --- | --- |
| Unverified | No revision line yet |
| Machine-confirmed | Any revision since the last full review was agent-drafted, approved by someone who does not own the folder, approved on an earlier commit than the one merged, or merged without approval |
| Human-reviewed | Every revision since the last full review was approved by a directory owner |
| `human-reviewed (self)` | As Human-reviewed, but the approval was the owner's own (a single maintainer merging their own change) |

A one-line owner-approved fix to an agent-drafted concept leaves it Machine-confirmed. To raise it, the owner reviews the whole concept and marks the change as a full review.

<!-- platform:github:start -->
On GitHub: label a pull request `agent-drafted` when an agent wrote any of it and `full-review` when the owner reviewed each changed concept in full. GitHub does not let an author approve their own pull request, so a single maintainer merges with the admin bypass and the line says `self-approved`. Directory owners are the code owners in `.github/CODEOWNERS`, per folder.
<!-- platform:github:end -->
<!-- platform:git-local:start -->
With `git-local`: mark the same facts as commit trailers (`Agent-Drafted: yes`, `Full-Review: yes`, `Approved-by: Name <email>`). An approval counts as someone else's only when the `Approved-by` address belongs to another entry in `maintainers` in `profile/profile.yaml`.
<!-- platform:git-local:end -->

## Revision history

<!-- platform:github:start -->
After each merge to `main`, `revision.yml` appends the lines and rebuilds the affected indexes in one commit. Each run records every change since the last revision commit, so a cancelled or failed run is caught up by the next. If lines go missing or the bot cannot push, follow [Recover the revision writer](runbooks.md#recover-the-revision-history).
<!-- platform:github:end -->
<!-- platform:git-local:start -->
After each merge to `main`, run `uv run poe revision`. It records every commit since the last revision commit and commits the result with the trailer `Revision-Bot: true`.
<!-- platform:git-local:end -->

## Releases

A release is a semantic-version tag with an archive of the bundle, its checksum and a manifest; agents cite concepts as `<uid>@<tag>`. Minor versions add or revise concepts; a change that breaks the profile, such as renaming a declared heading, is a major version. A release fails while any merged change lacks its revision line.

<!-- platform:github:start -->
Push an annotated tag `vX.Y.Z` on `main`. `release.yml` checks the revision lines, validates, builds the archive, rebuilds it from the tag to compare digests, and publishes a GitHub Release; versions below `1.0.0` are marked pre-release.
<!-- platform:github:end -->
<!-- platform:git-local:start -->
Run `uv run poe release vX.Y.Z`. It checks the revision lines, validates, builds the archive into `dist/` and makes an annotated tag whose message records the archive's digest. Keep the archive; `dist/` is not committed.
<!-- platform:git-local:end -->

To check an archive: `sha256sum -c <archive>.sha256`. The `RELEASE` file inside it names the tag and commit.

## The site

The site is built from the bundle in place with the profile's generator (`site.generator`, MkDocs or Zensical): `uv sync --group site-<generator>`, then `uv run poe docs` to serve it or `uv run poe docs-build` for the strict build. `uv run poe site-switch <generator>` changes the generator after a test build. No public site is published before the library's `v1.0.0`; a library may have none.

## Staleness and dependencies

A concept is due for review at the earlier of its `stale_after` time and two years after its last revision (`stale_after_default` in the profile). `uv run poe stale` lists them, and `uv run poe audit` checks the locked dependencies for known vulnerabilities; record a reviewed advisory in `profile/audit-ignore.txt` to accept it.

<!-- platform:github:start -->
`stale-report.yml` runs both every week and keeps one tracking issue. Dependabot proposes dependency updates; when it changes only `requirements/*.txt`, replace its pull request with `uv lock --upgrade-package <name>` and `uv run poe export`, so the lock and the exports stay together.
<!-- platform:github:end -->

## Going public, moving, and leaks

- [Promote a library to public](runbooks.md#promote-a-library-to-public): ruleset, revision App, secret scanning, Pages.
- [Move a git-local library to a platform](runbooks.md#move-a-git-local-library-to-github): history, revision lines and release digests unchanged.
- [Remove leaked content](runbooks.md#remove-leaked-content): what to rewrite, what to rotate, what cannot be undone.

## Taking a later template version

A library may diverge from the template and need not take its updates. A library created by clone can merge a later template tag: `git remote add template <template repository>`, `git fetch template --tags`, `git merge <tag>`, resolve the files you changed, then `uv run poe check` and `uv run poe test`. Record it in `DECISIONS.md`.
