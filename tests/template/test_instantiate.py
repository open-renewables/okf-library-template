"""Instantiating a library from a copy of the template (plan step 9, FR6.2, FR6.3, FR5.5, W-01)."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from okfprofile.cli import build_indexes_main, validate_main
from okfprofile.config import load_profile
from okfprofile.init_cli import init_library_main, questionnaire
from okfprofile.instantiate import (
    Answers,
    InitError,
    instantiate,
    leftover_markers,
    load_answers,
    parse_answers,
    rewrite_profile,
    strip_template_block,
)
from okfprofile.registry import load_registry
from support import ROOT

ANSWERS = ROOT / "tests" / "template" / "instantiation"


def base_answers(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "platform": "github",
        "name": "sample-library",
        "title": "Sample library",
        "description": "A sample.",
        "maintainer": {"login": "sample-owner", "name": "Sam Owner", "email": "sam@example.org"},
        "repository": "https://github.com/example-org/sample-library",
        "year": 2026,
    }
    data.update(overrides)
    return data


SKIPPED_FOLDERS = {".git", ".idea", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def copy_template(destination: Path) -> Path:
    """Copy the working tree (tracked and new files) without ``.git``, IDE files, virtual environments or caches."""
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        parts = path.relative_to(ROOT).parts
        if SKIPPED_FOLDERS & set(parts) or any(part.startswith(".venv") for part in parts):
            continue
        target = destination / Path(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    return destination


@pytest.fixture
def template(tmp_path: Path) -> Path:
    """A copy of the template to instantiate."""
    return copy_template(tmp_path / "copy")


def run(template: Path, **overrides: Any) -> Answers:
    answers = parse_answers(base_answers(**overrides))
    instantiate(template, answers)
    return answers


def test_valid_answers_get_their_defaults() -> None:
    answers = parse_answers(base_answers())
    assert (answers.content_licence, answers.code_licence, answers.keep_examples, answers.keep_tests) == (
        "CC-BY-4.0",
        "Apache-2.0",
        True,
        False,
    )
    assert answers.holder == "Sam Owner"
    assert parse_answers(base_answers(licence_holder="Org")).holder == "Org"
    assert parse_answers(base_answers(maintainer={"login": "x", "email": "x@example.org"})).holder == "x"
    assert parse_answers(base_answers(title="")).title == "Sample Library"
    assert parse_answers(base_answers(description="")).description == "An OKF knowledge library."


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"platform": "gitlab"}, "platform must be one of"),
        ({"name": "Bad Name"}, "name must be lower case"),
        ({"name": ""}, "name must be lower case"),
        ({"maintainer": {"login": "", "email": "a@b.org"}}, "maintainer.login"),
        ({"maintainer": {"login": "a", "email": "not-an-email"}}, "maintainer.email"),
        ({"maintainer": "alice"}, "maintainer.login"),
        ({"content_licence": "GPL-3.0"}, "content_licence must be one of"),
        ({"code_licence": "GPL-3.0"}, "code_licence must be one of"),
        ({"keep_examples": "yes"}, "keep_examples"),
        ({"keep_tests": 1}, "keep_tests"),
        ({"year": "soon"}, "year must be a number"),
        ({"surprise": 1}, "unknown answer 'surprise'"),
    ],
)
def test_invalid_answers_are_all_reported(override: dict[str, Any], fragment: str) -> None:
    with pytest.raises(InitError) as caught:
        parse_answers(base_answers(**override))
    assert any(fragment in problem for problem in caught.value.problems)


def test_several_problems_are_listed_together() -> None:
    with pytest.raises(InitError) as caught:
        parse_answers({"platform": "x", "name": "Bad"})
    assert len(caught.value.problems) >= 4


def test_answers_must_be_a_mapping_and_the_file_must_read(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="mapping"):
        parse_answers(["a"])
    with pytest.raises(InitError, match="cannot read"):
        load_answers(tmp_path / "missing.yaml")
    broken = tmp_path / "bad.yaml"
    broken.write_text("a: [unclosed\n", encoding="utf-8")
    with pytest.raises(InitError, match="invalid YAML"):
        load_answers(broken)
    assert load_answers(ANSWERS / "answers-github.yaml").platform == "github"
    assert load_answers(ANSWERS / "answers-git-local.yaml").code_licence == "MIT"


def test_a_github_library_is_personalised_and_still_validates(template: Path) -> None:
    answers = run(template, content_licence="CC-BY-SA-4.0", code_licence="proprietary", licence_holder="Example Org")
    profile = load_profile(template)
    assert (profile.name, profile.library_name, profile.library_title, profile.platform) == (
        "sample-library",
        "sample-library",
        "Sample library",
        "github",
    )
    assert profile.maintainers == {"sample-owner": ("sam@example.org",)}
    assert profile.rules.revision_token == "github-token"  # noqa: S105 - a setting name, not a secret
    assert "@sample-owner" in (template / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "richard-gledhill" not in (template / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "example-org/sample-library/blob/main/GOVERNANCE.md" in (
        template / ".github" / "ISSUE_TEMPLATE" / "config.yml"
    ).read_text(encoding="utf-8")
    assert 'name = "sample-library"' in (template / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "LicenseRef-Proprietary"' in (template / "pyproject.toml").read_text(encoding="utf-8")
    assert 'addopts = ""' in (template / "pyproject.toml").read_text(encoding="utf-8")
    assert "fail_under" not in (template / "pyproject.toml").read_text(encoding="utf-8")
    assert answers.holder == "Example Org"
    assert leftover_markers(template) == []
    assert validate_main(["--root", str(template)]) == 0
    assert build_indexes_main(["--root", str(template), "--check"]) == 0


def test_template_only_files_are_removed_and_library_files_kept(template: Path) -> None:
    run(template)
    for gone in ("CLAUDE.md", "docs", "tests/template"):
        assert not (template / gone).exists(), gone
    assert (template / "tests" / "library").is_dir()
    assert (template / ".github" / "labels.yml").is_file()
    assert "template-only" not in (template / "AGENTS.md").read_text(encoding="utf-8")
    assert (template / "NOTICE").read_text(encoding="utf-8").startswith("OKF library template")


def test_licence_files_follow_the_choices(template: Path) -> None:
    apache = (template / "LICENSE").read_text(encoding="utf-8")
    run(template)
    assert (template / "LICENSE").read_text(encoding="utf-8") == apache
    assert not (template / "LICENSE-template").exists()
    content = (template / "LICENSE-content").read_text(encoding="utf-8")
    assert "CC-BY-4.0" in content and "creativecommons.org/licenses/by/4.0" in content
    assert "Attribution 4.0 International" in content and "Section 1 -- Definitions." in content
    assert not (template / "licences").exists()
    run(template, code_licence="MIT", licence_holder="Example Org")
    mit = (template / "LICENSE").read_text(encoding="utf-8")
    assert mit.startswith("MIT License\n\nCopyright (c) 2026 Example Org")
    assert (template / "LICENSE-template").read_text(encoding="utf-8") == apache
    run(template, code_licence="proprietary", content_licence="proprietary")
    assert "All rights reserved" in (template / "LICENSE").read_text(encoding="utf-8")
    assert "proprietary" in (template / "LICENSE-content").read_text(encoding="utf-8")
    shutil.copytree(ROOT / "licences", template / "licences")  # a rerun with a new choice needs the folder back
    run(template, code_licence="Apache-2.0", content_licence="CC0-1.0")
    assert (template / "LICENSE").read_text(encoding="utf-8") == apache
    assert not (template / "LICENSE-template").exists()
    cc0 = (template / "LICENSE-content").read_text(encoding="utf-8")
    assert "CC0-1.0" in cc0 and "CC0 1.0 Universal" in cc0


def test_the_readme_citation_and_decision_record_name_the_library(template: Path) -> None:
    run(template, code_licence="MIT", content_licence="CC-BY-SA-4.0")
    readme = (template / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Sample library\n\nA sample.\n")
    assert "| `knowledge/` | CC-BY-SA-4.0" in readme and "| Code and changes by the owner | MIT" in readme
    citation = (template / "CITATION.cff").read_text(encoding="utf-8")
    assert 'title: "Sample library"' in citation and "license: CC-BY-SA-4.0" in citation
    assert 'repository-code: "https://github.com/example-org/sample-library"' in citation
    decisions = (template / "DECISIONS.md").read_text(encoding="utf-8")
    assert "| DR-01 |" in decisions and "Instantiated from okf-library-template v0.1.0 on platform github" in decisions
    assert "code licence MIT" in decisions


def test_a_git_local_library_has_no_platform_files(template: Path) -> None:
    run(template, platform="git-local", repository="")
    assert load_profile(template).platform == "git-local"
    github = sorted(p.relative_to(template).as_posix() for p in (template / ".github").rglob("*") if p.is_file())
    assert github == [".github/CODEOWNERS"]
    assert validate_main(["--root", str(template)]) == 0


def test_without_a_repository_the_issue_chooser_loses_its_link(template: Path) -> None:
    run(template, repository="")
    assert (template / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(
        encoding="utf-8"
    ) == "blank_issues_enabled: false\n"


def test_running_twice_with_the_same_answers_changes_nothing(template: Path) -> None:
    answers = parse_answers(base_answers(code_licence="MIT"))
    instantiate(template, answers)
    again = instantiate(template, answers)
    assert (again.changed, again.removed) == ([], [])


def test_dropping_the_examples_removes_them_from_the_registry_and_the_indexes(template: Path) -> None:
    run(template, keep_examples=False)
    assert not (template / "knowledge" / "example-group").exists()
    registry = load_registry(template)
    assert all(not entry.path.startswith("example-group/") for entry in registry.entries.values())
    assert len(registry.entries) == 3
    root_index = (template / "knowledge" / "index.md").read_text(encoding="utf-8")
    assert "Sample library" in root_index and "example-group" not in root_index
    assert validate_main(["--root", str(template)]) == 0


def test_keeping_the_template_tests_keeps_the_coverage_gate(template: Path) -> None:
    run(template, keep_tests=True)
    assert (template / "tests" / "template").is_dir()
    assert "fail_under" in (template / "pyproject.toml").read_text(encoding="utf-8")


def test_a_folder_that_is_not_a_template_copy_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InitError, match="does not look like a copy of the template"):
        instantiate(tmp_path, parse_answers(base_answers()))


def test_a_profile_that_lost_its_placeholders_is_refused() -> None:
    with pytest.raises(InitError, match="cannot find the profile name"):
        rewrite_profile("platform: github\n", parse_answers(base_answers()))


def test_the_template_block_is_stripped_from_agents() -> None:
    text = "# Agent instructions\n\n<!-- template-only:start -->\n> Building the template?\n<!-- template-only:end -->\n\nBody.\n"
    assert strip_template_block(text) == "# Agent instructions\n\nBody.\n"
    assert strip_template_block("no block\n") == "no block\n"


def test_leftovers_are_found_outside_the_places_that_may_name_the_template(template: Path) -> None:
    run(template)
    (template / "README.md").write_text("see open-renewables\n", encoding="utf-8")
    (template / "knowledge" / "note.md").write_text("by richard-gledhill\n", encoding="utf-8")
    (template / "scripts" / "tool.py").write_text("# okf-library-template\n", encoding="utf-8")
    (template / "image.bin").write_bytes(b"\xff\xfe")
    assert sorted(leftover_markers(template)) == ["README.md: open-renewables", "knowledge/note.md: richard-gledhill"]


def test_the_command_line_runs_from_an_answers_file(template: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        init_library_main(["--root", str(template), "--answers", str(ANSWERS / "answers-git-local.yaml"), "--json"])
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert "CLAUDE.md" in data["removed"] and data["leftovers"] == []
    assert load_profile(template).platform == "git-local"


def test_the_command_line_reports_bad_answers_and_bad_folders(
    tmp_path: Path, template: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("platform: nowhere\nname: X\n", encoding="utf-8")
    assert init_library_main(["--root", str(template), "--answers", str(bad)]) == 2
    assert "platform must be one of" in capsys.readouterr().err
    assert init_library_main(["--root", str(tmp_path), "--answers", str(ANSWERS / "answers-github.yaml")]) == 2


def test_the_questionnaire_asks_for_each_answer() -> None:
    replies = iter(
        [
            "git-local",
            "my-lib",
            "",
            "A library.",
            "owner",
            "Olive Owner",
            "olive@example.org",
            "",
            "CC0-1.0",
            "MIT",
            "no",
            "yes",
        ]
    )
    prompts: list[str] = []

    def ask(prompt: str) -> str:
        prompts.append(prompt)
        return next(replies)

    answers = questionnaire(ask)
    assert (answers.platform, answers.name, answers.title, answers.login) == ("git-local", "my-lib", "My Lib", "owner")
    assert (answers.content_licence, answers.code_licence, answers.keep_examples, answers.keep_tests) == (
        "CC0-1.0",
        "MIT",
        False,
        True,
    )
    assert answers.repository == ""
    assert any("Platform" in p for p in prompts) and not any("Repository URL" in p for p in prompts)


def test_the_questionnaire_asks_for_the_repository_on_github() -> None:
    replies = iter(
        ["", "my-lib", "", "", "owner", "", "owner@example.org", "", "", "", "https://github.com/o/my-lib", "", ""]
    )
    answers = questionnaire(lambda _prompt: next(replies))
    assert (answers.platform, answers.repository, answers.keep_examples, answers.keep_tests) == (
        "github",
        "https://github.com/o/my-lib",
        True,
        False,
    )


def test_the_command_line_can_ask(template: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter(
        [
            "github",
            "ask-lib",
            "",
            "",
            "asker",
            "",
            "asker@example.org",
            "",
            "",
            "",
            "https://github.com/o/ask-lib",
            "",
            "",
        ]
    )
    assert init_library_main(["--root", str(template)], ask=lambda _prompt: next(replies)) == 0
    assert load_profile(template).library_name == "ask-lib"
