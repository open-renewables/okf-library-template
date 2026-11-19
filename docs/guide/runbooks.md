# Runbooks

Step-by-step procedures. Each section stands on its own; run its commands from the library's root.

<!-- template-only:start -->
- [Instantiate a library](#instantiate-a-library): creating a library from the template, and timing it.
<!-- template-only:end -->
- [Promote a library to public](#promote-a-library-to-public): a private GitHub library goes public, normally at its `v1.0.0`.
- [Move a git-local library to GitHub](#move-a-git-local-library-to-github): a library run with git and Python alone moves to GitHub.
- [Recover the revision history](#recover-the-revision-history): a revision run failed, a line is missing, or the bot cannot push.
- [Remove leaked content](#remove-leaked-content): a secret or confidential text reached the repository.

<!-- template-only:start -->
## Instantiate a library

A run sheet for creating a library from the template: **create a library and merge a first validated concept in under 30 minutes.** The commands were rehearsed for both `platform: github` and `platform: git-local` before the template's release.

### What you need

| For | Need |
| --- | --- |
| Both | Python 3.11 or later, `uv`, `git` |
| `github` | `gh` signed in as an owner of the organisation; for a protected `main`, the revision App (steps 3 and 5 of [Promote a library to public](#promote-a-library-to-public)) |
| `git-local` | nothing else |

### Steps

Start a timer. Note the clock time at the end of each step in the timing table.

1. **Create the repository.** `github`: on the template page choose **Use this template → Create a new repository** (public or private, no branches). `git-local`: clone the template or unpack a release archive, then `git init`. (About 1 minute.)
2. **Clone and install.** `git clone <your repository>`, then `uv sync` (about 2 minutes).
3. **Write the answers.** Copy `tests/template/instantiation/answers-github.yaml` (or `answers-git-local.yaml`) outside the repository and edit it: `platform`, `name`, `title`, `description`, `repository`, `maintainer` (login, name, email), `licence_holder`, `content_licence` (`CC-BY-4.0`, `CC-BY-SA-4.0`, `CC0-1.0` or `proprietary`), `code_licence` (`Apache-2.0`, `MIT` or `proprietary`), `keep_examples`, `keep_tests`. Or leave `--answers` out and answer the questions.
4. **Instantiate.** `uv run python scripts/init_library.py --answers <file>`. It rewrites the names, writes the licence files (the full Creative Commons text goes into `LICENSE-content`), clears the example concepts' revision history, removes the template-only files and rebuilds the indexes. About 6 minutes with the questions.
   - A `template name left in …` warning is expected when your login or organisation name contains the template's (for example an organisation named after the template). Check that each listed file names you on purpose.
5. **Check.** `uv run poe check`. It should end with `0 error(s)`.
6. **Commit and push.** `git add -A && git commit -m "Instantiate the library" && git push origin main`.
7. **`github` only: apply the repository settings.** `uv run python scripts/setup_repo.py --dry-run`, then `uv run python scripts/setup_repo.py` (add `--app-slug <slug>` when the App exists). About 5 minutes. For a public library also step 5 of [Promote a library to public](#promote-a-library-to-public).
8. **First concept.** `uv run python scripts/new_concept.py Item <group>/<category>/<name> --title "<title>" --description "<one sentence>"`; write the declared sections with a footnote source; `uv run python scripts/build_indexes.py`; `uv run poe check`.
9. **Merge it.** `github`: branch, push, open a pull request, wait for `validate`, merge (a first concept on one's own library is `self-approved`). `git-local`: commit with any trailers, then `uv run poe revision`.

Stop the timer when the first concept is on `main` and `uv run poe check` passes.

### Rename the primary type (optional, before the first commit)

To give the primary type (`Item`, prefix `ITM`) the library's own name, run `uv run python scripts/rename_type.py Item <NewType> <PREFIX>` after step 4 and before step 6, the first commit. The procedure and why it must come first are in [Customising the profile](customising.md#rename-the-primary-type).

### Timing table

Fill one row per person. The platform steps (1, 4, 7) are measured first, then the whole sheet. The target is 30 minutes in total.

| Person | Platform | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 | Step 7 | Step 8 | Step 9 | Total | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | | | |

Record where the person stopped to ask or to read, because those are the places the sheet needs changing.

### If something fails

| Symptom | Cause and fix |
| --- | --- |
| `init_library.py` says the folder does not look like a copy of the template | Run it from the repository root, or pass `--root` |
| `setup_repo.py` fails creating a label with HTTP 422 | A label description is longer than 100 characters; shorten it in `.github/labels.yml` |
| `validate` is red on `main` straight after instantiating | Run `uv run poe check` locally; the first failure names the file |
| The first `revision` run fails on a protected `main` | The App is missing or `rules.revision_token` is `github-token`; see [Recover the revision history](#recover-the-revision-history) |
<!-- template-only:end -->

## Promote a library to public

Optional: a library may stay private for good. Run this when a `github` library goes public, normally at its v1.0.0. It uses `setup_repo.py --promote` and ends with the `main` ruleset, native secret scanning, push protection, immutable releases, GitHub Pages and the revision App in place.

### 1. Before you start

| Need | Check |
| --- | --- |
| The library's platform is `github` | `platform: github` in `profile/profile.yaml` |
| GitHub CLI, signed in as an organisation owner | `gh auth status` shows the `repo` and `admin:org` scopes |
| `main` is green, and `uv run poe check` and `uv run poe test` pass | Run both |
| Nothing confidential is in the repository or its history | `uv run poe scan --all`; for history, run gitleaks over all commits. If anything is found, stop and follow [Remove leaked content](#remove-leaked-content) |
| Nothing is still being merged | No open pull request that you do not intend to publish |

Making a repository public cannot be undone for what was already visible, so check the history before step 2.

### 2. Make the repository public

Repository **Settings → General → Danger zone → Change visibility → Make public**. `setup_repo.py` never does this: it refuses `--promote` on a private repository.

### 3. Create and install the revision App

Needed because `main` is protected from now on and `GITHUB_TOKEN` cannot push to it (plan step 1, 5a). About ten minutes.

1. Organisation **Settings → Developer settings → GitHub Apps → New GitHub App**, owned by the organisation. Name it, for example, `<library>-revision-bot`; untick **Webhook → Active**; choose **Only on this account**.
2. Repository permissions: **Contents: Read and write**, **Pull requests: Read-only**, and nothing else.
3. Create it, then **Generate a private key** (a `.pem` file stays on your machine; never paste it into a chat or commit it).
4. **Install App** on the organisation, **Only select repositories**, and choose this library.
5. In the repository, **Settings → Secrets and variables → Actions**:
   - **Variables** tab: `APP_CLIENT_ID` with the App's client ID. It starts with a capital `I` (`Iv23li…`); a lower-case `l` fails with "'Issuer' claim ('iss') must be an Integer".
   - **Secrets** tab: `APP_PRIVATE_KEY` with the whole `.pem`, BEGIN and END lines included.

### 4. Apply the settings

Look first, then apply:

```bash
uv run python scripts/setup_repo.py --promote --app-slug <app-slug> --dry-run
uv run python scripts/setup_repo.py --promote --app-slug <app-slug>
```

`--promote` sets what a private library does not have: the `main-protect` ruleset (pull request with one code-owner approval, the `validate` check once `validate.yml` exists, squash merges, repository admin bypass "for pull requests only", the App bypass "always"), native secret scanning with push protection, CodeQL default setup and GitHub Pages built by workflow, with the `github-pages` environment allowed to deploy from `main` and from `v*` tags (without that, the tag run that publishes the site is refused). It also changes `rules.revision_token` to `github-app` in `profile/profile.yaml` in your working tree. It then prints one manual step: enable **immutable releases** in **Settings → General**.

Every call names the repository, and the run is safe to repeat.

### 5. Merge the profile change

The `revision_token` edit is a tooling change. Commit it on a branch, open a pull request and merge it (squash). Until it merges, `revision.yml` keeps using `GITHUB_TOKEN` and is refused by the ruleset.

### 6. Check

```bash
uv run python scripts/setup_repo.py --check --app-slug <app-slug>
```

It must report no problem: no drift, the App installed, the App on the ruleset bypass list with mode "always", `APP_CLIENT_ID` equal to the App's client ID, and `APP_PRIVATE_KEY` present. Then merge one small content change and confirm that a `Revision-Bot` commit appears on `main`.

### 7. Record it

Add a row to `DECISIONS.md`: the date, "Promoted to public", the App slug, and, if the CI secret scanner was kept or removed, which.

### If something goes wrong

| Symptom | Cause and fix |
| --- | --- |
| `--promote` stops with "make it public first" | The repository is still private; do step 2 |
| "--promote needs --app-slug" | Pass the slug of the installed App |
| "the App ... is not installed" | Step 3.4: the App must be installed in the organisation |
| Revision commits are refused on `main` | The App is not on the bypass list or `revision_token` is still `github-token`; rerun step 4, merge step 5, then `--check` |
| Workflow fails minting the App token | `APP_CLIENT_ID` has a lower-case `l`, or `APP_PRIVATE_KEY` is truncated |
| A pull request cannot merge for a lack of approval | You are the only maintainer: merge as a repository admin (the "for pull requests only" bypass); the merge is recorded as `self-approved` |

To undo the protection, delete the `main-protect` ruleset in **Settings → Rules**. Visibility cannot be undone for content that was public.

## Move a git-local library to GitHub

For a library that has run with `platform: git-local` and now moves to GitHub. The procedure was rehearsed with a scratch library before the template's release. The rule throughout: history, tags and revision lines are never rewritten, so every commit identifier, every `commit <sha7>` line and every release archive stays valid.

### 1. Before you start

| Need | Check |
| --- | --- |
| The library is clean and validates | `uv run poe check` and `uv run poe test` pass; `git status` shows nothing |
| No change is missing its revision line | `uv run poe stale --check-since <first-commit>` lists no `OKF901` |
| Each past release has its archive digest in its tag message | `git tag -n8 vX.Y.Z` shows `Archive-Tar-SHA256` and `Archive-SHA256` |
| GitHub CLI signed in with `repo` scope as an owner of the target organisation | `gh auth status` |

### 2. Push the history

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

### 3. Switch the platform in one tooling branch

On a branch, change only tooling files:

1. In `profile/profile.yaml`: `platform: github`, and `library.repository` to the new URL. Keep `maintainers`: earlier lines name those logins.
2. Restore the GitHub files from the template release in `template_version`: `.github/ISSUE_TEMPLATE/`, `.github/workflows/`, `.github/labels.yml`, `.github/dependabot.yml`, `.github/pull_request_template.md`. `init_library.py` removed them for `git-local`; copy them from a library created with `platform: github`, or from the template at that tag. `.github/CODEOWNERS` is already there. In `.github/ISSUE_TEMPLATE/config.yml` use the new repository's address.
3. Run `uv run poe check` and `uv run poe check-config`.
4. Push the branch, open a pull request and merge it (no ruleset exists yet, so it merges at once).

Do not mix this with concept changes: the mixed-change rule applies on GitHub from the next pull request.

### 4. Apply the repository settings

```bash
uv run python scripts/setup_repo.py --app-slug <app-slug> --dry-run
uv run python scripts/setup_repo.py --app-slug <app-slug>
```

This sets labels, squash-only merges and the `main-protect` ruleset (and secret scanning where the plan allows). Create and install the revision App first (steps 3 and 5 of [Promote a library to public](#promote-a-library-to-public)) if `main` is to be protected: with the ruleset on, `GITHUB_TOKEN` can no longer push the revision commit, so set `rules.revision_token: github-app` through a pull request, as promoting a library to public does. Until then the first merges fail in the `revision` workflow, and the next run recovers them ([Recover the revision history](#recover-the-revision-history)).

### 5. Rebuild each past release and upload it

For every tag, in a **fresh clone** of the new repository:

```bash
git clone https://github.com/<org>/<repo>.git check && cd check
git fetch --tags
uv run python scripts/build_bundle.py --tag vX.Y.Z --ref vX.Y.Z --out ../rebuilt
sha256sum ../rebuilt/<name>-vX.Y.Z.tar.gz
git tag -n8 vX.Y.Z
```

The tar digest printed by the build and the `.tar.gz` digest from `sha256sum` equal the two values in the tag message. The gzip digest equals only where the Python and zlib versions match those recorded in the tag message; the tar digest is the canonical check. Cross-check with the original manifest:

```bash
uv run python scripts/build_bundle.py --root . --ref vX.Y.Z --rebuild-check <original-manifest>
```

It prints `archive matches`. Only then upload:

```bash
gh release create vX.Y.Z -R <org>/<repo> --title vX.Y.Z --notes "<text>" \
  ../rebuilt/<name>-vX.Y.Z.tar.gz ../rebuilt/<name>-vX.Y.Z.tar.gz.sha256 ../rebuilt/<name>-vX.Y.Z.manifest.json
```

If a digest differs, do not upload that release. Record the difference in `DECISIONS.md` and keep the original archive from `dist/` as the citable file.

### 6. Check and record

- Earlier revision lines still read `commit <sha7>`; new ones read `PR #n`.
- `uv run poe check` passes in the new clone.
- Add an entry to `DECISIONS.md`: the date, the new address, and any release that could not be rebuilt.
- Optional: make the library public with [Promote a library to public](#promote-a-library-to-public).

### 7. What the rehearsal showed

- Identifiers, tags and lines were unchanged after the push; the rebuilt archive for `v0.0.1` matched both digests in the tag message.
- On a new repository GitHub did not register the workflow files until the first merge to `main`, so the switch pull request showed no checks; the merge started `validate` and `revision` normally.

## Recover the revision history

For a library whose `revision.yml` run failed or was cancelled, whose revision lines are missing, or whose bot cannot push. It rests on one rule: each run records every change merged since the last `Revision-Bot` commit, so a missed run is repaired by the next one and nothing is lost. For a `git-local` library, `uv run poe revision` plays the part of the workflow.

### 1. Find out what is missing

```bash
git fetch origin
git switch main && git pull --ff-only
uv run poe stale --check-since <previous-release-tag>
```

Without a tag, use the library's first commit. The report lists each merged change whose concept has no revision line (`OKF901`). A change that is still waiting for the next run is normal for a few minutes after a merge.

### 2. Let the next run catch up

Merge any change, or run the workflow by hand (**Actions → revision → Run workflow**; it runs on `main`). It reads from the last `Revision-Bot` commit, so it records everything that is missing, in order. Check the result:

```bash
git pull --ff-only
uv run poe stale --check-since <previous-release-tag>
```

### 3. If the workflow keeps failing, run it locally

You need a token that may read pull requests and, when `main` is protected, push to it. For a protected `main` that is the App's token, which only the workflow can mint; so do the recording locally and push through a pull request:

```bash
git switch -c fix/revision-catch-up
export GITHUB_TOKEN=$(gh auth token)          # your own token, to read pull requests
uv run poe revision                            # writes lines and indexes, commits with the Revision-Bot trailer
git push -u origin fix/revision-catch-up
```

Open a pull request and merge it with a squash. The squash replaces the `Revision-Bot` trailer on the commit, so the next workflow run records this pull request as an ordinary change; that adds one line and no harm. Prefer fixing the workflow where you can.

### 4. Symptoms and causes

| Symptom | Cause and fix |
| --- | --- |
| The run is skipped | The head commit carries `Revision-Bot: true`: the writer's own push does not start another run. Nothing to do |
| `push declined due to repository rule violations` | The App is not on the ruleset bypass list with mode "always", or `rules.revision_token` is still `github-token` on a protected `main`. Run `uv run python scripts/setup_repo.py --check --app-slug <slug>` and follow its messages |
| `'Issuer' claim ('iss') must be an Integer` | `APP_CLIENT_ID` has a lower-case `l` where the client ID has a capital `I` (`Iv23li…`), or holds the App ID's text; correct the variable. `setup_repo.py --check` compares it with the App's real client ID |
| Both pushes of a run fail on non-fast-forward | Another merge landed meanwhile. The job pulls with rebase and retries three times; rerun the workflow |
| A line records `PR none` for a pull request | The platform had not yet linked the commit to its pull request (it lagged by up to 8 s in the sandbox, and the lookup waits 30 s for a squash commit). Correct nothing by hand: the history only grows. If it matters, open an issue |
| A line is wrong for another reason | Do not edit it. `OKF315` fails a change that edits or removes a recorded line. Record the correction in `DECISIONS.md` and, if the tier is affected, merge a reviewed change with the `full-review` label |
| `OKF901` stays after the next run | The concept was changed in a commit the writer could not resolve to a change, for example a direct push that skipped the pull request; the next release gate will keep failing until a line exists. Run step 3 |

### 5. Rotate the App's private key

1. In the App's settings, **Generate a private key**; keep the new `.pem` private.
2. Replace the secret `APP_PRIVATE_KEY` in the repository (**Settings → Secrets and variables → Actions**).
3. Run the `revision` workflow by hand and check it pushes.
4. Delete the old key in the App's settings.

### 6. What not to do

Do not edit a revision line or an `index.md` by hand (`OKF315` and `OKF502` fail them), and do not push to `main` with the App's token from your own machine.

## Remove leaked content

For a secret, personal data or confidential text that reached a library's history, found by `uv run poe scan --all`, by gitleaks, by GitHub secret scanning or by a person. **Partly rehearsed** before the template's release: the leak, its detection, the Release and the rewrite ran; the force-push to the protected `main`, the tag pushes and validation after a rewrite did not, and stay untested until a real incident. Removing content from history rewrites commits, which the library otherwise never does (history and revision lines are never rewritten), so this is an exception that you record.

### 1. Stop the spread (minutes)

1. If it is a credential or token, **revoke and replace it at its source first.** Treat it as public from the moment it was pushed to a public repository or to a remote others can read; removal from history does not undo that.
2. Pause merging: set the `main` ruleset to disabled only if you must rewrite `main` (step 3); otherwise tell contributors not to merge.
3. Note what leaked, where (file, commit, pull request), and who could have read it.

### 2. Decide how far to go

| Situation | Action |
| --- | --- |
| Only in an open pull request or an unmerged branch | Close the pull request and delete the branch; ask GitHub support to purge cached views if it was public |
| In `main`, nobody else has cloned, nothing released | Rewrite history (step 3) |
| In `main` and in a release or in clones | The secret is burned. Revoke it, remove the content in a new commit, and rewrite history only if the content itself (not a credential) must disappear |

### 3. Rewrite history

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

### 4. Repair what the rewrite broke

- **Revision lines** that cite `commit <sha7>` or a pull request now point at commits that no longer exist. Do not edit the lines (`OKF315` fails an edited line). Add a `DECISIONS.md` entry that lists the rewrite and the old and new identifiers if known.
- **Release tags** move with the rewrite; each past archive no longer rebuilds from its tag. Keep the originals from `dist/` or the GitHub Release assets as the citable files, and say so in the release notes.
- **Clones and forks:** everyone re-clones. Open forks keep the old history; ask their owners to delete them.
- **GitHub caches:** ask GitHub support to remove cached copies and to garbage-collect unreachable commits; closed pull requests keep their diffs until then.

### 5. Check and prevent

```bash
uv run poe scan --all
uv run poe check
```

Run gitleaks over the whole history as well (it is not installed here by default). Add the leaked pattern to `profile/scan.yaml` if the scanner missed it, in a tooling pull request on its own, and record the incident in `DECISIONS.md` with the date and what changed.
