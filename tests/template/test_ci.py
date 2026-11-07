"""Validation in CI and tracking issues (plan step 12, FR1.5, FR1.6, FR2.4 to FR2.6, G4)."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from okfprofile import ci_cli
from okfprofile.ci import (
    agent_markers_in,
    base_ref,
    before_sha,
    change_from_pull_request,
    change_from_push,
    latest_reviews,
    pull_request_number,
)
from okfprofile.ci_cli import ci_validate_main, commit_messages, report_issue_main, validate_event
from okfprofile.cli import build_indexes_main, validate_main
from okfprofile.issues import close_issues, open_issues, upsert_issue
from okfprofile.platforms import PlatformError
from okfprofile.platforms.github import NotFoundError
from support import PATH, ROOT, git

REPO = "acme/lib"


def review(login: str, state: str, commit_id: str, at: str) -> dict[str, Any]:
    return {"user": {"login": login}, "state": state, "commit_id": commit_id, "submitted_at": at}


def pull_event(labels: tuple[str, ...] = (), body: str = "", base: str = "main", number: int = 7) -> dict[str, Any]:
    return {
        "pull_request": {
            "number": number,
            "labels": [{"name": name} for name in labels],
            "user": {"login": "bob"},
            "head": {"sha": "h" * 40},
            "base": {"ref": base},
            "body": body,
        }
    }


class Reviews:
    """A transport that returns a fixed list of reviews for any pull request."""

    def __init__(self, reviews: list[dict[str, Any]]) -> None:
        self.reviews = reviews
        self.paths: list[str] = []

    def get(self, path: str) -> tuple[Any, str | None]:
        self.paths.append(path)
        return self.reviews, None


def test_the_latest_decision_of_each_reviewer_counts() -> None:
    raw = [
        review("alice", "APPROVED", "a1", "2026-01-01T00:00:00Z"),
        review("alice", "COMMENTED", "a2", "2026-01-02T00:00:00Z"),
        review("carol", "APPROVED", "c1", "2026-01-01T00:00:00Z"),
        review("carol", "CHANGES_REQUESTED", "c2", "2026-01-03T00:00:00Z"),
        review("dave", "APPROVED", "d1", "2026-01-01T00:00:00Z"),
        review("dave", "DISMISSED", "d2", "2026-01-02T00:00:00Z"),
        review("eve", "PENDING", "e1", "2026-01-02T00:00:00Z"),
        {"user": None, "state": "APPROVED", "commit_id": "x", "submitted_at": "2026-01-01T00:00:00Z"},
    ]
    by_login = {r.login: r for r in latest_reviews(raw)}
    assert {k: (v.approved, v.commit_id) for k, v in by_login.items()} == {
        "alice": (True, "a1"),
        "carol": (False, "c2"),
        "dave": (False, "d2"),
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>", True),
        ("co-authored-by: GitHub Copilot <copilot@github.com>", True),
        ("Agent-Drafted: yes", True),
        ("Generated with [Claude Code](https://claude.com/claude-code)", True),
        ("Co-Authored-By: Alice Example <alice@example.org>", False),
        ("Agent-Drafted: no", False),
        ("Fixes a typo", False),
        ("", False),
    ],
)
def test_agent_markers_are_found_in_trailers_and_descriptions(text: str, expected: bool) -> None:
    assert agent_markers_in("nothing here", text) is expected


def test_a_pull_request_event_becomes_a_change_context() -> None:
    reviews = [review("alice", "APPROVED", "a1", "2026-01-01T00:00:00Z")]
    change = change_from_pull_request(
        pull_event(("approved-move", "full-review"), "Generated with [Claude Code](x)"), reviews, ["Fix"]
    )
    assert change.labels == {"approved-move", "full-review"}
    assert (change.author, change.head_sha, change.agent_markers, change.reviews_known) == ("bob", "h" * 40, True, True)
    assert [(r.login, r.approved) for r in change.reviews] == [("alice", True)]
    plain = change_from_pull_request(pull_event(), [], ["Fix a typo"])
    assert plain.agent_markers is False and plain.reviews == []
    from_commit = change_from_pull_request(pull_event(), [], ["Fix\n\nCo-Authored-By: Claude <x@y.z>"])
    assert from_commit.agent_markers is True


def test_a_push_event_is_marked_when_it_is_a_revision_commit() -> None:
    bot = {
        "head_commit": {"message": "Record revision history\n\nRevision-Bot: true\n"},
        "after": "a" * 40,
        "pusher": {"name": "bot"},
    }
    assert change_from_push(bot).revision_bot is True
    human = {"head_commit": {"message": "Add a thing (#4)"}, "after": "b" * 40, "pusher": {"name": "bob"}}
    change = change_from_push(human)
    assert (change.revision_bot, change.author, change.head_sha) == (False, "bob", "b" * 40)
    assert change_from_push({}).revision_bot is False


def test_event_helpers() -> None:
    assert pull_request_number(pull_event(number=12)) == 12
    assert base_ref(pull_event(base="release")) == "origin/release"
    assert before_sha({"before": "a" * 40}) == "a" * 40
    assert before_sha({"before": "0" * 40}) is None
    assert before_sha({}) is None


# ----------------------------------------------------------------------------------------- validating by event


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A repository on `main` holding the template's tooling, profile and example bundle; `origin/main` is `main`."""
    root = tmp_path / "lib"
    for name in ("scripts", "profile", "knowledge"):
        shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "uv.lock", ".python-version", ".gitattributes"):
        shutil.copy2(ROOT / name, root / name)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.org")
    git(root, "config", "user.name", "T")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base", when="2026-11-01T10:00:00+00:00")
    git(root, "update-ref", "refs/remotes/origin/main", "main")
    git(root, "switch", "-q", "-c", "topic")
    return root


