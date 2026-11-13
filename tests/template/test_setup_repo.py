"""Configuring a GitHub repository: ``setup_repo.py`` against an in-memory GitHub (plan step 10, NFR7, W-11)."""

import copy
import json
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import pytest
from okfprofile import ghsetup
from okfprofile.ghsetup import (
    GhCli,
    GhError,
    NotFoundError,
    build_plan,
    covers,
    desired_ruleset,
    promote_profile,
    read_labels,
)
from okfprofile.setup_cli import setup_repo_main
from support import ROOT

REPO = "acme/lib"
LABELS = ["intake:new-concept", "intake:correction", "intake:feedback", "agent-drafted", "full-review"]


class FakeGitHub:
    """A small model of one repository: it answers the calls ``setup_repo`` makes and changes state like GitHub."""

    def __init__(self, visibility: str = "public", client_id: str = "Iv23liREAL") -> None:
        self.state: dict[str, Any] = {
            "repo": {
                "visibility": visibility,
                "allow_squash_merge": True,
                "allow_merge_commit": True,
                "allow_rebase_merge": True,
                "squash_merge_commit_title": "COMMIT_OR_PR_TITLE",
                "squash_merge_commit_message": "COMMIT_MESSAGES",
                "delete_branch_on_merge": False,
                "security_and_analysis": {
                    "secret_scanning": {"status": "disabled"},
                    "secret_scanning_push_protection": {"status": "disabled"},
                },
            },
            "workflow": {"default_workflow_permissions": "write", "can_approve_pull_request_reviews": True},
            "alerts": False,
            "labels": [],
            "rulesets": {},
            "codeql": {"state": "not-configured"},
            "pages": None,
            "environment": None,
            "variables": {},
            "secrets": set(),
        }
        self.installations = [{"app_slug": "rev-bot", "app_id": 77}]
        self.client_id = client_id
        self.calls: list[tuple[str, str]] = []

    def paginate(self, path: str) -> list[Any]:
        self.calls.append(("GET", path))
        assert path.startswith(f"repos/{REPO}/"), path
        if "/labels" in path:
            return copy.deepcopy(self.state["labels"])
        return [{"id": i, "name": r["name"]} for i, r in self.state["rulesets"].items()]

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:  # noqa: C901
        self.calls.append((method, path))
        state = self.state
        if path.startswith("orgs/acme/installations"):
            return {"installations": self.installations}
        if path.startswith("apps/"):
            return {"client_id": self.client_id}
        assert path.startswith(f"repos/{REPO}"), f"a request must name its repository: {path}"
        tail = path.removeprefix(f"repos/{REPO}").lstrip("/")
        if tail == "":
            if method == "PATCH":
                assert body is not None
                for key, value in body.items():
                    if key == "security_and_analysis":
                        for name, setting in value.items():
                            state["repo"]["security_and_analysis"][name] = dict(setting)
                    else:
                        state["repo"][key] = value
            return copy.deepcopy(state["repo"])
        if tail == "actions/permissions/workflow":
            if method == "PUT":
                state["workflow"] = dict(body or {})
            return dict(state["workflow"])
        if tail == "vulnerability-alerts":
            if method == "PUT":
                state["alerts"] = True
            elif not state["alerts"]:
                msg = "HTTP 404"
                raise NotFoundError(msg)
            return None
        if tail == "labels" and method == "POST":
            assert body is not None
            state["labels"].append(dict(body))
            return body
        if tail.startswith("labels/") and method == "PATCH":
            name = unquote(tail.removeprefix("labels/"))
            next(label for label in state["labels"] if label["name"] == name).update(body or {})
            return None
        if tail == "rulesets" and method == "POST":
            assert body is not None
            ruleset = copy.deepcopy(body)
            for rule in ruleset["rules"]:
                if rule["type"] == "pull_request":
                    rule["parameters"].update({"required_reviewers": [], "dismissal_restriction": {"enabled": False}})
            state["rulesets"][len(state["rulesets"]) + 1] = ruleset
            return ruleset
        if tail.startswith("rulesets/"):
            number = int(tail.removeprefix("rulesets/"))
            if method == "PUT":
                state["rulesets"][number] = copy.deepcopy(body)
            return copy.deepcopy(state["rulesets"][number])
        if tail == "code-scanning/default-setup":
            if method == "PATCH":
                state["codeql"] = {"state": "configured", **(body or {})}
            return dict(state["codeql"])
        if tail == "pages":
            if method == "POST":
                state["pages"] = dict(body or {})
            elif state["pages"] is None:
                msg = "HTTP 404"
                raise NotFoundError(msg)
            return state["pages"]
        if tail == "environments/github-pages":
            state["environment"] = {"policies": []}
            return None
        if tail == "environments/github-pages/deployment-branch-policies":
            if method == "POST":
                assert body is not None
                assert state["environment"] is not None, "the environment must exist before a policy is added"
                state["environment"]["policies"].append(dict(body))
            elif state["environment"] is None:
                msg = "HTTP 404"
                raise NotFoundError(msg)
            return {"branch_policies": list(state["environment"]["policies"])}
        for kind in ("variables", "secrets"):
            if tail.startswith(f"actions/{kind}/"):
                name = tail.rsplit("/", 1)[1]
                found = state[kind]
                if name not in found:
                    msg = "HTTP 404"
                    raise NotFoundError(msg)
                return {"value": found[name]} if kind == "variables" else {"name": name}
        msg = f"unexpected request {method} {path}"
        raise AssertionError(msg)


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A working tree with the real profile (platform github) and the label list."""
    root = tmp_path / "lib"
    shutil.copytree(ROOT / "profile", root / "profile")
    profile = root / "profile" / "profile.yaml"
    profile.write_text(
        profile.read_text(encoding="utf-8").replace("revision_token: github-app", "revision_token: github-token"),
        encoding="utf-8",
        newline="\n",
    )  # as init_library.py leaves a library that is not yet public
    (root / ".github").mkdir()
    shutil.copy2(ROOT / ".github" / "labels.yml", root / ".github" / "labels.yml")
    return root


def run(root: Path, api: FakeGitHub, *args: str) -> int:
    return setup_repo_main(["--root", str(root), "--repo", REPO, *args], api=api)


def test_a_dry_run_lists_every_change_and_changes_nothing(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub()
    before = copy.deepcopy(api.state)
    assert run(library, api, "--dry-run", "--json") == 0
    out = json.loads(capsys.readouterr().out)
    details = {op["detail"] for op in out["operations"]}
    assert {
        "create intake:new-concept",
        "create validation-failure",
        "create main-protect",
        "enable with push protection",
    } <= details
    assert any(d.startswith("allow_") or "delete_branch_on_merge" in d for d in details)
    assert sum(op["area"] == "label" for op in out["operations"]) == len(read_labels(library))
    assert api.state == before
    assert {method for method, _ in api.calls} == {"GET"}


def test_a_run_sets_everything_and_a_second_run_changes_nothing(
    library: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    api = FakeGitHub()
    assert run(library, api) == 0
    state = api.state
    assert state["repo"]["allow_merge_commit"] is False
    assert state["repo"]["allow_rebase_merge"] is False
    assert state["repo"]["squash_merge_commit_title"] == "PR_TITLE"
    assert state["workflow"] == {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
    assert state["alerts"] is True
    assert len(state["labels"]) == len(read_labels(library))
    assert state["repo"]["security_and_analysis"]["secret_scanning"] == {"status": "enabled"}
    (ruleset,) = state["rulesets"].values()
    assert ruleset["name"] == "main-protect" and ruleset["enforcement"] == "active"
    capsys.readouterr()
    api.calls.clear()
    assert run(library, api, "--json") == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operations"] == [] and out["problems"] == []
    assert {method for method, _ in api.calls} == {"GET"}


def test_rerunning_restores_what_someone_deleted(library: Path) -> None:
    api = FakeGitHub()
    run(library, api)
    api.state["labels"] = [label for label in api.state["labels"] if label["name"] != "full-review"]
    api.state["repo"]["allow_merge_commit"] = True
    api.state["workflow"]["can_approve_pull_request_reviews"] = True
    api.state["alerts"] = False
    api.state["rulesets"].clear()
    assert run(library, api) == 0
    assert any(label["name"] == "full-review" for label in api.state["labels"])
    assert api.state["repo"]["allow_merge_commit"] is False
    assert api.state["workflow"]["can_approve_pull_request_reviews"] is False
    assert api.state["alerts"] is True
    assert len(api.state["rulesets"]) == 1


def test_a_label_with_the_wrong_colour_is_patched_by_its_encoded_name(library: Path) -> None:
    api = FakeGitHub()
    run(library, api)
    next(label for label in api.state["labels"] if label["name"] == "intake:new-concept")["color"] = "000000"
    api.calls.clear()
    assert run(library, api) == 0
    assert ("PATCH", f"repos/{REPO}/labels/intake%3Anew-concept") in api.calls
    assert next(label for label in api.state["labels"] if label["name"] == "intake:new-concept")["color"] == "0e8a16"


def test_a_private_repository_gets_settings_and_labels_only(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub(visibility="private")
    assert run(library, api, "--json") == 0
    out = json.loads(capsys.readouterr().out)
    assert {op["area"] for op in out["operations"]} == {
        "merge methods",
        "workflow permissions",
        "dependency alerts",
        "label",
    }
    assert any("private repository" in note for note in out["notes"])
    assert api.state["rulesets"] == {}


def test_the_ruleset_puts_the_app_on_the_bypass_list_and_requires_the_check_once_the_workflow_exists(
    library: Path,
) -> None:
    api = FakeGitHub()
    assert run(library, api, "--app-slug", "rev-bot") == 0
    (ruleset,) = api.state["rulesets"].values()
    assert {"actor_id": 77, "actor_type": "Integration", "bypass_mode": "always"} in ruleset["bypass_actors"]
    assert {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"} in ruleset["bypass_actors"]
    assert "required_status_checks" not in {r["type"] for r in ruleset["rules"]}
    (library / ".github" / "workflows").mkdir()
    (library / ".github" / "workflows" / "validate.yml").write_text("name: validate\n", encoding="utf-8")
    assert run(library, api, "--app-slug", "rev-bot") == 0
    (ruleset,) = api.state["rulesets"].values()
    checks = next(r for r in ruleset["rules"] if r["type"] == "required_status_checks")
    assert checks["parameters"]["required_status_checks"] == [{"context": "validate"}]
    assert run(library, api, "--app-slug", "rev-bot", "--no-required-check") == 0
    (ruleset,) = api.state["rulesets"].values()
    assert "required_status_checks" not in {r["type"] for r in ruleset["rules"]}


def test_an_unknown_app_is_a_problem(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub()
    assert run(library, api, "--app-slug", "nobody") == 1
    assert "'nobody' is not installed in acme" in capsys.readouterr().err
    assert api.state["labels"] == []


def test_a_changed_ruleset_is_updated_in_place(library: Path) -> None:
    api = FakeGitHub()
    run(library, api)
    api.state["rulesets"][1]["enforcement"] = "disabled"
    api.calls.clear()
    assert run(library, api) == 0
    assert ("PUT", f"repos/{REPO}/rulesets/1") in api.calls
    assert api.state["rulesets"][1]["enforcement"] == "active"


def test_promote_needs_a_public_repository_and_an_app(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(library, FakeGitHub(visibility="private"), "--promote", "--app-slug", "rev-bot") == 1
    assert "make it public first" in capsys.readouterr().err
    api = FakeGitHub()
    assert run(library, api, "--promote") == 1
    assert "--promote needs --app-slug" in capsys.readouterr().err
    assert api.state["labels"] == []


def test_promote_reaches_the_end_state_of_w11(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub()
    assert run(library, api, "--promote", "--app-slug", "rev-bot") == 0
    state = api.state
    assert state["codeql"]["state"] == "configured" and state["codeql"]["languages"] == ["actions", "python"]
    assert state["pages"] == {"build_type": "workflow"}
    assert state["environment"]["policies"] == [{"name": "main", "type": "branch"}, {"name": "v*", "type": "tag"}]
    assert state["repo"]["security_and_analysis"]["secret_scanning_push_protection"] == {"status": "enabled"}
    assert "revision_token: github-app" in (library / "profile" / "profile.yaml").read_text(encoding="utf-8")
    assert "immutable releases" in capsys.readouterr().err
    api.calls.clear()
    assert run(library, api, "--promote", "--app-slug", "rev-bot") == 0
    assert {method for method, _ in api.calls} == {"GET"}


def test_promote_adds_only_the_missing_tag_policy_to_an_environment_that_allows_main(library: Path) -> None:
    api = FakeGitHub()
    api.state["pages"] = {"build_type": "workflow"}
    api.state["environment"] = {"policies": [{"name": "main", "type": "branch"}]}
    assert run(library, api, "--promote", "--app-slug", "rev-bot") == 0
    assert api.state["environment"]["policies"] == [{"name": "main", "type": "branch"}, {"name": "v*", "type": "tag"}]
    assert ("PUT", f"repos/{REPO}/environments/github-pages") not in api.calls


def test_promote_changes_the_profile_once(library: Path) -> None:
    assert promote_profile(library) is True
    assert promote_profile(library) is False


def test_check_reports_drift_and_the_app_setup(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub(client_id="Iv23liREAL")
    assert run(library, api, "--check", "--app-slug", "rev-bot") == 1
    err = capsys.readouterr().err
    assert "problem: drift: label: create agent-drafted" in err
    assert "is not on the main-protect ruleset bypass list" in err
    assert "the variable APP_CLIENT_ID is missing" in err
    assert "the secret APP_PRIVATE_KEY is missing" in err
    assert api.state["labels"] == []
    run(library, api, "--app-slug", "rev-bot")
    api.state["variables"]["APP_CLIENT_ID"] = "lv23liREAL"
    api.state["secrets"].add("APP_PRIVATE_KEY")
    assert run(library, api, "--check", "--app-slug", "rev-bot") == 1
    assert "not the App's client ID" in capsys.readouterr().err
    api.state["variables"]["APP_CLIENT_ID"] = "Iv23liREAL"
    assert run(library, api, "--check", "--app-slug", "rev-bot") == 0


def test_check_with_an_unknown_app_stops_at_the_installation(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    api = FakeGitHub()
    run(library, api)
    assert run(library, api, "--check", "--app-slug", "nobody") == 1
    assert "is not installed in acme" in capsys.readouterr().err


def test_the_command_reports_what_it_cannot_do(library: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = library / "profile" / "profile.yaml"
    profile.write_text(
        profile.read_text(encoding="utf-8").replace("platform: github", "platform: git-local"),
        encoding="utf-8",
        newline="\n",
    )
    assert run(library, FakeGitHub()) == 2
    assert setup_repo_main(["--root", str(tmp_path / "nowhere")], api=FakeGitHub()) == 2
    profile.write_text(
        profile.read_text(encoding="utf-8").replace("platform: git-local", "platform: github"),
        encoding="utf-8",
        newline="\n",
    )
    (library / ".github" / "labels.yml").unlink()
    assert run(library, FakeGitHub()) == 2
    (library / ".github" / "labels.yml").write_text("not: a list\n", encoding="utf-8")
    assert run(library, FakeGitHub()) == 2
    assert setup_repo_main(["--root", str(library)], api=FakeGitHub()) == 2


def test_covers_ignores_what_github_adds() -> None:
    assert covers({"a": 1, "extra": 2}, {"a": 1})
    assert not covers({"a": 1}, {"a": 2})
    assert not covers({}, {"a": 1})
    assert covers([{"t": 1, "x": 2}, {"t": 3}], [{"t": 3}, {"t": 1}])
    assert not covers([{"t": 1}], [{"t": 1}, {"t": 2}])
    assert not covers("x", {"a": 1})
    assert not covers({"a": 1}, [1])


def test_the_ruleset_follows_section_11() -> None:
    ruleset = desired_ruleset(77, True)
    assert ruleset["conditions"] == {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}}
    pull = next(r for r in ruleset["rules"] if r["type"] == "pull_request")["parameters"]
    assert pull["required_approving_review_count"] == 1 and pull["require_code_owner_review"] is True
    assert pull["require_last_push_approval"] is False and pull["allowed_merge_methods"] == ["squash"]
    assert desired_ruleset(None, False)["bypass_actors"] == [
        {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}
    ]


def test_build_plan_never_names_another_repository(library: Path) -> None:
    api = FakeGitHub()
    build_plan(api, REPO, library, "rev-bot", True, promote=True)
    assert all(path.startswith((f"repos/{REPO}", "orgs/acme/", "apps/")) for _, path in api.calls)


class Completed:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode, self.stdout, self.stderr = returncode, stdout.encode(), stderr.encode()


def test_the_gh_client_sends_json_and_reads_it_back(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[list[str], bytes | None]] = []

    def fake_run(command: list[str], **kwargs: Any) -> Completed:
        seen.append((command, kwargs.get("input")))
        return Completed(stdout='{"ok": true}')

    monkeypatch.setattr(ghsetup.subprocess, "run", fake_run)
    assert GhCli().request("PATCH", f"repos/{REPO}", {"a": 1}) == {"ok": True}
    assert seen[0] == (["gh", "api", "-X", "PATCH", f"repos/{REPO}", "--input", "-"], b'{"a": 1}')
    assert GhCli().request("GET", f"repos/{REPO}") == {"ok": True}
    assert seen[1] == (["gh", "api", "-X", "GET", f"repos/{REPO}"], None)


def test_the_gh_client_maps_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(
        [Completed(1, stderr="gh: Not Found (HTTP 404)"), Completed(1, stderr="gh: boom (HTTP 500)"), Completed(0, "")]
    )
    monkeypatch.setattr(ghsetup.subprocess, "run", lambda *_a, **_k: next(answers))
    with pytest.raises(NotFoundError):
        GhCli().request("GET", f"repos/{REPO}/pages")
    with pytest.raises(GhError, match="boom"):
        GhCli().request("GET", f"repos/{REPO}")
    assert GhCli().request("PUT", f"repos/{REPO}/vulnerability-alerts") is None


def test_the_gh_client_flattens_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter([Completed(0, '[[{"n": 1}], [{"n": 2}, {"n": 3}]]'), Completed(1, stderr="denied")])
    monkeypatch.setattr(ghsetup.subprocess, "run", lambda *_a, **_k: next(answers))
    assert GhCli().paginate(f"repos/{REPO}/labels") == [{"n": 1}, {"n": 2}, {"n": 3}]
    with pytest.raises(GhError, match="denied"):
        GhCli().paginate(f"repos/{REPO}/labels")


def test_unusable_label_files_are_refused(tmp_path: Path) -> None:
    with pytest.raises(GhError, match="cannot read"):
        read_labels(tmp_path)
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "labels.yml").write_text("- name: x\n", encoding="utf-8")
    with pytest.raises(GhError, match="name and a colour"):
        read_labels(tmp_path)


def test_every_label_in_the_repository_list_is_created() -> None:
    names = {label["name"] for label in read_labels(ROOT)}
    assert set(LABELS) <= names


def test_an_existing_ruleset_under_another_name_is_converged_in_place(library: Path) -> None:
    api = FakeGitHub()
    api.state["rulesets"][5] = {
        "name": "main",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}],
        "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
    }
    assert run(library, api, "--ruleset-name", "main", "--app-slug", "rev-bot") == 0
    assert list(api.state["rulesets"]) == [5]
    ruleset = api.state["rulesets"][5]
    assert ruleset["name"] == "main"
    assert {"actor_id": 77, "actor_type": "Integration", "bypass_mode": "always"} in ruleset["bypass_actors"]
    assert "pull_request" in {r["type"] for r in ruleset["rules"]}
    api.state["variables"]["APP_CLIENT_ID"] = "Iv23liREAL"
    api.state["secrets"].add("APP_PRIVATE_KEY")
    assert run(library, api, "--check", "--ruleset-name", "main", "--app-slug", "rev-bot") == 0
    assert run(library, api, "--check", "--app-slug", "rev-bot") == 1
