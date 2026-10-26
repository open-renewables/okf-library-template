# Testing

These files are written in build phase P1, when the tests and fixtures exist (owner decision, 25 October 2026).

- `strategy.md`: what is tested at which level (unit, fixture bundle, golden file, instantiation self-test, CI smoke) and why.
- `plan-<feature>.md`: a test plan for a feature where the SPEC needs one.
- `fixtures.md`: a catalogue of the fixture bundles in `tests/` and what each proves.
- `known-gaps.md`: behaviour not yet covered by an automated test, with the reason and the verification item (SDD §15) or plan that closes it.

Limits (coverage, matrix) are in `../constraints.md`; style is in `../conventions.md`.
