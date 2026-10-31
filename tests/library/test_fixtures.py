"""Fixture bundles for this library's profile rules.

``fixtures/pass/<name>/knowledge/...`` must validate with no error. ``fixtures/fail/<code>/knowledge/...``
must raise exactly the finding code named by the folder.

A fixture may also hold:

- ``profile/...``: files that overlay the library's ``profile/``, for rules the profile does not exercise;
- ``base/knowledge/...`` and ``base/profile/uid-registry.yaml``: the repository at the base commit;
- ``change.json``: a change proposal (``paths``, ``labels``, ``author``, ``head_sha``, ``reviews``, ...);
- ``CODEOWNERS``: directory owners;
- ``no-indexes``: an empty file; without it, missing ``index.md`` files are generated before validation.
"""

import shutil
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.changes import ChangeContext
from okfprofile.checks import BaseState
from okfprofile.config import load_profile
from okfprofile.indexes import write_indexes
from okfprofile.registry import load_registry
from okfprofile.report import Report
from okfprofile.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "library" / "fixtures"
FAIL = sorted(p.name for p in (FIXTURES / "fail").iterdir() if p.is_dir())
PASS = sorted(p.name for p in (FIXTURES / "pass").iterdir() if p.is_dir())


def load_base(fixture: Path, scratch: Path) -> BaseState | None:
    base = fixture / "base"
    if not base.is_dir():
        return None
    shutil.copytree(ROOT / "profile", scratch / "base" / "profile")
    shutil.copytree(base / "profile", scratch / "base" / "profile", dirs_exist_ok=True)
    shutil.copytree(base / "knowledge", scratch / "base" / "knowledge")
    concepts = load_bundle(scratch / "base" / "knowledge", scratch / "base")
    return BaseState(concepts, load_registry(scratch / "base"))


def run_fixture(fixture: Path, scratch: Path) -> Report:
    shutil.copytree(ROOT / "profile", scratch / "profile")
    if (fixture / "profile").is_dir():
        shutil.copytree(fixture / "profile", scratch / "profile", dirs_exist_ok=True)
    shutil.copytree(fixture / "knowledge", scratch / "knowledge")
    if (fixture / "CODEOWNERS").is_file():
        (scratch / ".github").mkdir()
        shutil.copy2(fixture / "CODEOWNERS", scratch / ".github" / "CODEOWNERS")
    profile = load_profile(scratch)
    if not (fixture / "no-indexes").exists():
        write_indexes(profile, load_bundle(profile.bundle_root, scratch), only_missing=True)
    change = ChangeContext.from_file(fixture / "change.json") if (fixture / "change.json").exists() else None
    return validate_bundle(profile, load_base(fixture, scratch), change)


@pytest.mark.parametrize("code", FAIL)
def test_failing_fixture_raises_exactly_its_code(code: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "fail" / code, tmp_path)
    assert {f.code for f in report.findings} == {code}, report.human()


@pytest.mark.parametrize("name", PASS)
def test_passing_fixture_has_no_errors(name: str, tmp_path: Path) -> None:
    report = run_fixture(FIXTURES / "pass" / name, tmp_path)
    assert report.errors == [], report.human()
