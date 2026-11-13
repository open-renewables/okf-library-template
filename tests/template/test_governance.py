"""The template's own README, NOTICE and GOVERNANCE.md name only things that exist (P3 plan step 8, G18, FR6.2)."""

import re
import tomllib
from pathlib import Path

from support import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8")
NOTICE = (ROOT / "NOTICE").read_text(encoding="utf-8")
GOVERNANCE = (ROOT / "GOVERNANCE.md").read_text(encoding="utf-8")
PLACEHOLDERS = {"{maintainer}", "{contact}"}


def tasks() -> set[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return set(data["tool"]["poe"]["tasks"])


def test_every_poe_task_the_readme_names_exists() -> None:
    named = set(re.findall(r"uv run poe ([a-z][a-z-]*)", README))
    assert {"init", "check", "test", "setup-repo", "link-skills", "docs-build", "bundle", "release"} <= named
    assert named <= tasks(), sorted(named - tasks())


def test_every_script_and_path_the_readme_names_exists() -> None:
    for script in re.findall(r"scripts/([a-z_]+)\.py", README):
        assert (ROOT / "scripts" / f"{script}.py").is_file(), script
    for target in re.findall(r"\]\((?!https?:|#)([^)]+)\)", README):
        assert (ROOT / target.replace("%20", " ")).exists(), target
    for path in ("docs/development/operations/runbook-instantiate-library.md", ".agents/skills", "AGENTS.md"):
        assert (ROOT / path).exists(), path


def test_the_readme_no_longer_says_the_template_is_unbuilt() -> None:
    assert "build phase P0" not in README
    assert "(planned)" not in README
    assert "not built yet" not in README


def test_notice_names_only_paths_that_exist_and_every_vendored_folder() -> None:
    for path in re.findall(r"(?<![\w/])((?:[\w.-]+/)+[\w.-]*)", NOTICE):
        if path.startswith(("http", "creativecommons")):
            continue
        assert (ROOT / path).exists(), path
    for folder in sorted((ROOT / "scripts" / "vendor").iterdir()):
        assert f"scripts/vendor/{folder.name}/" in NOTICE, folder.name


def test_governance_has_only_the_two_placeholders_init_library_fills() -> None:
    assert set(re.findall(r"\{[a-z_]+\}", GOVERNANCE)) == PLACEHOLDERS


def test_governance_covers_what_the_plan_lists() -> None:
    for heading in (
        "Roles",
        "Review and what `stable` means",
        "Contributing",
        "Decisions",
        "Releases",
        "Staleness, deprecation and deletion",
        "Reporting a security problem",
    ):
        assert f"## {heading}" in GOVERNANCE, heading
    assert "require_non_author_approver" in GOVERNANCE
    assert "never deleted" in GOVERNANCE


def test_the_labels_governance_names_exist_in_the_label_list() -> None:
    labels = (ROOT / ".github" / "labels.yml").read_text(encoding="utf-8")
    for label in re.findall(r"`(agent-drafted|full-review|approved-move|profile-migration)`", GOVERNANCE):
        assert f"name: {label}" in labels, label


def test_the_issue_chooser_links_a_file_that_exists() -> None:
    config = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    linked = re.findall(r"/blob/main/([\w./-]+)", config)
    assert linked == ["GOVERNANCE.md"]
    assert Path(ROOT / linked[0]).is_file()


def test_rfc_001_follows_the_rfc_rules() -> None:
    text = (ROOT / "docs" / "development" / "rfcs" / "RFC-001-scope-notes.md").read_text(encoding="utf-8")
    assert text.startswith("Status: Draft\n")
    assert "ADRs produced:" in text
    assert "## Recommendation" in text


def test_no_ide_folder_is_tracked() -> None:
    import subprocess

    done = subprocess.run(
        ["git", "ls-files", ".idea"],  # noqa: S607
        capture_output=True,
        check=True,
        cwd=ROOT,
        text=True,
    )
    assert done.stdout == ""
    assert ".idea/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
