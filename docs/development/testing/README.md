# Testing

These files are written in build phase P1, when the tests and fixtures exist (owner decision, 25 October 2026).

- `strategy.md`: what is tested at which level (unit, fixture bundle, golden file, instantiation self-test, CI smoke) and why.
- `plan-<feature>.md`: a test plan for a feature where the SPEC needs one.
- `fixtures.md`: a catalogue of the fixture bundles in `tests/` and what each proves.
- `known-gaps.md`: behaviour not yet covered by an automated test, with the reason and the verification item (SDD §15) or plan that closes it.
- `performance.md`: the one-off timing of the validator on a generated 600-concept bundle (information; the gate is P2).
- `master-test-plan.md`: the acceptance level above the fixtures, run at P4 against scratch libraries and the pilot (objectives, environments, phases, entry and exit, defects, open decisions).
- `traceability-matrix.md`: every SRS criterion, SDD verification item, P2 "Done when" item and known gap mapped to `AT-<requirement>-nn` cases.
- `acceptance-test-cases.md`: the cases, each runnable by a person or any agent.
- `acceptance-templates.md` and `library-under-test.yaml`: the blank test case, run sheet, results report and run parameter file. Run records go in `runs/YYYY-MM-DD-<library>/`.

Limits (coverage, matrix) are in `../constraints.md`; style is in `../conventions.md`.
