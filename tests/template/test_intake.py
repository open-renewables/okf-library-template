"""The intake and governance files under .github/ (plan step 7, FR5.1, FR5.3, FR5.4, C-09)."""

from pathlib import Path

import pytest
from okfprofile import supply_cli
from okfprofile.codeowners import load_codeowners
from okfprofile.document import parse_yaml
from okfprofile.supply_cli import check_config_main, config_commands
from support import ROOT

GITHUB = ROOT / ".github"
FORMS = sorted(p for p in (GITHUB / "ISSUE_TEMPLATE").glob("*.yml") if p.name != "config.yml")
LABELS = {
    "intake:new-concept",
    "intake:correction",
    "intake:feedback",
    "agent-drafted",
    "full-review",
    "approved-move",
    "profile-migration",
    "stale",
    "validation-failure",
}


def yaml_of(path: Path) -> object:
    return parse_yaml(path.read_text(encoding="utf-8"))[0]


def test_the_label_list_is_the_set_in_the_design() -> None:
    labels = yaml_of(GITHUB / "labels.yml")
    assert isinstance(labels, list)
    assert {label["name"] for label in labels} == LABELS
    assert len(labels) == len(LABELS)
    for label in labels:
        assert len(label["color"]) == 6
        assert int(label["color"], 16) >= 0
        assert label["description"]
        assert len(label["description"]) <= 100  # noqa: PLR2004 - GitHub's limit; longer fails with HTTP 422


def test_there_is_a_form_for_each_kind_of_contribution() -> None:
    assert [p.name for p in FORMS] == ["correction.yml", "feedback.yml", "new-concept.yml"]


@pytest.mark.parametrize("form", FORMS, ids=lambda p: p.name)
def test_a_form_names_only_listed_labels_and_has_unique_field_ids(form: Path) -> None:
    data = yaml_of(form)
    assert isinstance(data, dict)
    assert data["labels"]
    assert set(data["labels"]) <= LABELS
    ids = [item["id"] for item in data["body"] if "id" in item]
    assert len(ids) == len(set(ids))
    assert any(item.get("validations", {}).get("required") for item in data["body"])


def test_blank_issues_are_off() -> None:
    config = yaml_of(GITHUB / "ISSUE_TEMPLATE" / "config.yml")
    assert isinstance(config, dict)
    assert config["blank_issues_enabled"] is False
    assert config["contact_links"]


def test_the_pull_request_template_prompts_for_the_four_labels() -> None:
    text = (GITHUB / "pull_request_template.md").read_text(encoding="utf-8")
    for label in ("agent-drafted", "full-review", "approved-move", "profile-migration"):
        assert f"`{label}`" in text
        assert label in LABELS


def test_dependabot_watches_actions_and_python_dependencies() -> None:
    data = yaml_of(GITHUB / "dependabot.yml")
    assert isinstance(data, dict)
    assert {u["package-ecosystem"] for u in data["updates"]} == {"github-actions", "uv"}


def test_the_code_owners_cover_every_tooling_and_content_path() -> None:
    owners = load_codeowners(ROOT)
    for path in (
        "knowledge/example-group/example-category/example-item.md",
        "knowledge/vocab/group.md",
        "scripts/okfprofile/config.py",
        "profile/profile.yaml",
        ".github/workflows/validate.yml",
        "docs/development/plan/plan.md",
        "pyproject.toml",
    ):
        assert owners.owners_for(path), path
    assert all(rule.owners for rule in owners.rules)


def test_config_commands_cover_the_files_that_exist(tmp_path: Path) -> None:
    assert config_commands(tmp_path) == []
    commands = config_commands(ROOT)
    assert [c[3] for c in commands] == [
        "vendor.github-issue-forms",
        "vendor.github-issue-config",
        "vendor.github-workflows",
        "vendor.dependabot",
    ]
    assert all(c[:3] == ["uvx", "check-jsonschema", "--builtin-schema"] for c in commands)
    assert ".github/ISSUE_TEMPLATE/config.yml" not in commands[0]
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "a.yml").write_text("name: a\n", encoding="utf-8")
    expected = [["uvx", "check-jsonschema", "--builtin-schema", "vendor.github-workflows", ".github/workflows/a.yml"]]
    assert config_commands(tmp_path) == expected


def test_check_config_prints_or_refuses(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    assert check_config_main(["--root", str(ROOT), "--print-command"]) == 0
    assert capsys.readouterr().out.count("check-jsonschema") == 4
    monkeypatch.setattr(supply_cli.shutil, "which", lambda _name: None)
    assert check_config_main(["--root", str(ROOT)]) == 2
