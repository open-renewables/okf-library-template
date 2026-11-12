"""Skills and the provider adapter (P3 plan steps 1 to 3; SDD C-08, I-14; ADR-002)."""

import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from okfprofile.archive import ARCHIVE_FOLDERS
from okfprofile.config import load_profile
from okfprofile.skills import (
    ADAPTERS,
    MANAGED_MARKER,
    SKILLS_DIR,
    check_skill,
    check_skills,
    forbidden_terms,
    link_skills,
)
from okfprofile.skills_cli import check_skills_main, link_skills_main
from support import ROOT

SKILL_FILES = sorted((ROOT / SKILLS_DIR).glob("*/SKILL.md"))
DOCUMENTS = [*SKILL_FILES, ROOT / "AGENTS.md"]
CODE = re.compile(r"```[a-z]*\n(.*?)```|`([^`\n]+)`", re.DOTALL)
SCRIPT = re.compile(r"scripts/([a-z_]+)\.py")
TASK = re.compile(r"uv run poe ([a-z][a-z-]*)")
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z-]*)")
GOOD = "---\nname: {name}\ndescription: Does a thing.\n---\n\n# Title\n\nBody.\n"


def skill_in(tmp_path: Path, name: str, text: str) -> Path:
    folder = tmp_path / SKILLS_DIR / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
    return folder


def messages(tmp_path: Path, folder: Path) -> list[str]:
    terms = forbidden_terms(load_profile(ROOT))
    return [f.message for f in check_skill(tmp_path, folder, terms)]


def test_both_skills_exist_and_pass() -> None:
    assert {p.parent.name for p in SKILL_FILES} == {"author-concept", "use-bundle"}
    findings, count = check_skills(load_profile(ROOT))
    assert count == 2
    assert findings == []


def test_a_sound_skill_has_no_findings(tmp_path: Path) -> None:
    assert messages(tmp_path, skill_in(tmp_path, "good-skill", GOOD.format(name="good-skill"))) == []


def test_an_extra_frontmatter_field_is_found(tmp_path: Path) -> None:
    text = GOOD.format(name="x-skill").replace("description:", "disable-model-invocation: true\ndescription:")
    assert any("disable-model-invocation" in m for m in messages(tmp_path, skill_in(tmp_path, "x-skill", text)))


def test_a_name_that_differs_from_its_folder_is_found(tmp_path: Path) -> None:
    found = messages(tmp_path, skill_in(tmp_path, "folder-name", GOOD.format(name="other-name")))
    assert any("differs from its folder" in m for m in found)


def test_a_bad_name_is_found(tmp_path: Path) -> None:
    found = messages(tmp_path, skill_in(tmp_path, "Bad_Name", GOOD.format(name="Bad_Name")))
    assert any("lower-case hyphenated" in m for m in found)


def test_a_missing_description_and_missing_frontmatter_are_found(tmp_path: Path) -> None:
    no_description = skill_in(tmp_path, "no-description", "---\nname: no-description\n---\n\nBody.\n")
    assert messages(tmp_path, no_description) == ["description is missing"]
    plain = skill_in(tmp_path, "plain", "Body only.\n")
    assert messages(tmp_path, plain) == ["frontmatter is missing or unreadable"]
    broken = skill_in(tmp_path, "broken", "---\nname: [unclosed\n---\n\nBody.\n")
    assert messages(tmp_path, broken) == ["frontmatter is missing or unreadable"]


def test_a_missing_skill_file_is_found(tmp_path: Path) -> None:
    folder = tmp_path / SKILLS_DIR / "empty"
    folder.mkdir(parents=True)
    assert messages(tmp_path, folder) == ["has no SKILL.md"]


def test_an_overlong_description_and_body_are_found(tmp_path: Path) -> None:
    text = "---\nname: long-skill\ndescription: " + "x" * 1025 + "\n---\n\n" + "line\n" * 501
    found = messages(tmp_path, skill_in(tmp_path, "long-skill", text))
    assert any("description is over" in m for m in found)
    assert any("body is over" in m for m in found)


@pytest.mark.parametrize(
    "term",
    ["a concept of type Item", "uid ITM-0001", "tag group:example-group", "a Vocabulary", "uid GLS-0001"],
)
def test_a_profile_term_in_a_skill_is_found(tmp_path: Path, term: str) -> None:
    text = GOOD.format(name="hard-coded").replace("Body.", f"Write {term} here.")
    assert any("must read it from the profile" in m for m in messages(tmp_path, skill_in(tmp_path, "hard-coded", text)))


def test_a_profile_term_in_a_references_file_is_found(tmp_path: Path) -> None:
    folder = skill_in(tmp_path, "with-reference", GOOD.format(name="with-reference"))
    (folder / "references").mkdir()
    (folder / "references" / "tiers.md").write_text("Use ITM-0001.\n", encoding="utf-8")
    assert any("uid prefix ITM" in m for m in messages(tmp_path, folder))


def test_a_broken_link_and_a_missing_script_are_found(tmp_path: Path) -> None:
    text = GOOD.format(name="links").replace("Body.", "See [it](references/none.md) and scripts/nothing.py.")
    found = messages(tmp_path, skill_in(tmp_path, "links", text))
    assert any("references/none.md" in m for m in found)
    assert any("scripts/nothing.py" in m for m in found)


