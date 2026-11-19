# Reference

## Commands

Run as `uv run poe <task>`; `uv run poe` lists them all.

| Task | Does |
| --- | --- |
| `install` | Install every dependency group and the pre-commit hooks |
| `check` | Lock check, lint, types, validation, index freshness, skill checks |
| `test` | The tests, with coverage where the template's tests are kept |
| `ci-validate` | Validate the working tree against a base branch with the base branch's own tooling (`base=origin/main` by default) |
| `scan` | Scan changed files for confidentiality markers and secret-shaped strings (`--all` for every tracked file) |
| `audit` | Check the locked dependencies for known vulnerabilities (needs network) |
| `stale` | List concepts past their review date (`--check-since <tag>` lists changes with no revision line) |
| `rename-type` | Rename a concept type and its `uid` prefix, before the first commit |
| `renumber` | Give a concept whose `uid` clashes with another the next free number |
| `docs`, `docs-build` | Serve the site, or build it strictly, with the profile's generator |
| `docs-alt`, `docs-linkcheck` | Build with the other generator and compare pages; check a built site's links with lychee |
| `site-generator`, `site-switch` | Print the site generator; switch it after a test build |
| `bundle`, `bundle-verify` | Build the release archive into `dist/`; check it against its manifest |
| `link-skills` | Optional: copy the agent skills into `.claude/skills/` in your own checkout |

<!-- platform:github:start -->
On GitHub, `setup-repo` configures the repository (labels, merge methods, permissions, ruleset; `--dry-run`, `--check`, `--promote`); CI runs the revision writer and the release.
<!-- platform:github:end -->
<!-- platform:git-local:start -->
With `git-local`, `revision` records every change since the last revision commit and commits the result, and `release` cuts a release: revision-line gate, validation, archive and an annotated tag recording its digest.
<!-- platform:git-local:end -->

Scripts behind them, each with `--help` and `--json`: `validate_profile.py`, `new_concept.py` (with `--set key=value`), `build_indexes.py` (with `--check`), `rename_type.py`, `renumber.py`, `write_revision.py`, `stale_report.py`, `build_bundle.py`, `release.py`, `scan.py`.

## Revision-history line

One line per change, appended to each concept the change touched:

```
- <date> · author @<login> · <approval> · <change>[ · full-review][ · agent-drafted]
<change>   ::= PR #<n> | PR none | commit <sha7>
<approval> ::= approved @<login> (owner | non-owner)
             | approved (stale) @<login> (owner | non-owner)
             | self-approved (owner | non-owner)
             | merged without approval @<login>
```

`<date>` is the merge date in UTC. `full-review` is written only when an owner approved the change.

## Commit trailers (git-local)

| Trailer | Meaning |
| --- | --- |
| `Approved-by: Name <email>` | An approval; it counts as someone else's only if the address belongs to another `maintainers` entry |
| `Full-Review: yes` | The owner reviewed each changed concept in full |
| `Agent-Drafted: yes` | An agent wrote some of the change |
| `Revision-Bot: true` | A revision-writer commit; written by `poe revision` |

## Finding codes

Every `OKF` code, with its level, check and fixture, is listed in [Finding codes](finding-codes.md). Errors block a merge; warnings need a reason or a fix.
