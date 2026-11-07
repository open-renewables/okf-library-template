# Runbook: recover the revision history

For a library whose `revision.yml` run failed or was cancelled, whose revision lines are missing, or whose bot cannot push. It rests on SDD W-05: each run records every change merged since the last `Revision-Bot` commit, so a missed run is repaired by the next one and nothing is lost. For a `git-local` library, `uv run poe revision` plays the part of the workflow.

## 1. Find out what is missing

```bash
git fetch origin
git switch main && git pull --ff-only
uv run poe stale --check-since <previous-release-tag>
```

Without a tag, use the library's first commit. The report lists each merged change whose concept has no revision line (`OKF901`). A change that is still waiting for the next run is normal for a few minutes after a merge.

## 2. Let the next run catch up

Merge any change, or run the workflow by hand (**Actions → revision → Run workflow**; it runs on `main`). It reads from the last `Revision-Bot` commit, so it records everything that is missing, in order. Check the result:

```bash
git pull --ff-only
uv run poe stale --check-since <previous-release-tag>
```

## 3. If the workflow keeps failing, run it locally

You need a token that may read pull requests and, when `main` is protected, push to it. For a protected `main` that is the App's token, which only the workflow can mint; so do the recording locally and push through a pull request:

```bash
git switch -c fix/revision-catch-up
export GITHUB_TOKEN=$(gh auth token)          # your own token, to read pull requests
uv run poe revision                            # writes lines and indexes, commits with the Revision-Bot trailer
git push -u origin fix/revision-catch-up
```

Open a pull request and merge it with a squash. The squash replaces the `Revision-Bot` trailer on the commit, so the next workflow run records this pull request as an ordinary change; that adds one line and no harm. Prefer fixing the workflow where you can.

## 4. Symptoms and causes

| Symptom | Cause and fix |
| --- | --- |
| The run is skipped | The head commit carries `Revision-Bot: true`: the writer's own push does not start another run. Nothing to do |
| `push declined due to repository rule violations` | The App is not on the ruleset bypass list with mode "always", or `rules.revision_token` is still `github-token` on a protected `main`. Run `uv run python scripts/setup_repo.py --check --app-slug <slug>` and follow its messages |
| `'Issuer' claim ('iss') must be an Integer` | `APP_CLIENT_ID` has a lower-case `l` where the client ID has a capital `I` (`Iv23li…`), or holds the App ID's text; correct the variable. `setup_repo.py --check` compares it with the App's real client ID |
| Both pushes of a run fail on non-fast-forward | Another merge landed meanwhile. The job pulls with rebase and retries three times; rerun the workflow |
| A line records `PR none` for a pull request | The platform had not yet linked the commit to its pull request (it lagged by up to 8 s in the sandbox, and the lookup waits 30 s for a squash commit). Correct nothing by hand: the history only grows. If it matters, open an issue |
| A line is wrong for another reason | Do not edit it. `OKF315` fails a change that edits or removes a recorded line. Record the correction in `DECISIONS.md` and, if the tier is affected, merge a reviewed change with the `full-review` label |
| `OKF901` stays after the next run | The concept was changed in a commit the writer could not resolve to a change, for example a direct push that skipped the pull request; the next release gate will keep failing until a line exists. Run step 3 |

## 5. Rotate the App's private key

1. In the App's settings, **Generate a private key**; keep the new `.pem` private.
2. Replace the secret `APP_PRIVATE_KEY` in the repository (**Settings → Secrets and variables → Actions**).
3. Run the `revision` workflow by hand and check it pushes.
4. Delete the old key in the App's settings.

## 6. What not to do

Do not edit a revision line or an `index.md` by hand (`OKF315` and `OKF502` fail them), and do not push to `main` with the App's token from your own machine.
