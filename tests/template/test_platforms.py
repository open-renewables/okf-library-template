"""The platform adapters, replayed from responses recorded in the sandbox (plan step 4, G9)."""

import io
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from email.message import Message
from pathlib import Path
from typing import Any

import pytest
from okfprofile.config import load_profile
from okfprofile.platforms import CommitInfo, PlatformError, normalise_login
from okfprofile.platforms.commits import parse_trailers
from okfprofile.platforms.git_local import GitLocalAdapter
from okfprofile.platforms.github import GitHubAdapter, HttpTransport, NotFoundError, subject_number
from support import ROOT

RECORDED = json.loads((ROOT / "tests/template/fixtures/github/sandbox-2026-11-03.json").read_text(encoding="utf-8"))
REPO = RECORDED["repo"]
ROUTES: dict[str, Any] = RECORDED["routes"]
WHEN = datetime(2026, 11, 3, 2, 20, tzinfo=UTC)


class Replay:
    """A transport that answers from recorded routes and remembers what was asked."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def get(self, path: str) -> tuple[Any, str | None]:
        self.calls.append(path)
        if path not in self.routes:
            msg = f"not recorded: {path}"
            raise NotFoundError(msg)
        return self.routes[path], None


def recorded_commit(sha: str) -> CommitInfo:
    raw = ROUTES[f"repos/{REPO}/commits/{sha}"]["commit"]
    return CommitInfo(sha, WHEN, raw["message"].splitlines()[0], raw["author"]["name"], raw["author"]["email"], "x")


def adapter(routes: dict[str, Any] | None = None, **kwargs: Any) -> tuple[GitHubAdapter, Replay, list[float]]:
    transport = Replay(ROUTES if routes is None else routes)
    sleeps: list[float] = []
    return GitHubAdapter(REPO, transport, sleeps.append, **kwargs), transport, sleeps


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("okf-sandbox-revision-bot[bot]", "okf-sandbox-revision-bot"),
        ("alice", "alice"),
        ("a b/c", "a-b-c"),
        ("-x", "x"),
        ("[bot]", "unknown"),
        ("", "unknown"),
    ],
)
def test_logins_fit_the_revision_grammar(raw: str, expected: str) -> None:
    assert normalise_login(raw) == expected


def test_trailers_come_from_the_last_paragraph_only() -> None:
    message = "Subject\n\nBody text: not a trailer\n\nApproved-by: Ann <a@example.org>\nFull-Review: yes\n"
    assert parse_trailers(message) == {"approved-by": "Ann <a@example.org>", "full-review": "yes"}
    assert parse_trailers("Subject\n\nA paragraph that is\nnot trailers.\n") == {}
    assert parse_trailers("Revision-Bot: true") == {}


def test_subject_number() -> None:
    assert subject_number("Add a thing (#12)") == 12
    assert subject_number("Add a thing") is None
    assert subject_number("Fix (#3) later") is None


def test_a_stale_approval_is_recorded_with_the_commit_it_was_given_on() -> None:
    github, _transport, sleeps = adapter()
    change = github.resolve(recorded_commit(RECORDED["merge_shas"]["stale"]))
    assert (change.kind, change.number, change.reference) == ("pr", 2, "PR #2")
    assert change.author == change.merged_by == "richard-gledhill"
    assert change.labels == {"approved-move"}
    (review,) = change.reviews
    assert (review.login, review.state) == ("okf-sandbox-revision-bot", "APPROVED")
    assert review.commit_id.startswith("081457a")
    assert change.head_sha.startswith("7bf2b9f")
    assert review.commit_id != change.head_sha
    assert sleeps == []


def test_a_merge_without_review_has_no_reviews() -> None:
    github, _transport, _sleeps = adapter()
    change = github.resolve(recorded_commit(RECORDED["merge_shas"]["noreview"]))
    assert (change.number, change.reviews) == (3, ())


@pytest.mark.parametrize("key", ["app-push", "app-push-2"])
def test_a_push_without_a_pull_request_is_pr_none_by_the_pusher(key: str) -> None:
    github, _transport, sleeps = adapter()
    commit = recorded_commit(RECORDED["direct_shas"][key])
    change = github.resolve(commit)
    assert (change.kind, change.number, change.reference) == ("pr-none", None, "PR none")
    assert change.author == change.merged_by == "p2-s1"
    assert sleeps == []


def test_the_closed_list_is_tried_first_and_the_subject_next() -> None:
    sha = RECORDED["merge_shas"]["lk1"]
    github, transport, _ = adapter()
    assert github.find_pull_number(recorded_commit(sha)) == 4
    assert transport.calls == [f"repos/{REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=100"]
    routes = dict(ROUTES)
    del routes[f"repos/{REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=100"]
    github, transport, _ = adapter(routes)
    assert github.find_pull_number(recorded_commit(sha)) == 4
    assert transport.calls[-1] == f"repos/{REPO}/pulls/4"


def test_the_commit_endpoint_is_the_last_resort_and_is_retried_while_it_lags() -> None:
    sha = RECORDED["merge_shas"]["lk2"]
    pulls_path = f"repos/{REPO}/commits/{sha}/pulls"
    empty = {k: v for k, v in ROUTES.items() if k not in {pulls_path, f"repos/{REPO}/pulls/5"}}
    empty[f"repos/{REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=100"] = []

    class Lagging(Replay):
        def get(self, path: str) -> tuple[Any, str | None]:
            if path == pulls_path and self.calls.count(path) >= 3:
                return ROUTES[pulls_path], None
            return super().get(path)

    sleeps: list[float] = []
    github = GitHubAdapter(REPO, Lagging(empty), sleeps.append, attempts=6, delay=6.0)
    assert github.find_pull_number(recorded_commit(sha)) == 5
    assert sleeps == [6.0, 6.0, 6.0]


def test_a_commit_whose_subject_names_a_pull_request_is_retried_for_the_whole_budget() -> None:
    github, _transport, sleeps = adapter({}, attempts=6, delay=6.0)
    commit = CommitInfo("f" * 40, WHEN, "Add a thing (#99)", "A", "a@example.org", "a@example.org")
    assert github.find_pull_number(commit) is None
    assert sum(sleeps) == 30.0


def test_a_commit_with_no_number_in_the_subject_is_tried_once() -> None:
    github, _transport, sleeps = adapter({})
    commit = CommitInfo("f" * 40, WHEN, "Direct push", "A", "a@example.org", "a@example.org")
    assert github.find_pull_number(commit) is None
    assert sleeps == []


def test_reviews_are_paged_and_ordered_oldest_first() -> None:
    sha = RECORDED["merge_shas"]["stale"]
    first = [{"user": {"login": "b"}, "state": "approved", "commit_id": "2", "submitted_at": "2026-01-02T00:00:00Z"}]
    second = [{"user": {"login": "a"}, "state": "COMMENTED", "commit_id": "1", "submitted_at": "2026-01-01T00:00:00Z"}]

    class Paged(Replay):
        def get(self, path: str) -> tuple[Any, str | None]:
            if path.endswith("pulls/2/reviews?per_page=100"):
                self.calls.append(path)
                return first, f"repos/{REPO}/pulls/2/reviews?per_page=100&page=2"
            if path.endswith("page=2"):
                self.calls.append(path)
                return second, None
            return super().get(path)

    github = GitHubAdapter(REPO, Paged(ROUTES), lambda _s: None)
    change = github.resolve(recorded_commit(sha))
    assert [(r.login, r.state) for r in change.reviews] == [("a", "COMMENTED"), ("b", "APPROVED")]


def test_a_vanished_pull_request_is_an_error() -> None:
    sha = RECORDED["merge_shas"]["lk1"]
    routes = {k: v for k, v in ROUTES.items() if k != f"repos/{REPO}/pulls/4"}
    github, _transport, _sleeps = adapter(routes)
    with pytest.raises(PlatformError, match="disappeared"):
        github.resolve(recorded_commit(sha))


class Response(io.BytesIO):
    """A stand-in for the object ``urlopen`` returns."""

    def __init__(self, body: object, link: str = "") -> None:
        super().__init__(json.dumps(body).encode("utf-8"))
        self.headers = Message()
        if link:
            self.headers["Link"] = link

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://api.github.com/x", code, "x", Message(), None)


def test_http_transport_sends_the_token_and_follows_the_link_header(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[urllib.request.Request] = []

    def urlopen(request: urllib.request.Request, timeout: int) -> Response:
        seen.append(request)
        return Response([1], '<https://api.github.com/repos/o/r/pulls?page=2>; rel="next", <x>; rel="last"')

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    data, nxt = HttpTransport("tok").get("repos/o/r/pulls")
    assert (data, nxt) == ([1], "repos/o/r/pulls?page=2")
    assert seen[0].get_header("Authorization") == "Bearer tok"
    assert seen[0].full_url == "https://api.github.com/repos/o/r/pulls"


def test_http_transport_retries_a_gateway_error_and_reports_the_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    answers: list[object] = [http_error(502), http_error(503), Response({"ok": True})]
    sleeps: list[float] = []

    def urlopen(_request: object, timeout: int) -> Response:
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer  # type: ignore[return-value]  # the stand-in is a Response

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    assert HttpTransport("t", sleep=sleeps.append).get("x") == ({"ok": True}, None)
    assert sleeps == [2.0, 4.0]
    answers[:] = [http_error(404)]
    with pytest.raises(NotFoundError):
        HttpTransport("t").get("x")
    answers[:] = [http_error(500)]
    with pytest.raises(PlatformError, match="HTTP 500"):
        HttpTransport("t").get("x")
    answers[:] = [http_error(502)] * 3
    with pytest.raises(PlatformError, match="HTTP 502"):
        HttpTransport("t", sleep=lambda _s: None).get("x")
    answers[:] = [urllib.error.URLError("offline")]
    with pytest.raises(PlatformError, match="cannot read"):
        HttpTransport("t").get("x")


@pytest.fixture
def local(tmp_path: Path) -> GitLocalAdapter:
    for name in ("profile",):
        (tmp_path / name).mkdir()
    import shutil

    shutil.copytree(ROOT / "profile", tmp_path / "profile", dirs_exist_ok=True)
    text = (tmp_path / "profile" / "profile.yaml").read_text(encoding="utf-8")
    text = text.replace("platform: github", "platform: git-local").replace(
        "maintainers: {}", "maintainers:\n  alice:\n    emails: [alice@example.org]\n    role: maintainer\n"
    )
    (tmp_path / "profile" / "profile.yaml").write_text(text, encoding="utf-8", newline="\n")
    return GitLocalAdapter(load_profile(tmp_path))


def commit(trailers: dict[str, str], author: str = "alice@example.org", committer: str | None = None) -> CommitInfo:
    return CommitInfo("abcdef1" + "0" * 33, WHEN, "Change", "A", author, committer or author, trailers)


def test_git_local_resolves_authors_through_the_maintainers_map(local: GitLocalAdapter) -> None:
    change = local.resolve(commit({}))
    assert (change.kind, change.reference, change.author, change.merged_by) == (
        "commit",
        "commit abcdef1",
        "alice",
        "alice",
    )
    other = local.resolve(commit({}, author="bob@example.org"))
    assert other.author == "bob"


def test_git_local_approvals_count_only_when_they_name_someone_else(local: GitLocalAdapter) -> None:
    approved = local.resolve(commit({"approved-by": "Carol <carol@example.org>; Alice <alice@example.org>"}))
    assert [(r.login, r.state, r.commit_id == approved.head_sha) for r in approved.reviews] == [
        ("carol", "APPROVED", True)
    ]
    assert local.resolve(commit({"approved-by": "Alice <ALICE@example.org>"})).reviews == ()
    assert local.resolve(commit({"approved-by": "Dave"})).reviews[0].login == "Dave"


def test_git_local_labels_stand_for_trailers(local: GitLocalAdapter) -> None:
    change = local.resolve(commit({"full-review": "yes", "agent-drafted": "YES"}))
    assert change.labels == {"full-review", "agent-drafted"}
    assert local.resolve(commit({"full-review": "no"})).labels == frozenset()
