"""The instantiation self-test (SDD W-10, FR6.3, FR6.5, FR6.2): the template instantiates for both platforms.

Each platform is instantiated once into a scratch folder from the answers files in ``instantiation/``; the tests
then check the result. ``setup_repo.py`` is not run here (it changes GitHub settings); ``test_setup_repo.py``
covers it against an in-memory GitHub. Nothing here may call a platform: the ``git-local`` run fails if it does.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from okfprofile.archive import build_archive, rebuild_problems
from okfprofile.cli import build_indexes_main, new_concept_main, validate_main
from okfprofile.config import load_profile
from okfprofile.init_cli import init_library_main
from okfprofile.instantiate import leftover_markers
from okfprofile.release import tag_digest
from okfprofile.release_cli import release_main
from okfprofile.revision_cli import write_revision_main
from okfprofile.site import build, compare_pages, docs_dir, installed
from okfprofile.skills_cli import check_skills_main
from support import ROOT, git
from test_instantiate import copy_template

PLATFORMS = ("github", "git-local")
ANSWERS = ROOT / "tests" / "template" / "instantiation"


@pytest.fixture(scope="module", params=PLATFORMS)
def instantiated(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[tuple[str, Path]]:
    """The template, instantiated for one platform from its answers file."""
    platform = request.param
    root = copy_template(tmp_path_factory.mktemp(platform) / "library")
    assert init_library_main(["--root", str(root), "--answers", str(ANSWERS / f"answers-{platform}.yaml")]) == 0
    yield platform, root


def copy_of(root: Path, tmp_path: Path) -> Path:
    return shutil.copytree(root, tmp_path / "work")


def test_template_only_files_are_gone_and_library_files_remain(instantiated: tuple[str, Path]) -> None:
    platform, root = instantiated
    for gone in ("CLAUDE.md", "docs", "tests/template", ".github/workflows/template-tests.yml"):
        assert not (root / gone).exists(), gone
    assert (root / "tests" / "library" / "test_fixtures.py").is_file()
    assert (root / "AGENTS.md").is_file() and "template-only" not in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert (root / ".github" / "CODEOWNERS").is_file()
    assert (root / ".github" / "ISSUE_TEMPLATE").exists() == (platform == "github")
    assert (root / ".github" / "labels.yml").exists() == (platform == "github")


def test_no_placeholder_remains(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    assert leftover_markers(root) == []


def test_the_answers_are_carried_into_the_files(instantiated: tuple[str, Path]) -> None:
    platform, root = instantiated
    answers = (ANSWERS / f"answers-{platform}.yaml").read_text(encoding="utf-8")
    login = "sample-owner" if platform == "github" else "local-owner"
    profile = load_profile(root)
    assert profile.platform == platform
    assert list(profile.maintainers) == [login]
    assert f"@{login}" in (root / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert profile.library_title in (root / "CITATION.cff").read_text(encoding="utf-8")
    assert f"on platform {platform}" in (root / "DECISIONS.md").read_text(encoding="utf-8")
    assert "name: " in answers


def test_the_chosen_licences_the_apache_text_and_the_notice_are_present(instantiated: tuple[str, Path]) -> None:
    platform, root = instantiated
    code = (root / "LICENSE").read_text(encoding="utf-8")
    assert (
        (code.startswith("Copyright") and "proprietary" in code)
        if platform == "github"
        else code.startswith("MIT License")
    )
    assert "Apache License" in (root / "LICENSE-template").read_text(encoding="utf-8")
    assert "Licensed under the Apache License" in (root / "NOTICE").read_text(encoding="utf-8")
    content = (root / "LICENSE-content").read_text(encoding="utf-8")
    assert ("CC-BY-SA-4.0" if platform == "github" else "CC-BY-4.0") in content


def test_the_library_validates_and_its_indexes_are_current(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    assert validate_main(["--root", str(root)]) == 0
    assert build_indexes_main(["--root", str(root), "--check"]) == 0


def test_the_librarys_skills_and_entry_point_pass_the_skill_checks(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    assert (root / ".agents" / "skills" / "use-bundle" / "SKILL.md").is_file()
    assert check_skills_main(["--root", str(root)]) == 0
    assert "docs/development" not in (root / "AGENTS.md").read_text(encoding="utf-8")


def test_the_lock_still_matches_the_renamed_project(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    if shutil.which("uv") is None:
        pytest.skip("uv is not installed")
    done = subprocess.run(["uv", "lock", "--locked"], cwd=root, capture_output=True, check=False, text=True)  # noqa: S607
    assert done.returncode == 0, done.stderr


def test_the_librarys_own_tests_still_run_without_the_template_tests(
    instantiated: tuple[str, Path], tmp_path: Path
) -> None:
    _platform, root = instantiated
    work = copy_of(root, tmp_path)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "scripts")}
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/library", "-q", "-p", "no:cacheprovider"],
        cwd=work,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    assert done.returncode == 0, done.stdout[-2000:]
    assert " passed" in done.stdout


def test_a_new_concept_of_the_primary_type_validates_after_the_indexes_are_built(
    instantiated: tuple[str, Path], tmp_path: Path
) -> None:
    _platform, root = instantiated
    work = copy_of(root, tmp_path)
    assert (
        new_concept_main(["--root", str(work), "Item", "example-group/example-category/second", "--title", "Second"])
        == 0
    )
    assert build_indexes_main(["--root", str(work)]) == 0
    assert validate_main(["--root", str(work)]) == 0


def test_a_git_local_library_makes_a_release_without_calling_a_platform(
    instantiated: tuple[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    platform, root = instantiated
    if platform != "git-local":
        pytest.skip("only the git-local library is released locally")

    def refuse(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a git-local run must not call a platform")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    work = copy_of(root, tmp_path)
    git(work, "init", "-q", "-b", "main")
    git(work, "config", "user.email", "lou@example.org")
    git(work, "config", "user.name", "Lou Owner")
    git(work, "add", "-A")
    git(
        work,
        "commit",
        "-q",
        "-m",
        "Instantiate the library",
        "-m",
        "Full-Review: yes",
        when="2026-11-01T10:00:00+00:00",
    )
    assert write_revision_main(["--root", str(work), "--commit"]) == 0
    for concept in work.glob("knowledge/**/example-item.md"):
        text = concept.read_text(encoding="utf-8")
        assert "author @local-owner · self-approved (owner)" in text
        assert "· full-review" in text
    out = tmp_path / "dist"
    assert release_main(["v0.0.1", "--root", str(work), "--out", str(out)]) == 0
    manifest = json.loads((out / "local-library-v0.0.1.manifest.json").read_text(encoding="utf-8"))
    assert manifest["platform"] == "git-local"
    digest = tag_digest(work, "v0.0.1")
    assert digest == manifest["archive"]["tar_sha256"]
    assert hashlib.sha256(build_archive(load_profile(work), "v0.0.1", "v0.0.1").tar).hexdigest() == digest
    assert rebuild_problems(load_profile(work), manifest, "v0.0.1") == []


def test_the_librarys_site_config_names_the_library_and_links_only_where_there_is_a_repository(
    instantiated: tuple[str, Path],
) -> None:
    platform, root = instantiated
    config = (root / "mkdocs.yml").read_text(encoding="utf-8")
    title = "Sample library" if platform == "github" else "Local library"
    assert f'site_name: "{title}"' in config
    if platform == "github":
        assert "repo_url: https://github.com/example-org/sample-library" in config
        assert "https://github.com/example-org/sample-library/issues/new/choose" in config
        assert "edit_uri: edit/main/knowledge/" in config
    else:
        for dead in ("repo_url", "edit_uri", "social", "content.action.edit", "issues/new"):
            assert dead not in config, dead
        assert "extra:" in config


def test_the_librarys_site_builds_strict_from_the_bundle_in_place(
    instantiated: tuple[str, Path], tmp_path: Path
) -> None:
    """W-10 step 4 (known gap G25). Skipped where the site group is not installed; CI installs it."""
    if not installed("mkdocs"):
        pytest.skip("mkdocs is not installed (uv sync --group site-mkdocs)")
    _platform, root = instantiated
    before = sorted(p.relative_to(root).as_posix() for p in (root / "knowledge").rglob("*"))
    out = build(root, "mkdocs", tmp_path / "site")
    assert compare_pages(docs_dir(root), out).ok
    assert sorted(p.relative_to(root).as_posix() for p in (root / "knowledge").rglob("*")) == before


def test_a_template_name_left_in_the_site_config_is_reported(instantiated: tuple[str, Path], tmp_path: Path) -> None:
    _platform, root = instantiated
    work = copy_of(root, tmp_path)
    config = work / "mkdocs.yml"
    config.write_text(config.read_text(encoding="utf-8") + "# see okf-library-template\n", encoding="utf-8")
    assert leftover_markers(work) == ["mkdocs.yml: okf-library-template"]
