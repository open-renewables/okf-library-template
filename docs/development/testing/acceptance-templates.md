# Acceptance templates

Blank forms for the [Master Test Plan](master-test-plan.md). Copy them into the run folder (`testing/runs/YYYY-MM-DD-<library>/`) and fill them in. They name no tool or provider: a person or any agent can fill them. The parameter file is [library-under-test.yaml](library-under-test.yaml).

## 1. Test-case template

Add a case to [acceptance-test-cases.md](acceptance-test-cases.md) as one table row in its requirement group, with these columns, or as a block when the steps do not fit a row.

```markdown
### AT-<req>-nn <short title>

- **Requirement:** <SRS id, for example FR2.5>; criterion: <short quote>
- **Kind:** scripted | live | human | review
- **Mode:** RO (real library allowed) | D (scratch only)
- **Preconditions:** <L, S, G, T, A2 and anything else; state the fallback if A2 is missing>
- **Reads from profile:** <types, prefixes, namespaces used; never hard-coded>
- **Steps:**
  1. `<command>` → <expected result: exit code, finding code, file content>
  2. ...
- **Pass when:** <one sentence>
- **Evidence:** E1 | E2 | E3 | E4 | E5 and the file name
- **Status:** ready | pending P2 PRn | pending P3 | pending P4
- **Cites:** <fixture folder, known-gap id, plan step; never a copy of them>
```

Rules: one requirement per case; every expected result is observable (exit code, finding code, text in a file, a count); a case that needs a second account states its fallback and what `partial` means; a case never restates a fixture, gap or plan step, it links it.

## 2. Run sheet

```markdown
# Run sheet: <run id>

| Field | Value |
| --- | --- |
| Run id / date | |
| Template tag and commit | |
| Library, kind, platform | |
| Runner (role) | |
| System and Python version | |
| Phase (smoke, full local, live platform, release and rehearsal, human and agent) | |
| Parameter file | `library-under-test.yaml` (attach) |
| Selection | Mode RO only (real library) / all (scratch) |

| Case | Started | Ended | Result | Evidence file | Defect |
| --- | --- | --- | --- | --- | --- |
| AT-FR1.1-01 | | | pass / fail / partial / blocked / skipped (reason) | logs/AT-FR1.1-01.txt | |

Result values: `pass`; `fail`; `partial` (ran on its stated fallback); `blocked` (precondition or feature missing; name it); `skipped` (with reason). A skipped or blocked case is never counted as passed.

Timing sheet (human cases, E5): step, start, end, minutes, note. Stop the clock only when the first concept has merged.
```

## 3. Results report

```markdown
# Results report: <run id>

## Summary
- Template tag, library, platform, systems, Python versions.
- Cases selected / run / pass / partial / fail / blocked / skipped.
- Exit criteria met (master-test-plan.md, Entry and exit): yes / no, per criterion.

## Results by requirement group
| Group | Run | Pass | Partial | Fail | Blocked | Skipped |
| --- | --- | --- | --- | --- | --- | --- |
| FR1 ... | | | | | | |

## Failures and defects
| Defect | Case | Severity (S1 to S4) | Description | Known gap or issue | Status |
| --- | --- | --- | --- | --- | --- |

## Deviations
Steps changed, cases skipped and why, anything that differs from the plan.

## Evidence
Location of the run folder, the raw log location if not committed, platform URLs.

## Sign-off
Runner, reviewer and date. The owner decides whether the exit criteria are met.
```
