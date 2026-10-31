"""Fixture bundles for this library's profile rules.

``fixtures/pass/<name>/knowledge/...`` must validate with no error. ``fixtures/fail/<code>/knowledge/...``
must raise exactly the finding code named by the folder. A fixture may overlay files of ``profile/`` by
holding its own ``profile/...`` files, for rules the library's profile does not exercise.
"""

import shutil
from pathlib import Path

import pytest
from okfprofile.config import load_profile
from okfprofile.report import Report
from okfprofile.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "library" / "fixtures"
FAIL = sorted(p.name for p in (FIXTURES / "fail").iterdir() if p.is_dir())
PASS = sorted(p.name for p in (FIXTURES / "pass").iterdir() if p.is_dir())


def run_fixture(fixture: Path, scratch: Path) -> Report:
    shutil.copytree(ROOT / "profile", scratch / "profile")
    if (fixture / "profile").is_dir():
        shutil.copytree(fixture / "profile", scratch / "profile", dirs_exist_ok=True)
    shutil.copytree(fixture / "knowledge", scratch / "knowledge")
    return validate_bundle(load_profile(scratch))


@pytest.mark.parametrize("code", FAIL)
def test_failing_fixture_raises_exactly_its_code(code: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "fail" / code, tmp_path)
    assert {f.code for f in report.findings} == {code}, report.human()


@pytest.mark.parametrize("name", PASS)
def test_passing_fixture_has_no_errors(name: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "pass" / name, tmp_path)
    assert report.errors == [], report.human()
