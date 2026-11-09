# Runbook: move a git-local library to GitHub (W-12)

For a library that has run with `platform: git-local` and now moves to GitHub. It applies SDD W-12 and was rehearsed on 2026-11-09 with `open-renewables-sandbox/p2-scratch-local` moved to `p2-w12-target` (known gap G32 lists what the rehearsal did not cover). The rule throughout: history, tags and revision lines are never rewritten, so every commit identifier, every `commit <sha7>` line and every release archive stays valid.

## 1. Before you start

| Need | Check |
| --- | --- |
| The library is clean and validates | `uv run poe check` and `uv run poe test` pass; `git status` shows nothing |
| No change is missing its revision line | `uv run poe stale --check-since <first-commit>` lists no `OKF901` |
| Each past release has its archive digest in its tag message | `git tag -n8 vX.Y.Z` shows `Archive-Tar-SHA256` and `Archive-SHA256` |
| GitHub CLI signed in with `repo` scope as an owner of the target organisation | `gh auth status` |

## 2. Push the history

Create an **empty** repository (no README, no licence, no `.gitignore`), then:

```bash
git remote add origin https://github.com/<org>/<repo>.git
git push --all origin
git push --tags origin
```

Check that nothing changed in transit:

```bash
git rev-parse HEAD
gh api repos/<org>/<repo>/commits/main -q .sha
git ls-remote --tags origin
```

The two commit identifiers are equal, and each tag points at the same object as before. If they differ, stop: something rewrote history.

## 3. Switch the platform in one tooling branch

On a branch, change only tooling files:

1. In `profile/profile.yaml`: `platform: github`, and `library.repository` to the new URL. Keep `maintainers`: earlier lines name those logins.
2. Restore the GitHub files from the template release in `template_version`: `.github/ISSUE_TEMPLATE/`, `.github/workflows/`, `.github/labels.yml`, `.github/dependabot.yml`, `.github/pull_request_template.md`. `init_library.py` removed them for `git-local`; copy them from a library created with `platform: github`, or from the template at that tag. `.github/CODEOWNERS` is already there. In `.github/ISSUE_TEMPLATE/config.yml` use the new repository's address.
3. Run `uv run poe check` and `uv run poe check-config`.
4. Push the branch, open a pull request and merge it (no ruleset exists yet, so it merges at once).

Do not mix this with concept changes: the mixed-change rule applies on GitHub from the next pull request.

## 4. Apply the repository settings

```bash
uv run python scripts/setup_repo.py --app-slug <app-slug> --dry-run
uv run python scripts/setup_repo.py --app-slug <app-slug>
```

This sets labels, squash-only merges and the `main-protect` ruleset (and secret scanning where the plan allows). Create and install the revision App first (steps 3 and 5 of `runbook-promote-to-public.md`) if `main` is to be protected: with the ruleset on, `GITHUB_TOKEN` can no longer push the revision commit, so set `rules.revision_token: github-app` through a pull request, as W-11 does. Until then the first merges fail in the `revision` workflow, and the next run recovers them (`runbook-revision-writer-recovery.md`).

## 5. Rebuild each past release and upload it

For every tag, in a **fresh clone** of the new repository:

```bash
git clone https://github.com/<org>/<repo>.git check && cd check
git fetch --tags
uv run python scripts/build_bundle.py --tag vX.Y.Z --ref vX.Y.Z --out ../rebuilt
sha256sum ../rebuilt/<name>-vX.Y.Z.tar.gz
git tag -n8 vX.Y.Z
```

The tar digest printed by the build and the `.tar.gz` digest from `sha256sum` equal the two values in the tag message. The gzip digest equals only where the Python and zlib versions match those recorded in the tag message; the tar digest is the canonical check (ADR-004). Cross-check with the original manifest:

```bash
uv run python scripts/build_bundle.py --root . --ref vX.Y.Z --rebuild-check <original-manifest>
```

It prints `archive matches`. Only then upload:

```bash
gh release create vX.Y.Z -R <org>/<repo> --title vX.Y.Z --notes "<text>" \
  ../rebuilt/<name>-vX.Y.Z.tar.gz ../rebuilt/<name>-vX.Y.Z.tar.gz.sha256 ../rebuilt/<name>-vX.Y.Z.manifest.json
```

If a digest differs, do not upload that release. Record the difference in `DECISIONS.md` and keep the original archive from `dist/` as the citable file.

## 6. Check and record

- Earlier revision lines still read `commit <sha7>`; new ones read `PR #n`.
- `uv run poe check` passes in the new clone.
- Add an entry to `DECISIONS.md`: the date, the new address, and any release that could not be rebuilt.
- Optional: make the library public with `runbook-promote-to-public.md`.

## 7. What the rehearsal showed

- Identifiers, tags and lines were unchanged after the push; the rebuilt archive for `v0.0.1` matched both digests in the tag message.
- On a new repository GitHub did not register the workflow files until the first merge to `main`, so the switch pull request showed no checks; the merge started `validate` and `revision` normally.
