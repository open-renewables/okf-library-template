# Runbook: instantiate a library (W-01) and time it (V-06)

A run sheet for creating a library from the template. It is also the sheet a second person follows when FR6.1 is timed in build phase P4 (V-06): **create a library and merge a first validated concept in under 30 minutes.** The commands were rehearsed on 2026-11-09 for `platform: github` (`p2-scratch-github`) and `platform: git-local` (`p2-scratch-local`).

## What you need

| For | Need |
| --- | --- |
| Both | Python 3.11 or later, `uv`, `git` |
| `github` | `gh` signed in as an owner of the organisation; for a protected `main`, the revision App (steps 3 and 5 of `runbook-promote-to-public.md`) |
| `git-local` | nothing else |

## Steps

Start a timer. Note the clock time at the end of each step in the timing table.

1. **Create the repository.** `github`: on the template page choose **Use this template → Create a new repository** (public or private, no branches). `git-local`: clone the template or unpack a release archive, then `git init`. (About 1 minute.)
2. **Clone and install.** `git clone <your repository>`, then `uv sync` (about 2 minutes).
3. **Write the answers.** Copy `tests/template/instantiation/answers-github.yaml` (or `answers-git-local.yaml`) outside the repository and edit it: `platform`, `name`, `title`, `description`, `repository`, `maintainer` (login, name, email), `licence_holder`, `content_licence` (`CC-BY-4.0`, `CC-BY-SA-4.0`, `CC0-1.0` or `proprietary`), `code_licence` (`Apache-2.0`, `MIT` or `proprietary`), `keep_examples`, `keep_tests`. Or leave `--answers` out and answer the questions.
4. **Instantiate.** `uv run python scripts/init_library.py --answers <file>`. It rewrites the names, writes the licence files (the full Creative Commons text goes into `LICENSE-content`), clears the example concepts' revision history, removes the template-only files and rebuilds the indexes. About 6 minutes with the questions.
   - A `template name left in …` warning is expected when your login or organisation name contains the template's (for example `open-renewables-sandbox`). Check that each listed file names you on purpose.
5. **Check.** `uv run poe check`. It should end with `0 error(s)`.
6. **Commit and push.** `git add -A && git commit -m "Instantiate the library" && git push origin main`.
7. **`github` only: apply the repository settings.** `uv run python scripts/setup_repo.py --dry-run`, then `uv run python scripts/setup_repo.py` (add `--app-slug <slug>` when the App exists). About 5 minutes. For a public library also step 5 of `runbook-promote-to-public.md`.
8. **First concept.** `uv run python scripts/new_concept.py Item <group>/<category>/<name> --title "<title>" --description "<one sentence>"`; write the declared sections with a footnote source; `uv run python scripts/build_indexes.py`; `uv run poe check`.
9. **Merge it.** `github`: branch, push, open a pull request, wait for `validate`, merge (a first concept on one's own library is `self-approved`). `git-local`: commit with any trailers, then `uv run poe revision`.

Stop the timer when the first concept is on `main` and `uv run poe check` passes.

## Timing table (V-06)

Fill one row per person. The platform steps (1, 4, 7) are measured first, then the whole sheet. The gate is 30 minutes in total (FR6.1).

| Person | Platform | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 | Step 7 | Step 8 | Step 9 | Total | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | | | | | | |

Record where the person stopped to ask or to read, because those are the places the sheet needs changing.

## If something fails

| Symptom | Cause and fix |
| --- | --- |
| `init_library.py` says the folder does not look like a copy of the template | Run it from the repository root, or pass `--root` |
| `setup_repo.py` fails creating a label with HTTP 422 | A label description is longer than 100 characters; shorten it in `.github/labels.yml` |
| `validate` is red on `main` straight after instantiating | Run `uv run poe check` locally; the first failure names the file |
| The first `revision` run fails on a protected `main` | The App is missing or `rules.revision_token` is `github-token`; see `runbook-revision-writer-recovery.md` |
