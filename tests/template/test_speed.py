"""Validation speed: 600 concepts in under 10 s (SDD section 12, constraints.md, known gap G8).

A small bundle is always generated to keep the generator honest. The 600-concept timing runs only when
``OKF_PERF=1`` (``uv run poe perf``, and the CI speed job), because wall-clock limits do not belong in the ordinary
test run.
"""

import os
import shutil
import time
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.cli import build_indexes_main, validate_main
from okfprofile.config import Profile, load_profile
from okfprofile.indexes import write_indexes
from okfprofile.registry import Registry, RegistryEntry, load_registry, save_registry
from okfprofile.scaffold import concept_text
from support import ROOT

LIMIT_SECONDS = 10.0
FULL_SIZE = 600
FOLDER = "example-group/example-category"


def generate(root: Path, count: int) -> Profile:
    """A scratch library holding the example bundle and ``count`` generated Items, with indexes and registry."""
    for name in ("profile", "knowledge"):
        shutil.copytree(ROOT / name, root / name)
    profile = load_profile(root)
    entries = dict(load_registry(root).entries)
    for number in range(1, count + 1):
        concept_id = f"{FOLDER}/generated-item-{number:04d}"
        uid = f"ITM-{number + 1:04d}"
        text = concept_text(profile, "Item", concept_id, uid, f"Generated item {number}", f"Generated item {number}.")
        target = profile.bundle_root / f"{concept_id}.md"
        target.write_text(text, encoding="utf-8", newline="\n")
        entries[uid] = RegistryEntry(concept_id, "Item", ())
    save_registry(root, Registry(entries))
    write_indexes(profile, load_bundle(profile.bundle_root, root))
    return profile


def test_a_generated_bundle_validates(tmp_path: Path) -> None:
    generate(tmp_path / "lib", 30)
    assert validate_main(["--root", str(tmp_path / "lib")]) == 0
    assert build_indexes_main(["--root", str(tmp_path / "lib"), "--check"]) == 0


@pytest.mark.skipif(os.environ.get("OKF_PERF") != "1", reason="timing runs only with OKF_PERF=1 (poe perf)")
def test_six_hundred_concepts_validate_in_under_ten_seconds(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    generate(tmp_path / "lib", FULL_SIZE)
    started = time.perf_counter()
    status = validate_main(["--root", str(tmp_path / "lib")])
    elapsed = time.perf_counter() - started
    with capsys.disabled():
        print(f"\nvalidate_profile: {FULL_SIZE + 4} concepts in {elapsed:.2f} s (limit {LIMIT_SECONDS:.0f} s)")
    assert status == 0
    assert elapsed < LIMIT_SECONDS
