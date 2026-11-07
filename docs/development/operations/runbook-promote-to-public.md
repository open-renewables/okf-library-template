# Runbook: promote a library to public (W-11)

Optional: a library may stay private for good (SRS T1). Run this when a `github` library goes public, normally at its v1.0.0. It applies SDD W-11 with `setup_repo.py --promote` (plan step 10) and ends with the settings of SDD §11, "Library once public".

## 1. Before you start

| Need | Check |
| --- | --- |
| The library's platform is `github` | `platform: github` in `profile/profile.yaml` |
| GitHub CLI, signed in as an organisation owner | `gh auth status` shows the `repo` and `admin:org` scopes |
| `main` is green, and `uv run poe check` and `uv run poe test` pass | Run both |
| Nothing confidential is in the repository or its history | `uv run poe scan --all`; for history, run gitleaks over all commits. If anything is found, stop and follow `runbook-remove-leaked-content.md` |
| Nothing is still being merged | No open pull request that you do not intend to publish |

Making a repository public cannot be undone for what was already visible, so check the history before step 2.

## 2. Make the repository public

Repository **Settings → General → Danger zone → Change visibility → Make public**. `setup_repo.py` never does this: it refuses `--promote` on a private repository.

## 3. Create and install the revision App

Needed because `main` is protected from now on and `GITHUB_TOKEN` cannot push to it (plan step 1, 5a). About ten minutes.

1. Organisation **Settings → Developer settings → GitHub Apps → New GitHub App**, owned by the organisation. Name it, for example, `<library>-revision-bot`; untick **Webhook → Active**; choose **Only on this account**.
2. Repository permissions: **Contents: Read and write**, **Pull requests: Read-only**, and nothing else.
3. Create it, then **Generate a private key** (a `.pem` file stays on your machine; never paste it into a chat or commit it).
4. **Install App** on the organisation, **Only select repositories**, and choose this library.
5. In the repository, **Settings → Secrets and variables → Actions**:
   - **Variables** tab: `APP_CLIENT_ID` with the App's client ID. It starts with a capital `I` (`Iv23li…`); a lower-case `l` fails with "'Issuer' claim ('iss') must be an Integer".
   - **Secrets** tab: `APP_PRIVATE_KEY` with the whole `.pem`, BEGIN and END lines included.

## 4. Apply the settings

Look first, then apply:

```bash
uv run python scripts/setup_repo.py --promote --app-slug <app-slug> --dry-run
uv run python scripts/setup_repo.py --promote --app-slug <app-slug>
```

`--promote` sets what a private library does not have: the `main-protect` ruleset (pull request with one code-owner approval, the `validate` check once `validate.yml` exists, squash merges, repository admin bypass "for pull requests only", the App bypass "always"), native secret scanning with push protection, CodeQL default setup and GitHub Pages built by workflow. It also changes `rules.revision_token` to `github-app` in `profile/profile.yaml` in your working tree. It then prints one manual step: enable **immutable releases** in **Settings → General**.

Every call names the repository, and the run is safe to repeat.

## 5. Merge the profile change

The `revision_token` edit is a tooling change. Commit it on a branch, open a pull request and merge it (squash). Until it merges, `revision.yml` keeps using `GITHUB_TOKEN` and is refused by the ruleset.

## 6. Check

```bash
uv run python scripts/setup_repo.py --check --app-slug <app-slug>
```

It must report no problem: no drift, the App installed, the App on the ruleset bypass list with mode "always", `APP_CLIENT_ID` equal to the App's client ID, and `APP_PRIVATE_KEY` present. Then merge one small content change and confirm that a `Revision-Bot` commit appears on `main`.

## 7. Record it

Add a row to `DECISIONS.md`: the date, "Promoted to public (W-11)", the App slug, and, if the CI secret scanner was kept or removed, which.

## If something goes wrong

| Symptom | Cause and fix |
| --- | --- |
| `--promote` stops with "make it public first" | The repository is still private; do step 2 |
| "--promote needs --app-slug" | Pass the slug of the installed App |
| "the App ... is not installed" | Step 3.4: the App must be installed in the organisation |
| Revision commits are refused on `main` | The App is not on the bypass list or `revision_token` is still `github-token`; rerun step 4, merge step 5, then `--check` |
| Workflow fails minting the App token | `APP_CLIENT_ID` has a lower-case `l`, or `APP_PRIVATE_KEY` is truncated |
| A pull request cannot merge for a lack of approval | You are the only maintainer: merge as a repository admin (the "for pull requests only" bypass); the merge is recorded as `self-approved` |

To undo the protection, delete the `main-protect` ruleset in **Settings → Rules**. Visibility cannot be undone for content that was public.