def run_event(root: Path, name: str, event: dict[str, Any], reviews: list[dict[str, Any]] | None = None) -> int:
    transport = Reviews(reviews or [])
    return validate_event(root, name, event, transport, REPO)


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message, when="2026-11-02T10:00:00+00:00")


def test_a_content_pull_request_passes_with_the_base_tooling(library: Path) -> None:
    concept = library / PATH
    concept.write_text(
        concept.read_text(encoding="utf-8").replace("plain prose", "plain prose (edited)", 1),
        encoding="utf-8",
        newline="\n",
    )
    commit(library, "Edit the example")
    assert run_event(library, "pull_request", pull_event()) == 0


def test_a_pull_request_that_changes_tooling_and_content_fails_unless_labelled(
    library: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    (library / "scripts" / "extra.py").write_text("# tooling\n", encoding="utf-8")
    concept = library / PATH
    concept.write_text(
        concept.read_text(encoding="utf-8").replace("plain prose", "plain prose (edited)", 1),
        encoding="utf-8",
        newline="\n",
    )
    commit(library, "Both at once")
    assert run_event(library, "pull_request", pull_event()) == 1
    assert "OKF001" in capfd.readouterr().err
    assert run_event(library, "pull_request", pull_event(("profile-migration",))) == 1
    assert "OKF002" in capfd.readouterr().err


def test_a_moved_concept_needs_the_approved_move_label(library: Path, capfd: pytest.CaptureFixture[str]) -> None:
    moved = library / "knowledge" / "example-group" / "example-category" / "renamed-item.md"
    git(library, "mv", PATH, str(moved.relative_to(library)))
    assert validate_main(["--root", str(library), "--fix-registry", "--label", "approved-move"]) == 0
    assert build_indexes_main(["--root", str(library)]) == 0
    commit(library, "Rename the example")
    assert run_event(library, "pull_request", pull_event()) == 1
    assert "OKF60" in capfd.readouterr().err
    assert run_event(library, "pull_request", pull_event(("approved-move",))) == 0


def test_the_pull_request_is_judged_with_the_base_tooling_and_its_own_labels_and_reviews(
    library: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (library / "docs").mkdir()
    (library / "docs" / "note.md").write_text("x\n", encoding="utf-8")
    git(library, "add", "-A")
    git(
        library,
        "commit",
        "-q",
        "-m",
        "Note\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        when="2026-11-02T10:00:00+00:00",
    )
    seen: dict[str, Any] = {}

    def fake_validate(argv: list[str]) -> int:
        seen["argv"] = argv
        seen["change"] = json.loads(Path(argv[argv.index("--change") + 1]).read_text(encoding="utf-8"))
        return 0

    monkeypatch.setattr(ci_cli, "validate_main", fake_validate)
    reviews = [review("alice", "APPROVED", "a1", "2026-01-01T00:00:00Z")]
    transport = Reviews(reviews)
    assert (
        validate_event(library, "pull_request_review", pull_event(("full-review",)), transport, REPO, ["--json"]) == 0
    )
    argv = seen["argv"]
    assert argv[argv.index("--tooling-from") + 1] == "origin/main" and argv[argv.index("--base") + 1] == "origin/main"
    assert argv[-1] == "--json"
    assert seen["change"]["labels"] == ["full-review"]
    assert seen["change"]["agent_markers"] is True
    assert seen["change"]["reviews"] == [{"login": "alice", "approved": True, "commit_id": "a1"}]
    assert transport.paths == [f"repos/{REPO}/pulls/7/reviews?per_page=100"]
    assert commit_messages(library, "origin/main")[0].startswith("Note")


def test_a_pull_request_event_needs_a_transport(library: Path) -> None:
    with pytest.raises(PlatformError, match="without a token"):
        validate_event(library, "pull_request", pull_event(), None, REPO)


def test_a_push_to_main_is_validated_against_the_commit_before_it(library: Path) -> None:
    before = git(library, "rev-parse", "HEAD")
    concept = library / PATH
    concept.write_text(
        concept.read_text(encoding="utf-8").replace("plain prose", "plain prose (edited)", 1),
        encoding="utf-8",
        newline="\n",
    )
    commit(library, "Edit the example")
    (library / "scripts" / "extra.py").write_text("# tooling\n", encoding="utf-8")
    commit(library, "Tooling merged together with content earlier, as a migration")
    event = {"before": before, "after": git(library, "rev-parse", "HEAD"), "head_commit": {"message": "x"}}
    assert run_event(library, "push", event) == 0


def test_a_revision_line_removed_from_main_fails_the_push_run(
    library: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    concept = library / PATH
    line = "- 2026-11-01 · author @bob · self-approved (non-owner) · PR #3\n"
    marker = "<!-- Maintained by CI. Do not edit. -->\n"
    text = concept.read_text(encoding="utf-8")
    concept.write_text(text.replace(marker, marker + "\n" + line, 1), encoding="utf-8", newline="\n")
    git(library, "add", "-A")
    git(
        library, "commit", "-q", "-m", "Record revision history\n\nRevision-Bot: true", when="2026-11-02T09:00:00+00:00"
    )
    before = git(library, "rev-parse", "HEAD")
    concept.write_text(text, encoding="utf-8", newline="\n")
    commit(library, "Hand edit that removes the line")
    event = {"before": before, "after": git(library, "rev-parse", "HEAD"), "head_commit": {"message": "Hand edit"}}
    assert run_event(library, "push", event) == 1
    assert "OKF315" in capsys.readouterr().err


def test_a_push_without_a_before_commit_and_a_manual_run_validate_the_whole_tree(library: Path) -> None:
    assert run_event(library, "push", {"before": "0" * 40, "after": "a" * 40}) == 0
    assert run_event(library, "workflow_dispatch", {}) == 0
    (library / "knowledge" / "stray.md").write_text("no frontmatter\n", encoding="utf-8")
    assert run_event(library, "workflow_dispatch", {}) == 1


def test_the_command_reads_the_event_from_the_environment(
    library: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    event = tmp_path / "event.json"
    event.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert ci_validate_main(["--root", str(library)]) == 0
    assert summary.read_text(encoding="utf-8") == "No findings.\n"
    event.write_text("not json", encoding="utf-8")
    assert ci_validate_main(["--root", str(library)]) == 2
    monkeypatch.delenv("GITHUB_EVENT_NAME")
    assert ci_validate_main(["--root", str(library), "--event-path", str(event)]) == 2


# ----------------------------------------------------------------------------------------- tracking issues


class FakeIssues:
    """An in-memory issue tracker that answers the calls ``issues.py`` makes."""

    def __init__(self, issues: list[dict[str, Any]] | None = None) -> None:
        self.issues = issues or []
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def paginate(self, path: str) -> list[Any]:
        self.calls.append(("GET", path, None))
        return [dict(i) for i in self.issues if i.get("state", "open") == "open"]

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, path, body))
        if method == "POST" and path.endswith("/issues"):
            assert body is not None
            made = {"number": 100 + len(self.issues), "state": "open", **body}
            self.issues.append(made)
            return made
        if method == "PATCH":
            number = int(path.rsplit("/", 1)[1])
            next(i for i in self.issues if i["number"] == number).update(body or {})
        return None


def test_the_tracking_issue_is_created_then_updated_in_place() -> None:
    api = FakeIssues()
    assert upsert_issue(api, REPO, "validation-failure", "Failed", "body one") == ("created", 100)
    assert api.issues[0]["labels"] == ["validation-failure"]
    assert upsert_issue(api, REPO, "validation-failure", "Failed", "body two") == ("updated", 100)
    assert api.issues[0]["body"] == "body two" and len(api.issues) == 1
    api.calls.clear()
    assert upsert_issue(api, REPO, "validation-failure", "Failed", "body two") == ("updated", 100)
    assert [c[0] for c in api.calls] == ["GET"]


def test_pull_requests_are_not_tracking_issues_and_the_oldest_issue_wins() -> None:
    api = FakeIssues(
        [
            {"number": 9, "title": "t", "body": "b", "pull_request": {}},
            {"number": 8, "title": "newer", "body": "b"},
            {"number": 5, "title": "older", "body": "b"},
        ]
    )
    assert [i["number"] for i in open_issues(api, REPO, "stale")] == [5, 8]
    assert upsert_issue(api, REPO, "stale", "new title", "b")[1] == 5
    assert api.paginate(f"repos/{REPO}/issues?labels=stale&state=open&per_page=100")


def test_the_label_is_url_encoded() -> None:
    api = FakeIssues()
    open_issues(api, REPO, "intake:new-concept")
    assert api.calls[0][1] == f"repos/{REPO}/issues?labels=intake%3Anew-concept&state=open&per_page=100"


def test_closing_comments_and_closes_each_open_issue() -> None:
    api = FakeIssues([{"number": 3, "title": "t", "body": "b"}, {"number": 4, "title": "t", "body": "b"}])
    assert close_issues(api, REPO, "validation-failure", "fixed") == 2
    assert all(i["state"] == "closed" for i in api.issues)
    assert [c[1] for c in api.calls if c[0] == "POST"] == [
        f"repos/{REPO}/issues/3/comments",
        f"repos/{REPO}/issues/4/comments",
    ]
    assert close_issues(api, REPO, "validation-failure", "again") == 0


def test_the_report_command_opens_updates_and_closes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = tmp_path / "body.md"
    body.write_text("details\n", encoding="utf-8")
    api = FakeIssues()
    args = ["--repo", REPO, "--label", "stale", "--title", "Review report", "--body-file", str(body)]
    assert report_issue_main(args, api=api) == 0
    assert "created issue #100" in capsys.readouterr().err
    assert report_issue_main(args, api=api) == 0
    assert "updated issue #100" in capsys.readouterr().err
    assert report_issue_main(["--repo", REPO, "--label", "stale", "--close", "--comment", "done"], api=api) == 0
    assert "closed 1 issue(s)" in capsys.readouterr().err
    assert api.issues[0]["state"] == "closed"


def test_the_report_command_reports_what_it_cannot_do(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert report_issue_main(["--label", "stale"], api=FakeIssues()) == 2
    assert report_issue_main(["--repo", REPO, "--label", "stale"], api=FakeIssues()) == 2
    assert (
        report_issue_main(
            ["--repo", REPO, "--label", "stale", "--title", "t", "--body-file", str(tmp_path / "none.md")],
            api=FakeIssues(),
        )
        == 2
    )

    class Refusing(FakeIssues):
        def paginate(self, path: str) -> list[Any]:
            raise NotFoundError(path)

    body = tmp_path / "b.md"
    body.write_text("x", encoding="utf-8")
    assert (
        report_issue_main(["--repo", REPO, "--label", "x", "--title", "t", "--body-file", str(body)], api=Refusing())
        == 2
    )
