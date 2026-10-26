# Template development documentation

This folder records how the OKF library template itself is specified, designed, built, tested and operated. It is template-only: `init_library.py` removes the whole of `docs/` when a library is instantiated, as it did the former `design/` folder (DDR QA-66, QA-67). Agents read `AGENTS.md` in this folder before working here.

For the mixed-change rule (SDD AD-18), `docs/` counts as tooling: a pull request that changes `docs/` and `knowledge/` together fails unless it is labelled `profile-migration` (QA-70).

## Paths

| Path | Holds | Naming | Owner |
| --- | --- | --- | --- |
| [`constraints.md`](constraints.md) | The measured quality bar that tools enforce: lock, lint, types, tests, coverage, validation, site build, security | — | Maintainer. Never weakened to make a change pass; a change to the bar needs an ADR |
| [`conventions.md`](conventions.md) | Judgement calls tools can't check: design, code, module layout, tests, docs, git | — | Maintainer |
| [`AGENTS.md`](AGENTS.md) | Instructions for agents working on the template | — | Maintainer |
| [`requirements/`](requirements/README.md) | The SRS and, after v1.0.0, feature PRDs, briefs and user stories | `<feature>-prd.md`; the SRS keeps its exact name | People only |
| [`rfcs/`](rfcs/README.md) | Requests for change that need discussion | `RFC-NNN-title.md` until v1.0.0; then GitHub issues labelled `rfc`, with earlier files kept as history | Proposer; accepted by the maintainer |
| [`adr/`](adr/README.md) | The DDR (frozen series AD-, QA-, DR-) and new architecture decision records | `ADR-NNN-title.md` from ADR-001; the DDR keeps its exact name | Maintainer |
| [`architecture/`](architecture/README.md) | The SDD, the stack report, diagrams and data model | Exact existing names; new files lowercase-hyphenated | Maintainer |
| [`plan/`](plan/README.md) | The current piece of work only: `SPEC.md`, `plan.md`, `todo.md` | Fixed names | Whoever does the work |
| [`plan/archive/`](plan/archive/README.md) | Finished work, the three plan files moved together | `YYYY-MM-<feature>/` | — |
| [`testing/`](testing/README.md) | Test strategy, test plans, fixture catalogue, known gaps | Lowercase-hyphenated | Maintainer |
| [`operations/`](operations/README.md) | Runbooks, rollback plans, postmortems | `runbook-<task>.md`, `rollback-<change>.md`, `postmortem-YYYY-MM-DD-<slug>.md` | Maintainer |

## From requirement to shipped work

1. A requirement in `requirements/` reaches `Status: Accepted`. Only people set a status.
2. If the design needs discussion, an RFC is opened in `rfcs/`.
3. Each decision is recorded as an ADR in `adr/`, linked both ways with its RFC.
4. `plan/SPEC.md` links its requirement and references `conventions.md`, `constraints.md` and `testing/` instead of restating them.
5. `plan/plan.md` and `plan/todo.md` break the SPEC into steps.
6. The work is built; `uv run poe check` and `uv run poe test` pass against an unchanged `constraints.md`.
7. When the work ships, `SPEC.md`, `plan.md` and `todo.md` move together to `plan/archive/YYYY-MM-<feature>/`, and the requirement's status is set to `Done`.

Every folder has a short `README.md` stating its purpose and naming rules.