def test_agents_md_names_no_profile_term(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    (tmp_path / "AGENTS.md").write_text("Write an Item with uid ITM-0001.\n", encoding="utf-8")
    findings, _ = check_skills(load_profile(tmp_path))
    assert {f.file for f in findings} == {"AGENTS.md"}


def tasks() -> set[str]:
    return set(tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poe"]["tasks"])


def help_of(script: str) -> str:
    done = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts" / f"{script}.py"), "--help"],
        capture_output=True,
        check=False,
        cwd=ROOT,
        text=True,
    )
    return done.stdout


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_command_a_skill_or_agents_md_names_exists(path: Path) -> None:
    problems = []
    text = path.read_text(encoding="utf-8")
    for m in CODE.finditer(text):
        snippet = (m[1] or m[2]).replace("\\\n", " ")
        for line in snippet.splitlines():
            for task in TASK.findall(line):
                if task not in tasks():
                    problems.append(f"no poe task {task}")
            for script in set(SCRIPT.findall(line)):
                if not (ROOT / "scripts" / f"{script}.py").is_file():
                    problems.append(f"no scripts/{script}.py")
                    continue
                problems.extend(
                    f"scripts/{script}.py has no {flag}"
                    for flag in set(FLAG.findall(line))
                    if flag not in help_of(script) and flag != "--help"
                )
    assert not problems, problems


def test_the_consuming_skill_is_in_the_archive_and_the_authoring_skill_is_not() -> None:
    assert ".agents/skills/use-bundle" in ARCHIVE_FOLDERS
    assert not any("author-concept" in folder for folder in ARCHIVE_FOLDERS)


def test_no_provider_specific_file_is_tracked() -> None:
    done = subprocess.run(["git", "ls-files", ".claude"], capture_output=True, check=True, cwd=ROOT, text=True)  # noqa: S607
    assert done.stdout.strip() == ""


def adapter_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / SKILLS_DIR, tmp_path / SKILLS_DIR)
    return tmp_path


def test_link_skills_creates_then_changes_nothing(tmp_path: Path) -> None:
    root = adapter_root(tmp_path)
    first = link_skills(root)
    assert {r.action for r in first} == {"created"}
    destination = root / ADAPTERS["claude"]
    assert (destination / "use-bundle" / "SKILL.md").is_file()
    assert (destination / "use-bundle" / MANAGED_MARKER).is_file()
    assert {r.action for r in link_skills(root)} == {"unchanged"}


def test_link_skills_updates_a_changed_source(tmp_path: Path) -> None:
    root = adapter_root(tmp_path)
    link_skills(root)
    skill = root / SKILLS_DIR / "use-bundle" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nMore.\n", encoding="utf-8")
    assert {r.skill: r.action for r in link_skills(root)}["use-bundle"] == "updated"
    assert "More." in (root / ADAPTERS["claude"] / "use-bundle" / "SKILL.md").read_text(encoding="utf-8")


def test_link_skills_refuses_a_folder_it_did_not_make(tmp_path: Path) -> None:
    root = adapter_root(tmp_path)
    foreign = root / ADAPTERS["claude"] / "use-bundle"
    foreign.mkdir(parents=True)
    (foreign / "SKILL.md").write_text("mine\n", encoding="utf-8")
    results = {r.skill: r.action for r in link_skills(root)}
    assert results["use-bundle"] == "refused"
    assert results["author-concept"] == "created"
    assert (foreign / "SKILL.md").read_text(encoding="utf-8") == "mine\n"


def test_link_skills_dry_run_changes_nothing(tmp_path: Path) -> None:
    root = adapter_root(tmp_path)
    assert {r.action for r in link_skills(root, dry_run=True)} == {"created"}
    assert not (root / ADAPTERS["claude"]).exists()


def test_link_skills_can_make_a_directory_link(tmp_path: Path) -> None:
    root = adapter_root(tmp_path)
    try:
        results = link_skills(root, link=True)
    except OSError:
        pytest.skip("this system does not allow directory links")
    assert {r.action for r in results} == {"created"}
    assert (root / ADAPTERS["claude"] / "use-bundle").is_symlink()
    assert {r.action for r in link_skills(root, link=True)} == {"unchanged"}
    assert {r.action for r in link_skills(root)} == {"updated"}


def test_the_adapter_folder_is_git_ignored() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".claude/skills/use-bundle/SKILL.md"],  # noqa: S607
        check=False,
        cwd=ROOT,
    )
    assert ignored.returncode == 0


def test_check_skills_cli(capsys: pytest.CaptureFixture[str]) -> None:
    assert check_skills_main(["--root", str(ROOT), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == {"ok": True, "skills": 2, "findings": []}


def test_check_skills_cli_reports_a_fault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    shutil.copytree(ROOT / "knowledge", tmp_path / "knowledge")
    skill_in(tmp_path, "bad", GOOD.format(name="other"))
    assert check_skills_main(["--root", str(tmp_path), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is False
    assert report["findings"]


def test_check_skills_cli_cannot_run_without_a_profile(tmp_path: Path) -> None:
    assert check_skills_main(["--root", str(tmp_path)]) == 2


def test_link_skills_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = adapter_root(tmp_path)
    assert link_skills_main(["--root", str(root), "--json"]) == 0
    assert {r["action"] for r in json.loads(capsys.readouterr().out)} == {"created"}
    assert link_skills_main(["--root", str(root), "--dry-run"]) == 0
    foreign = root / ADAPTERS["claude"] / "author-concept"
    shutil.rmtree(foreign)
    foreign.mkdir()
    assert link_skills_main(["--root", str(root)]) == 1


def test_link_skills_cli_needs_a_skills_folder(tmp_path: Path) -> None:
    assert link_skills_main(["--root", str(tmp_path)]) == 2
