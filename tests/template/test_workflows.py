"""Rules for the workflow files (SDD section 10, AD-02, AD-20, NFR6): pinned actions, least privilege, tasks only."""

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
from okfprofile.document import parse_yaml
from support import ROOT

WORKFLOWS = ROOT / ".github" / "workflows"
FILES = sorted(WORKFLOWS.glob("*.yml"))
USES = re.compile(r"^\s*-?\s*uses:\s*(?P<action>[\w./-]+)@(?P<ref>\S+)(?P<rest>.*)$", re.MULTILINE)
PINNED_COMMENT = re.compile(r"^\s*#\s*v\d+(\.\d+)*\s*$")
SHA = re.compile(r"^[0-9a-f]{40}$")
UV_RUN = re.compile(r"\buv run (?P<what>\S+)")
POE_TASK = re.compile(r"\buv run poe (?P<task>[\w-]+)")
FORBIDDEN_IN_RUN = ("python ", "python3 ", "pip install", "pip3 install", "npm ", "npx ")
TOKEN_PERMISSIONS = {"contents", "pull-requests", "issues", "pages", "id-token", "actions", "checks", "packages"}


def load(path: Path) -> dict[str, Any]:
    data = parse_yaml(path.read_text(encoding="utf-8"))[0]
    assert isinstance(data, dict)
    return data


def run_blocks(workflow: dict[str, Any]) -> list[str]:
    return [step["run"] for job in workflow["jobs"].values() for step in job.get("steps", []) if "run" in step]


def pins() -> dict[str, str]:
    """Key and value of the gitleaks pin in `constraints.md`."""
    text = (ROOT / "docs" / "development" / "constraints.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| gitleaks |"))
    cells = [c.strip().strip("`") for c in row.strip("|").split("|")]
    return {"version": cells[1].removeprefix("v"), "sha256": cells[3]}


def test_the_expected_workflows_exist() -> None:
    assert [p.name for p in FILES] == ["revision.yml", "stale-report.yml", "template-tests.yml", "validate.yml"]


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_action_is_pinned_by_full_sha_with_its_version_in_a_comment(path: Path) -> None:
    uses = list(USES.finditer(path.read_text(encoding="utf-8")))
    assert uses, "a workflow without actions would not check anything out"
    for match in uses:
        assert SHA.match(match["ref"]), f"{match['action']}@{match['ref']} is not pinned by a full commit SHA"
        assert re.match(r"^\s*#\s*v\d", match["rest"]), f"{match['action']} has no version comment"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_dangerous_trigger_and_least_privilege(path: Path) -> None:
    workflow = load(path)
    triggers = workflow["on"]
    assert not {"pull_request_target", "workflow_run"} & set(triggers)
    assert workflow["permissions"] == {}, "the workflow default must grant nothing; each job declares its own"
    for name, job in workflow["jobs"].items():
        assert "permissions" in job, f"job {name} must declare its permissions"
        assert set(job["permissions"]) <= TOKEN_PERMISSIONS
        assert "timeout-minutes" in job, f"job {name} needs a timeout"
        assert job["permissions"].get("contents") in {"read", "write"}


def test_a_job_that_pushes_is_the_only_one_with_write_access_to_contents() -> None:
    writers = {
        (path.name, name)
        for path in FILES
        for name, job in load(path)["jobs"].items()
        if job["permissions"].get("contents") == "write"
    }
    assert writers == {("revision.yml", "revision-token")}


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_workflows_call_only_poe_tasks_and_never_a_script_or_an_installer(path: Path) -> None:
    for block in run_blocks(load(path)):
        for line in block.splitlines():
            stripped = line.strip()
            assert not stripped.startswith(FORBIDDEN_IN_RUN), f"{path.name}: {stripped}"
            for match in UV_RUN.finditer(stripped):
                assert match["what"] == "poe", f"{path.name}: `uv run {match['what']}` is not a poe task"


def test_every_poe_task_a_workflow_calls_exists() -> None:
    tasks = set(tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poe"]["tasks"])
    called = {m["task"] for p in FILES for b in run_blocks(load(p)) for m in POE_TASK.finditer(b)}
    assert called
    assert called <= tasks, sorted(called - tasks)


def test_the_validate_job_is_the_required_check_and_runs_for_pull_requests_reviews_and_pushes() -> None:
    workflow = load(WORKFLOWS / "validate.yml")
    triggers = workflow["on"]
    assert {"pull_request", "pull_request_review", "push", "workflow_dispatch"} <= set(triggers)
    assert set(triggers["pull_request"]["types"]) >= {"labeled", "unlabeled", "synchronize"}
    assert workflow["jobs"]["validate"]["name"] == "validate"
    assert workflow["jobs"]["validate"]["permissions"] == {"contents": "read", "pull-requests": "read"}


def test_validation_runs_on_the_lowest_and_highest_supported_python() -> None:
    check = load(WORKFLOWS / "validate.yml")["jobs"]["check"]
    assert check["strategy"]["matrix"]["python"] == ["3.11", "3.14"]
    template = load(WORKFLOWS / "template-tests.yml")["jobs"]["tests"]["strategy"]["matrix"]
    assert template["python"] == ["3.11", "3.14"]
    assert set(template["os"]) == {"ubuntu-latest", "macos-latest", "windows-latest"}


def test_the_gitleaks_pin_matches_constraints() -> None:
    pin = pins()
    env = load(WORKFLOWS / "validate.yml")["jobs"]["scan"]["env"]
    assert env["GITLEAKS_VERSION"] == pin["version"]
    assert env["GITLEAKS_SHA256"] == pin["sha256"]
    assert len(pin["sha256"]) == 64


def test_the_revision_workflow_skips_its_own_commits_and_serialises_runs() -> None:
    workflow = load(WORKFLOWS / "revision.yml")
    assert workflow["concurrency"] == {"group": "revision", "cancel-in-progress": False}
    assert "Revision-Bot: true" in workflow["jobs"]["mode"]["if"]
    app = workflow["jobs"]["revision-app"]
    assert app["permissions"]["contents"] == "read"
    assert "github-app" in app["if"]
    steps = [s.get("uses", "") for s in app["steps"]]
    assert any(s.startswith("actions/create-github-app-token@") for s in steps)
    for job in ("revision-app", "revision-token"):
        checkout = next(s for s in workflow["jobs"][job]["steps"] if s.get("uses", "").startswith("actions/checkout@"))
        assert checkout["with"]["persist-credentials"] is False
        assert checkout["with"]["fetch-depth"] == 0


def test_the_revision_token_mode_is_read_from_the_profile_by_the_workflow() -> None:
    step = next(s for s in load(WORKFLOWS / "revision.yml")["jobs"]["mode"]["steps"] if s.get("id") == "mode")
    command = step["run"].splitlines()[0]
    assert "sed -n 's/^  revision_token: *//p' profile/profile.yaml" in command
    assert re.search(
        r"^  revision_token: (github-app|github-token)\s*$",
        (ROOT / "profile" / "profile.yaml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )


def test_labels_the_workflows_use_exist_in_the_label_list() -> None:
    labels = {entry["name"] for entry in parse_yaml((ROOT / ".github" / "labels.yml").read_text(encoding="utf-8"))[0]}
    used = set()
    for path in FILES:
        used |= set(re.findall(r"--label ([\w:-]+)", path.read_text(encoding="utf-8")))
    assert used == {"validation-failure", "stale"}
    assert used <= labels


def test_the_template_only_workflow_is_removed_at_instantiation() -> None:
    from okfprofile.instantiate import TEMPLATE_TESTS

    assert ".github/workflows/template-tests.yml" in TEMPLATE_TESTS
