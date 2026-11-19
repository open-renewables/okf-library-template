# Runbook: remove leaked content

For a secret, personal data or confidential text that reached a library's history, found by `uv run poe scan --all`, by gitleaks, by GitHub secret scanning or by a person. **Partly rehearsed (2026-11-14, in the sandbox library `p3-scratch-github`):** the leak, its detection, the Release and the rewrite ran; the force-push to the protected `main`, the tag pushes and `validate` after a rewrite did not, and stay untested until a real incident (G33, closed on that basis). Removing it from history rewrites commits, which the design otherwise forbids (W-12: history and revision lines are never rewritten), so this is an exception that you record.

## 1. Stop the spread (minutes)

1. If it is a credential or token, **revoke and replace it at its source first.** Treat it as public from the moment it was pushed to a public repository or to a remote others can read; removal from history does not undo that.
2. Pause merging: set the `main` ruleset to disabled only if you must rewrite `main` (step 3); otherwise tell contributors not to merge.
3. Note what leaked, where (file, commit, pull request), and who could have read it.

## 2. Decide how far to go

| Situation | Action |
| --- | --- |
| Only in an open pull request or an unmerged branch | Close the pull request and delete the branch; ask GitHub support to purge cached views if it was public |
| In `main`, nobody else has cloned, nothing released | Rewrite history (step 3) |
| In `main` and in a release or in clones | The secret is burned. Revoke it, remove the content in a new commit, and rewrite history only if the content itself (not a credential) must disappear |

## 3. Rewrite history

Use a clean clone and `git filter-repo` (a separate tool; install it as its documentation says). Remove the path or replace the text, then force-push:

```bash
git clone --mirror https://github.com/<org>/<repo>.git leak.git && cd leak.git
git filter-repo --path <leaked-file> --invert-paths        # or --replace-text <file-of-patterns>
git push --force --all
git push --force --tags
```

What the rehearsal showed (a file under `profile/` merged by pull request, a release tag cut on it, then the rewrite with `uvx --from git-filter-repo git-filter-repo --path <file> --invert-paths`):

- **Detection.** `uv run poe scan --all` finds a marker or a secret-shaped string only in files git tracks, so run it after the commit. In CI the `scan` job stops at the first failing step: the `scan.py` finding is reported and the gitleaks step after it does not run, so a second secret that only gitleaks sees stays hidden until the first is removed.
- **Delete the Release before the rewrite.** The release archive of a tag cut after the leak holds the leaked file. On a repository with immutable releases an asset cannot be deleted, but the whole Release can; its tag name can then never be reused.
- **Every commit id changes, not only those after the leak.** Web merges on GitHub are signed, and `git filter-repo` drops the signatures when it rewrites, so the whole history and every tag get new ids (all six tags moved). A pull request that only added the leaked file becomes an empty commit and disappears, so two tags can end on the same commit.
- **Revision lines.** Lines that cite `PR #n` stay correct; lines that cite `commit <sha7>` (a library that began as `git-local`) point at ids that no longer exist.

Pushing to a protected `main` needs the ruleset disabled for the push and re-enabled straight after; re-run `uv run python scripts/setup_repo.py --check` to confirm the ruleset is back. Every commit after the leak gets a new identifier.

## 4. Repair what the rewrite broke

- **Revision lines** that cite `commit <sha7>` or a pull request now point at commits that no longer exist. Do not edit the lines (`OKF315` fails an edited line). Add a `DECISIONS.md` entry that lists the rewrite and the old and new identifiers if known.
- **Release tags** move with the rewrite; each past archive no longer rebuilds from its tag. Keep the originals from `dist/` or the GitHub Release assets as the citable files, and say so in the release notes.
- **Clones and forks:** everyone re-clones. Open forks keep the old history; ask their owners to delete them.
- **GitHub caches:** ask GitHub support to remove cached copies and to garbage-collect unreachable commits; closed pull requests keep their diffs until then.

## 5. Check and prevent

```bash
uv run poe scan --all
uv run poe check
```

Run gitleaks over the whole history as well (it is not installed here by default). Add the leaked pattern to `profile/scan.yaml` if the scanner missed it, in a tooling pull request on its own, and record the incident in `DECISIONS.md` with the date and what changed.
