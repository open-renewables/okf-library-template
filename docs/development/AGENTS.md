# Agent instructions: template development

This folder is used to build the OKF library template itself. It is removed when a
library is instantiated. Agents that author or consume a library's knowledge bundle
follow the root AGENTS.md instead.

## Where things are

| Path | Use it for | Rule |
| --- | --- | --- |
| `README.md` | Index of these paths and the work flow | Read first |
| `constraints.md` | The quality bar tools enforce | Never weaken it to make a change pass; propose an ADR instead |
| `conventions.md` | Judgement calls tools can't check | Follow it; cite it rather than restate it |
| `requirements/` | The SRS (`OKF Library Template - Software Requirements Spec.md`) and later PRDs | Owned by people: do not create or change a requirement's Status |
| `rfcs/` | Proposed design changes needing discussion | Open one when a design choice is contested |
| `adr/` | Decisions: the DDR (frozen series AD-, QA-, DR-) and `ADR-NNN-title.md` from ADR-001 | Never delete or renumber; supersede with a new ADR |
| `architecture/` | The SDD, stack report, diagrams and data model | Update in the same change as the code it describes |
| `plan/` | The current piece of work only: `SPEC.md`, `plan.md`, `todo.md` | Work from `todo.md`; tick items as done |
| `plan/archive/` | Finished work, moved together to `YYYY-MM-<feature>/` | Archive when the work ships |
| `testing/` | Test strategy, plans, fixtures, known gaps | Add a known gap rather than skip a test silently |
| `operations/` | Runbooks, rollback plans, postmortems | Follow the runbook for W-11, W-12 and recovery steps |

## Flow

1. Start only from a requirement with `Status: Accepted`.
2. If the design needs discussion, open an RFC; record each decision as an ADR, linked both ways with the RFC.
3. Write `plan/SPEC.md`, linking the requirement and referencing `conventions.md`, `constraints.md` and `testing/` instead of restating them.
4. Write `plan/plan.md` and `plan/todo.md`, then implement.
5. Before finishing: `uv run poe check` and `uv run poe test` pass with no change to `constraints.md`.
6. When the work ships, move the three plan files to `plan/archive/YYYY-MM-<feature>/` and ask the owner to set the requirement to `Done`.

## Boundaries

- `docs/` counts as tooling for the mixed-change rule: don't change `knowledge/` in the same pull request unless it is labelled `profile-migration`.
- Don't write requirements, change their Status, or accept an RFC; propose them for the owner.
- File names in `requirements/`, `architecture/` and `adr/` that existed before this folder keep their exact names.
