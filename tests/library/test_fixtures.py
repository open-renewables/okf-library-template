"""Fixture bundles for this library's profile rules.

``fixtures/pass/<name>/knowledge/...`` must validate with no error. ``fixtures/fail/<code>/knowledge/...``
must raise exactly the finding code named by the folder. A fixture may overlay files of ``profile/`` by
holding its own ``profile/...`` files, for rules the library's profile does not exercise. A fixture with a
``base/`` folder (``base/knowledge/...`` and ``base/profile/uid-registry.yaml``) is validated against that base,
and an empty file named ``approved-move`` marks the change as carrying the approved-move label.
"""

import shutil
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.checks import BaseState
from okfprofile.config import load_profile
from okfprofile.registry import load_registry
from okfprofile.report import Report
from okfprofile.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "library" / "fixtures"
FAIL = sorted(p.name for p in (FIXTURES / "fail").iterdir() if p.is_dir())
PASS = sorted(p.name for p in (FIXTURES / "pass").iterdir() if p.is_dir())


def load_base(fixture: Path, scratch: Path, profile_root: Path) -> BaseState | None:
    base = fixture / "base"
    if not base.is_dir():
        return None
    shutil.copytree(profile_root / "profile", scratch / "base" / "profile")
    shutil.copytree(base / "profile", scratch / "base" / "profile", dirs_exist_ok=True)
    shutil.copytree(base / "knowledge", scratch / "base" / "knowledge")
    concepts = load_bundle(scratch / "base" / "knowledge", scratch / "base")
    return BaseState(concepts, load_registry(scratch / "base"))


def run_fixture(fixture: Path, scratch: Path) -> Report:
    shutil.copytree(ROOT / "profile", scratch / "profile")
    if (fixture / "profile").is_dir():
        shutil.copytree(fixture / "profile", scratch / "profile", dirs_exist_ok=True)
    shutil.copytree(fixture / "knowledge", scratch / "knowledge")
    base = load_base(fixture, scratch, ROOT)
    return validate_bundle(load_profile(scratch), base, approved_move=(fixture / "approved-move").exists())


@pytest.mark.parametrize("code", FAIL)
def test_failing_fixture_raises_exactly_its_code(code: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "fail" / code, tmp_path)
    assert {f.code for f in report.findings} == {code}, report.human()


@pytest.mark.parametrize("name", PASS)
def test_passing_fixture_has_no_errors(name: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "pass" / name, tmp_path)
    assert report.errors == [], report.human()
