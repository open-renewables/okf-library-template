"""The instantiation self-test (SDD W-10, FR6.3, FR6.5, FR6.2): the template instantiates for both platforms.

Each platform is instantiated once into a scratch folder from the answers files in ``instantiation/``; the tests
then check the result. ``setup_repo.py`` is not run here (it changes GitHub settings); ``test_setup_repo.py``
covers it against an in-memory GitHub. Nothing here may call a platform: the ``git-local`` run fails if it does.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from okfprofile.archive import build_archive, rebuild_problems
from okfprofile.bundle import load_bundle
from okfprofile.checks import check_indexes
from okfprofile.cli import build_indexes_main, new_concept_main, validate_main
from okfprofile.config import load_profile
from okfprofile.document import parse_yaml
from okfprofile.indexes import read_header
from okfprofile.init_cli import init_library_main
from okfprofile.instantiate import Answers, leftover_markers, root_index_header
from okfprofile.release import tag_digest
from okfprofile.release_cli import release_main
from okfprofile.revision_cli import write_revision_main
from okfprofile.site import build, compare_pages, docs_dir, generator, installed
from okfprofile.skills_cli import check_skills_main
from okfprofile.supply_cli import audit_command, audit_main
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
    for gone in ("CLAUDE.md", "docs/development", "tests/template", ".github/workflows/template-tests.yml"):
        assert not (root / gone).exists(), gone
    assert (root / "tests" / "library" / "test_fixtures.py").is_file()
    assert (root / "AGENTS.md").is_file() and "template-only" not in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert (root / ".github" / "CODEOWNERS").is_file()
    assert (root / ".github" / "ISSUE_TEMPLATE").exists() == (platform == "github")
    assert (root / ".github" / "labels.yml").exists() == (platform == "github")


def test_no_placeholder_remains(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    assert leftover_markers(root) == []


def test_governance_and_readme_have_no_template_text_or_unresolved_placeholder(
    instantiated: tuple[str, Path],
) -> None:
    platform, root = instantiated
    governance = (root / "GOVERNANCE.md").read_text(encoding="utf-8")
    assert "{maintainer}" not in governance and "{contact}" not in governance
    assert ("Sam Owner (@sample-owner)" if platform == "github" else "Lou Owner") in governance
    assert ("sam@example.org" if platform == "github" else "lou@example.org") in governance
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "{" not in readme and "okf-library-template" not in readme


def test_the_issue_chooser_governance_link_resolves_in_the_library(instantiated: tuple[str, Path]) -> None:
    platform, root = instantiated
    config = root / ".github" / "ISSUE_TEMPLATE" / "config.yml"
    if platform == "git-local":
        assert not config.exists()
        return
    text = config.read_text(encoding="utf-8")
    assert "https://github.com/example-org/sample-library/blob/main/GOVERNANCE.md" in text
    assert (root / "GOVERNANCE.md").is_file()


def test_the_licence_map_matches_the_licence_files_present(instantiated: tuple[str, Path]) -> None:
    _platform, root = instantiated
    readme = (root / "README.md").read_text(encoding="utf-8")
    present = {name for name in ("LICENSE", "LICENSE-content", "LICENSE-template", "NOTICE") if (root / name).exists()}
    mentioned = {n for n in ("LICENSE-content", "LICENSE-template", "NOTICE") if f"`{n}`" in readme or n in readme}
    assert {"LICENSE", "LICENSE-content", "NOTICE"} <= present
    assert mentioned <= present
    assert ("LICENSE-template" in present) == ("proprietary" in readme or "MIT" in readme)


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


def test_the_audit_runs_in_an_instantiated_library_without_constraints_md(instantiated: tuple[str, Path]) -> None:
    """Known gap G37: the audit used to read `docs/development/constraints.md`, which a library does not have."""
    _platform, root = instantiated
    assert not (root / "docs" / "development").exists()
    assert audit_command(root) == ["uvx", "pip-audit", "--disable-pip", "--no-deps", "-r", "requirements/dev.txt"]
    assert audit_main(["--root", str(root), "--print-command"]) == 0


def test_the_chosen_site_generator_is_in_the_profile_and_the_readme(instantiated: tuple[str, Path]) -> None:
    platform, root = instantiated
    chosen = "mkdocs" if platform == "github" else "zensical"  # the answers files choose one each
    assert generator(root) == chosen == load_profile(root).site_generator
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert f"The site is built with {chosen.title()}" in readme and f"uv sync --group site-{chosen}" in readme
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "site-mkdocs" in pyproject and "site-zensical" in pyproject  # both groups stay, so the lock still matches


def test_the_librarys_site_builds_strict_from_the_bundle_in_place(
    instantiated: tuple[str, Path], tmp_path: Path
) -> None:
    """W-10 step 4 (known gap G25), with the generator the answers chose. Skipped where its group is not installed."""
    _platform, root = instantiated
    chosen = generator(root)
    if not installed(chosen):
        pytest.skip(f"{chosen} is not installed (uv sync --group site-{chosen})")
    before = sorted(p.relative_to(root).as_posix() for p in (root / "knowledge").rglob("*"))
    out = build(root, chosen, tmp_path / "site")
    assert compare_pages(docs_dir(root), out).ok
    assert sorted(p.relative_to(root).as_posix() for p in (root / "knowledge").rglob("*")) == before


def test_a_template_name_left_in_the_site_config_is_reported(instantiated: tuple[str, Path], tmp_path: Path) -> None:
    _platform, root = instantiated
    work = copy_of(root, tmp_path)
    config = work / "mkdocs.yml"
    config.write_text(config.read_text(encoding="utf-8") + "# see okf-library-template\n", encoding="utf-8")
    assert leftover_markers(work) == ["mkdocs.yml: okf-library-template"]


def test_the_root_index_carries_the_bundle_metadata(instantiated: tuple[str, Path]) -> None:
    """OKF v0.3 §8.1 (RFC-002 D5): the root index names the library and its content licence, and keeps them."""
    platform, root = instantiated
    header = read_header((root / "knowledge" / "index.md").read_text(encoding="utf-8"), root=True)
    assert header.problem is None
    assert header.values is not None
    answers, _ = parse_yaml((ANSWERS / f"answers-{platform}.yaml").read_text(encoding="utf-8"))
    assert header.values["okf_version"] == "0.3"
    assert header.values["title"] == answers["title"]
    assert header.values["license"] == answers.get("content_licence", "CC-BY-4.0")
    profile = load_profile(root)
    assert check_indexes(profile, load_bundle(profile.bundle_root, root)) == []


def test_a_proprietary_content_licence_is_a_licence_ref() -> None:
    answers = Answers(
        platform="git-local",
        name="x",
        title="X library",
        description="d",
        login="o",
        email="o@example.org",
        content_licence="proprietary",
    )
    assert "license: LicenseRef-proprietary\n" in root_index_header(answers, "0.3")


def _guide_pages(root: Path) -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((root / "docs" / "guide").glob("*.md"))}


def test_the_user_guide_is_kept_as_the_answers_chose(instantiated: tuple[str, Path]) -> None:
    """OD-24: `github` answers morph the guide (the default), `git-local` answers copy it."""
    platform, root = instantiated
    pages = _guide_pages(root)
    assert {"index.md", "getting-started.md", "maintaining.md", "customising.md", "reference.md"} <= set(pages)
    assert {"finding-codes.md", "runbooks.md"} <= set(pages)
    for name, text in pages.items():
        assert "<!-- template-only" not in text, name
        assert "<!-- platform:" not in text, name
        assert "docs/development" not in text, name
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
            if "://" not in target:
                assert (root / "docs" / "guide" / target).resolve().exists(), f"{name}: {target}"
    if platform == "github":
        assert "## Instantiate a library" not in pages["runbooks.md"]
        assert "## Promote a library to public" in pages["runbooks.md"]
        assert "conventions.md" in pages
        assert "## How this library was created" in pages["getting-started.md"]
        assert "Sample library was created from the OKF library template, release v" in pages["getting-started.md"]
        assert "Choose how the library runs" not in pages["getting-started.md"]
        assert "With `git-local`" not in pages["maintaining.md"]
        assert "On GitHub:" in pages["maintaining.md"]
        assert "[This library's conventions](conventions.md)" in pages["index.md"]
    else:
        assert "## Instantiate a library" in pages["runbooks.md"]
        assert "conventions.md" not in pages
        assert "Choose how the library runs" in pages["getting-started.md"]
        assert "With `git-local`" in pages["maintaining.md"] and "On GitHub:" in pages["maintaining.md"]
    decisions = (root / "DECISIONS.md").read_text(encoding="utf-8")
    assert ("made the library's own" if platform == "github" else "copied as the template wrote it") in decisions
    assert "docs/guide/index.md" in (root / "README.md").read_text(encoding="utf-8")
    assert "`docs/guide/`" in (root / "AGENTS.md").read_text(encoding="utf-8")


def test_the_user_guide_can_be_removed(tmp_path: Path) -> None:
    root = copy_template(tmp_path / "library")
    answers = tmp_path / "answers.yaml"
    answers.write_text(
        (ANSWERS / "answers-git-local.yaml").read_text(encoding="utf-8").replace("guide: copy", "guide: remove"),
        encoding="utf-8",
    )
    assert init_library_main(["--root", str(root), "--answers", str(answers)]) == 0
    assert not (root / "docs").exists()
    assert "docs/guide" not in (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/guide" not in (root / "README.md").read_text(encoding="utf-8")
    assert "User guide: removed." in (root / "DECISIONS.md").read_text(encoding="utf-8")
