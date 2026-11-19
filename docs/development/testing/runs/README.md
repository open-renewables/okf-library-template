# Acceptance runs

One folder per run of the [Master Test Plan](../master-test-plan.md): `YYYY-MM-DD-<library>/`, holding the filled `library-under-test.yaml`, `run-sheet.md` and `results-report.md` (blank forms in [acceptance-templates.md](../acceptance-templates.md), sections 2 and 3), and `findings/` summaries. Raw logs are not committed; the report records where they are (OD-AT3).

`planned/` holds the parameter files for the P4 runs, filled except for the date:

| File | Environment | Phases | Runner |
| --- | --- | --- | --- |
| [`planned/scratch-local.yaml`](planned/scratch-local.yaml) | E-LOCAL, `git-local` scratch library | 1, 2, 4 | agent |
| [`planned/scratch-github.yaml`](planned/scratch-github.yaml) | E-GH, `github` scratch repository in `open-renewables-sandbox` | 3 (live) | owner, agent preparing each case |
| [`planned/pilot.yaml`](planned/pilot.yaml) | E-REAL, the pilot after promotion | 1 (read-only), 5 | owner and agent |

To start a run: copy the planned file into a new run folder as `library-under-test.yaml`, set `run.id` and `evidence.folder` to the folder name, fill `accounts.owner_login`, and copy the run sheet and report forms. No token, key or password goes in any file; name the environment variable that holds it.

## Entry criteria (MTP section 7) at 2026-11-19

| Criterion | State |
| --- | --- |
| Template build complete (P3 merged, `v0.5.0` tagged) | Met 2026-11-15 |
| `poe check` and `poe test` pass on the tag under test | Due on `v0.9.0` (P4 step 5) |
| Every case's `pending` status cleared or recorded `blocked` | Met 2026-11-19 (P4 PR 3) |
| Parameter file filled and reviewed | Drafted in `planned/`; the owner reviews them with this pull request |
| Sandbox repositories exist (E-GH); token in its environment variable | Due before phase 3 (P4 steps 8, 9, 11) |
