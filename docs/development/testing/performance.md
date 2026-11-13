# Validation speed

Information only. The constraint (600 concepts in under 10 s locally; SDD §12, [constraints.md](../constraints.md)) is timed as a gate in P2.

## Measurement (2026-11-01, build phase P1)

| Item | Value |
| --- | --- |
| Bundle | 600 generated Items in 12 groups of 10 categories (5 per category), plus the example bundle: 604 concept files |
| Machine | Windows 11 Home, one local run, warm disk cache, Python 3.12 via `uv run` |
| `validate_profile.py` (checks 1 to 6, whole bundle) | 2.05 to 2.28 s over three runs |
| `build_indexes.py --check` | 1.23 to 1.27 s over three runs |
| Target | Under 10 s |

Both figures are wall-clock for the whole command and include `uv run` start-up and interpreter import time. The target is met with a wide margin on this machine.

## Method

The bundle was built outside the repository in a copy of `scripts/`, `profile/` and `knowledge/`: a throwaway generator (kept out of the repo) added vocabulary values and called `okfprofile.scaffold.create_concept` 600 times, then `build_indexes.py` wrote the indexes. Creating the concepts took 246 s because `create_concept` reloads the bundle for each concept; that is the scaffolder's cost, not the validator's, and is not a concern for authoring one concept at a time.

The copy still held the shipped `example-item`, whose tags are not in the generated vocabularies, so the timed validation reported two `OKF406` errors. The checks still ran over every file; the figure is not affected.

Not covered: other machines and systems (see [known-gaps.md](known-gaps.md), G1), a cold cache, and the 3-minute `validate` job target, which needs CI (P2).

## Site build (2026-11-12, build phase P3)

Information only; recorded, not gated (P3 plan OD-8). SDD §12 sets under 2 minutes per builder for 600 concepts.

| Item | Value |
| --- | --- |
| Bundle | The generator of `tests/template/test_speed.py`: 600 generated Items plus the example bundle, 604 concept files |
| Machine | Windows 11 Home, one local run, warm disk cache, Python 3.12 |
| MkDocs 1.6.1 + Material 9.7.7, strict | 7.66 s |
| Zensical 0.1.1 | 4.33 s |
| Target | Under 120 s per builder |

Run again with `OKF_PERF=1 uv run pytest tests/template/test_speed.py -s -k site_build`. The Linux CI figure is added when `site.yml` has run on the template.
