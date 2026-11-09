# Runbook: remove leaked content

For a secret, personal data or confidential text that reached a library's history, found by `uv run poe scan --all`, by gitleaks, by GitHub secret scanning or by a person. **Not rehearsed.** Removing it from history rewrites commits, which the design otherwise forbids (W-12: history and revision lines are never rewritten), so this is an exception that you record. Known gap G33 lists what is untested.

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
