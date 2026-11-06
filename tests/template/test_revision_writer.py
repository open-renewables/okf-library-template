"""The revision writer: inference, insertion, catch-up, ``verified`` and ``OKF901`` (plan step 5, G4, G9)."""

import json
import os
import shutil
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from okfprofile.cli import validate_main
from okfprofile.codeowners import parse_codeowners
from okfprofile.config import load_profile
from okfprofile.document import parse_concept
from okfprofile.history import history_lines
from okfprofile.platforms import CommitInfo, MergedChange, MergeReview, PlatformError
from okfprofile.platforms.commits import commits_after, last_revision_bot_commit
from okfprofile.platforms.git_local import GitLocalAdapter
from okfprofile.platforms.github import GitHubAdapter, HttpTransport
from okfprofile.revision import Tier, concept_tier, parse_revision_line
from okfprofile.revision_cli import make_adapter, repository_from_remote, write_revision_main
from okfprofile.revision_writer import (
    RevisionError,
    WriteResult,
    build_line,
    catch_up,
    check_since,
    commit_revision,
    infer_approval,
    insert_line,
    set_verified,
    verified_entries,
)
from support import ROOT

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

OWNERS = parse_codeowners("/knowledge/ @alice\n")
PATH = "knowledge/example-group/example-category/example-item.md"
HEAD = "h" * 40
WHEN = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


def review(login: str, state: str = "APPROVED", commit_id: str = HEAD, at: str = "2026-11-01T10:00:00Z") -> MergeReview:
    return MergeReview(login, state, commit_id, at)


def change(
    reviews: tuple[MergeReview, ...] = (),
    author: str = "bob",
    merged_by: str | None = None,
    labels: frozenset[str] = frozenset(),
    kind: str = "pr",
) -> MergedChange:
    commit = CommitInfo("c" * 40, WHEN, "Change (#7)", "B", "b@example.org", "b@example.org")
    return MergedChange(commit, kind, 7 if kind == "pr" else None, author, merged_by or author, HEAD, reviews, labels)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("reviews", "author", "merged_by", "expected", "full"),
    [
        ((review("alice"),), "bob", "bob", "approved @alice (owner)", True),
        ((review("alice", commit_id="old"),), "bob", "bob", "approved (stale) @alice (owner)", False),
        ((review("carol"),), "bob", "bob", "approved @carol (non-owner)", False),
        ((review("carol", commit_id="old"),), "bob", "bob", "approved (stale) @carol (non-owner)", False),
        ((), "alice", "alice", "self-approved (owner)", True),
        ((), "bob", "bob", "self-approved (non-owner)", False),
        ((), "bob", "dave", "merged without approval @dave", False),
        ((review("alice"),), "alice", "alice", "self-approved (owner)", True),
        (
            (review("alice"), review("alice", "CHANGES_REQUESTED", at="2026-11-01T11:00:00Z")),
            "bob",
            "bob",
            "self-approved (non-owner)",
            False,
        ),
        (
            (review("alice"), review("alice", "COMMENTED", at="2026-11-01T11:00:00Z")),
            "bob",
            "bob",
            "approved @alice (owner)",
            True,
        ),
        (
            (review("alice"), review("alice", "DISMISSED", at="2026-11-01T11:00:00Z")),
            "bob",
            "dave",
            "merged without approval @dave",
            False,
        ),
        ((review("carol"), review("alice")), "bob", "bob", "approved @alice (owner)", True),
        ((review("alice", commit_id="old"), review("carol")), "bob", "bob", "approved (stale) @alice (owner)", False),
        (
            (review("carol", at="2026-11-01T10:00:00Z"), review("dave", at="2026-11-01T12:00:00Z")),
            "bob",
            "bob",
            "approved @dave (non-owner)",
            False,
        ),
    ],
)
def test_approval_inference_follows_w05(
    reviews: tuple[MergeReview, ...], author: str, merged_by: str, expected: str, full: bool
) -> None:
    outcome = infer_approval(change(reviews, author, merged_by), PATH, OWNERS)
    assert (outcome.text, outcome.counts_for_full_review) == (expected, full)


def test_ownership_is_assessed_per_concept_file() -> None:
    owners = parse_codeowners("/knowledge/a/ @alice\n/knowledge/b/ @bob\n")
    one = change((review("alice"),), author="carol")
    assert infer_approval(one, "knowledge/a/x.md", owners).text == "approved @alice (owner)"
    assert infer_approval(one, "knowledge/b/y.md", owners).text == "approved @alice (non-owner)"


def profile_for(tmp_path: Path) -> object:
    shutil.copytree(ROOT / "profile", tmp_path / "profile", dirs_exist_ok=True)
    return load_profile(tmp_path)


def test_lines_follow_the_grammar_and_the_labels_rules(tmp_path: Path) -> None:
    profile = profile_for(tmp_path)
    full = change((review("alice"),), labels=frozenset({"full-review", "agent-drafted"}))
    line = build_line(profile, full, PATH, OWNERS)  # type: ignore[arg-type]
    assert line == "2026-11-01 · author @bob · approved @alice (owner) · PR #7 · full-review · agent-drafted"
    parsed = parse_revision_line(line)
    assert parsed is not None
    assert (parsed.full_review, parsed.agent_drafted) == (True, True)
    stale = change((review("alice", commit_id="old"),), labels=frozenset({"full-review"}))
    assert build_line(profile, stale, PATH, OWNERS).endswith("PR #7")  # type: ignore[arg-type]
    non_owner = change((review("carol"),), labels=frozenset({"full-review"}))
    assert "full-review" not in build_line(profile, non_owner, PATH, OWNERS)  # type: ignore[arg-type]
    direct = change(kind="pr-none")
    assert build_line(profile, direct, PATH, OWNERS).endswith("self-approved (non-owner) · PR none")  # type: ignore[arg-type]


def test_an_unusable_line_is_refused(tmp_path: Path) -> None:
    profile = profile_for(tmp_path)
    with pytest.raises(RevisionError, match="grammar"):
        build_line(profile, change((review("a b"),)), PATH, OWNERS)  # type: ignore[arg-type]


CONCEPT = (
    "---\ntype: Item\n---\n\n# T\n\n## Revision history\n\n<!-- Maintained by CI. Do not edit. -->\n\n[^1]: Source.\n"
)


def test_a_first_line_goes_after_the_ci_comment_and_before_the_footnotes() -> None:
    text = insert_line(CONCEPT, "Revision history", "L1")
    assert text.endswith("<!-- Maintained by CI. Do not edit. -->\n\n- L1\n\n[^1]: Source.\n")


def test_later_lines_follow_the_last_item() -> None:
    text = insert_line(insert_line(CONCEPT, "Revision history", "L1"), "Revision history", "L2")
    assert "- L1\n- L2\n\n[^1]: Source.\n" in text


def test_a_section_without_the_comment_gets_the_line_under_its_heading() -> None:
    bare = "---\ntype: Item\n---\n\n## Revision history\n\n[^1]: S.\n"
    assert "## Revision history\n\n- L1\n\n[^1]: S.\n" in insert_line(bare, "Revision history", "L1")


def test_line_endings_are_kept() -> None:
    crlf = CONCEPT.replace("\n", "\r\n")
    text = insert_line(insert_line(crlf, "Revision history", "L1"), "Revision history", "L2")
    assert text.count("\r\n") == text.count("\n")
    assert "- L1\r\n- L2\r\n" in text
    with pytest.raises(RevisionError, match="no 'Missing' section"):
        insert_line(CONCEPT, "Missing", "L")


ENTRIES = [("human:alice", "2026-11-01T00:00:00Z")]


def test_verified_is_added_replaced_and_removed() -> None:
    added = set_verified(CONCEPT, ENTRIES)
    assert added.startswith("---\ntype: Item\nverified:\n  - by: human:alice\n    at: 2026-11-01T00:00:00Z\n---\n")
    assert set_verified(added, ENTRIES) == added
    replaced = set_verified(added, [("process:revision-bot", "2026-11-02T00:00:00Z")])
    assert replaced.count("verified:") == 1
    assert "human:alice" not in replaced
    assert set_verified(replaced, []) == CONCEPT
    assert set_verified("no frontmatter\n", ENTRIES) == "no frontmatter\n"
    assert set_verified("---\nopen only\n", ENTRIES) == "---\nopen only\n"


def test_verified_keeps_following_keys_and_crlf() -> None:
    text = "---\r\nverified:\r\n- by: x\r\n  at: y\r\nstatus: draft\r\n---\r\n\r\nBody\r\n"
    out = set_verified(text, ENTRIES)
    assert (
        out
        == "---\r\nverified:\r\n  - by: human:alice\r\n    at: 2026-11-01T00:00:00Z\r\nstatus: draft\r\n---\r\n\r\nBody\r\n"
    )


@pytest.mark.parametrize(
    ("raw", "tier", "entries"),
    [
        ([], Tier.UNVERIFIED, []),
        (
            ["2026-11-01 · author @bob · approved @alice (owner) · PR #1"],
            Tier.HUMAN_REVIEWED,
            [("human:alice", "2026-11-01T00:00:00Z")],
        ),
        (
            ["2026-11-01 · author @alice · self-approved (owner) · PR #1"],
            Tier.HUMAN_REVIEWED,
            [("human:alice", "2026-11-01T00:00:00Z")],
        ),
        (
            ["2026-11-01 · author @bob · approved @alice (owner) · PR #1 · agent-drafted"],
            Tier.MACHINE_CONFIRMED,
            [("process:revision-bot", "2026-11-01T00:00:00Z")],
        ),
        (
            [
                "2026-11-01 · author @bob · approved @alice (owner) · PR #1 · agent-drafted",
                "2026-11-02 · author @bob · approved @alice (owner) · PR #2",
            ],
            Tier.MACHINE_CONFIRMED,
            [("process:revision-bot", "2026-11-02T00:00:00Z")],
        ),
        (
            [
                "2026-11-01 · author @bob · approved @alice (owner) · PR #1 · agent-drafted",
                "2026-11-02 · author @bob · approved @alice (owner) · PR #2 · full-review",
            ],
            Tier.HUMAN_REVIEWED,
            [("human:alice", "2026-11-02T00:00:00Z")],
        ),
    ],
)
def test_verified_entries_give_a_generic_tool_the_same_tier(
    tmp_path: Path, raw: list[str], tier: Tier, entries: list[tuple[str, str]]
) -> None:
    profile = profile_for(tmp_path)
    lines = [parsed for text in raw if (parsed := parse_revision_line(text)) is not None]
    assert concept_tier(lines).tier is tier
    assert verified_entries(profile, lines) == entries  # type: ignore[arg-type]
    humans = [by for by, _ in entries if by.startswith("human:")]
    assert bool(humans) == (tier is Tier.HUMAN_REVIEWED)


# ---------------------------------------------------------------------------------------------- git-local runs


def git(root: Path, *args: str, when: str | None = None) -> str:
    env = dict(os.environ)
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, env=env, text=True)  # noqa: S603, S607
    return done.stdout.strip()


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A git-local library: the template's profile and example bundle, owner alice, one base commit."""
    root = tmp_path / "lib"
    for name in ("profile", "knowledge"):
        shutil.copytree(ROOT / name, root / name)
    text = (root / "profile" / "profile.yaml").read_text(encoding="utf-8")
    text = text.replace("platform: github", "platform: git-local").replace(
        "maintainers: {}",
        "maintainers:\n  alice:\n    emails: [alice@example.org]\n    role: maintainer\n"
        "  bob:\n    emails: [bob@example.org]\n    role: contributor\n",
    )
    (root / "profile" / "profile.yaml").write_text(text, encoding="utf-8", newline="\n")
    (root / ".github").mkdir()
    (root / ".github" / "CODEOWNERS").write_text("/knowledge/ @alice\n", encoding="utf-8", newline="\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "bot@example.org")
    git(root, "config", "user.name", "Bot")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base", when="2026-10-31T09:00:00+00:00")
    return root


def edit(root: Path, who: str, subject: str, when: str, trailers: str = "", tag: str = "x") -> str:
    file = root / PATH
    file.write_text(
        file.read_text(encoding="utf-8").replace("plain prose", f"plain prose ({tag})", 1),
        encoding="utf-8",
        newline="\n",
    )
    git(root, "add", "-A")
    args = ["commit", "-q", f"--author={who} <{who}@example.org>", "-m", subject]
    if trailers:
        args += ["-m", trailers]
    git(root, *args, when=when)
    return git(root, "rev-parse", "--short=7", "HEAD")


def lines_of(root: Path) -> list[str]:
    profile = load_profile(root)
    concept = parse_concept((root / PATH).read_text(encoding="utf-8"), PATH)
    section = concept.section("Revision history")
    assert section is not None
    return [item.text for item in section.items] if history_lines(profile, concept) is not None else []


def run(root: Path, since: str | None = None, dry_run: bool = False) -> WriteResult:
    profile = load_profile(root)
    owners = parse_codeowners((root / ".github" / "CODEOWNERS").read_text(encoding="utf-8"))
    return catch_up(profile, GitLocalAdapter(profile), owners, since=since, dry_run=dry_run)


def test_catch_up_records_each_change_in_order_and_regenerates_the_index(library: Path) -> None:
    base = git(library, "rev-parse", "HEAD")
    one = edit(library, "alice", "Owner edit", "2026-11-01T10:00:00+00:00", "Full-Review: yes", "one")
    two = edit(
        library, "bob", "Contributor edit", "2026-11-02T10:00:00+00:00", "Approved-by: Alice <alice@example.org>", "two"
    )
    result = run(library, since=base)
    assert [text for _, text in result.lines] == [
        f"2026-11-01 · author @alice · self-approved (owner) · commit {one} · full-review",
        f"2026-11-02 · author @bob · approved @alice (owner) · commit {two}",
    ]
    assert lines_of(library) == [text for _, text in result.lines]
    index = (library / "knowledge/example-group/example-category/index.md").read_text(encoding="utf-8")
    assert "human-reviewed (self)" in index
    assert validate_main(["--root", str(library)]) == 0


def test_a_second_run_changes_nothing(library: Path) -> None:
    base = git(library, "rev-parse", "HEAD")
    edit(library, "alice", "Owner edit", "2026-11-01T10:00:00+00:00")
    run(library, since=base)
    before = (library / PATH).read_bytes()
    again = run(library, since=base)
    assert again.lines == [] and again.already_present == 1
    assert (library / PATH).read_bytes() == before


def test_a_dropped_run_is_recovered_by_the_next_one(library: Path) -> None:
    base = git(library, "rev-parse", "HEAD")
    edit(library, "alice", "First", "2026-11-01T10:00:00+00:00", tag="one")
    first = run(library, since=base)
    assert commit_revision(library, first.files)
    assert last_revision_bot_commit(library) == git(library, "rev-parse", "HEAD")
    # Two merges, and no run in between (the run was cancelled or failed).
    three = edit(library, "alice", "Second", "2026-11-02T10:00:00+00:00", tag="two")
    four = edit(library, "bob", "Third", "2026-11-03T10:00:00+00:00", tag="three")
    caught = run(library)
    assert [text.split(" · ")[3] for _, text in caught.lines] == [f"commit {three}", f"commit {four}"]
    assert len(lines_of(library)) == 3
    assert not run(library, dry_run=True).lines


def test_a_dry_run_writes_nothing_and_non_concept_files_get_no_line(library: Path) -> None:
    base = git(library, "rev-parse", "HEAD")
    (library / "knowledge" / "notes.txt").write_text("not a concept\n", encoding="utf-8")
    edit(library, "alice", "Edit", "2026-11-01T10:00:00+00:00")
    before = (library / PATH).read_bytes()
    result = run(library, since=base, dry_run=True)
    assert len(result.lines) == 1 and result.files == [PATH]
    assert (library / PATH).read_bytes() == before


def test_the_writer_fills_in_verified_when_the_profile_asks(library: Path) -> None:
    profile_file = library / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8").replace("write_okf_verified: false", "write_okf_verified: true"),
        encoding="utf-8",
        newline="\n",
    )
    git(library, "commit", "-qam", "profile", when="2026-10-31T09:30:00+00:00")
    base = git(library, "rev-parse", "HEAD")
    edit(library, "alice", "Owner edit", "2026-11-01T10:00:00+00:00", "Full-Review: yes")
    run(library, since=base)
    text = (library / PATH).read_text(encoding="utf-8")
    assert "verified:\n  - by: human:alice\n    at: 2026-11-01T00:00:00Z\n" in text
    edit(library, "alice", "Agent edit", "2026-11-02T10:00:00+00:00", "Agent-Drafted: yes", "agent")
    run(library)
    text = (library / PATH).read_text(encoding="utf-8")
    assert "human:alice" not in text
    assert "by: process:revision-bot\n    at: 2026-11-02T00:00:00Z" in text
    assert validate_main(["--root", str(library)]) == 0


def test_check_since_reports_a_change_with_no_revision_line(library: Path) -> None:
    git(library, "tag", "v0.0.1")
    one = edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00", tag="one")
    profile = load_profile(library)
    adapter = GitLocalAdapter(profile)
    findings = check_since(profile, adapter, "v0.0.1")
    assert [(f.code, f.file) for f in findings] == [("OKF901", PATH)]
    assert f"commit {one}" in findings[0].message
    result = run(library, since="v0.0.1")
    commit_revision(library, result.files)
    assert check_since(profile, adapter, "v0.0.1") == []
    file = library / PATH
    file.write_text(
        "\n".join(line for line in file.read_text(encoding="utf-8").splitlines() if f"commit {one}" not in line) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    git(library, "commit", "-qam", "hand edit", when="2026-11-04T10:00:00+00:00")
    missing = check_since(profile, adapter, "v0.0.1")
    # The removed line, and the hand-edit commit itself, which no line records either.
    assert [f.code for f in missing] == ["OKF901", "OKF901"]
    assert f"commit {one}" in missing[0].message


def test_commits_after_reads_trailers_files_and_utc_dates(library: Path) -> None:
    base = git(library, "rev-parse", "HEAD")
    edit(library, "alice", "Edit", "2026-11-01T23:30:00-05:00", "Approved-by: X <x@example.org>")
    (commit,) = commits_after(library, base)
    assert commit.when == datetime(2026, 11, 2, 4, 30, tzinfo=UTC)
    assert commit.day == date(2026, 11, 2)
    assert commit.files == (PATH,)
    assert commit.trailers == {"approved-by": "X <x@example.org>"}
    assert not commit.is_revision_bot
    assert len(commits_after(library, None)) == 2


# ---------------------------------------------------------------------------------------------- command line


def test_the_command_line_writes_commits_and_checks(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = git(library, "rev-parse", "HEAD")
    git(library, "tag", "v0.0.1")
    edit(library, "alice", "Edit", "2026-11-01T10:00:00+00:00")
    assert write_revision_main(["--root", str(library), "--since", base, "--dry-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["committed"] is False
    assert write_revision_main(["--root", str(library), "--check-since", "v0.0.1"]) == 1
    assert write_revision_main(["--root", str(library), "--since", base, "--commit", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["committed"] is True and len(out["lines"]) == 1
    assert git(library, "log", "-1", "--format=%B").strip().endswith("Revision-Bot: true")
    assert write_revision_main(["--root", str(library), "--check-since", "v0.0.1", "--json"]) == 0
    assert write_revision_main(["--root", str(library)]) == 0


def test_the_command_line_reports_what_it_cannot_do(
    tmp_path: Path, library: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert write_revision_main(["--root", str(tmp_path)]) == 2
    profile_file = library / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8").replace("platform: git-local", "platform: github"),
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert write_revision_main(["--root", str(library)]) == 2
    assert write_revision_main(["--root", str(library), "--since", "nonexistent-ref"]) == 2


def test_the_github_adapter_needs_a_token_and_a_repository(library: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile_file = library / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8").replace("platform: git-local", "platform: github"),
        encoding="utf-8",
        newline="\n",
    )
    profile = load_profile(library)
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    with pytest.raises(PlatformError, match="repository"):
        make_adapter(profile)
    assert isinstance(make_adapter(profile, "o/r"), GitHubAdapter)
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    adapter = make_adapter(profile)
    assert isinstance(adapter, GitHubAdapter) and adapter.repo == "o/r" and isinstance(adapter.transport, HttpTransport)
    git(library, "remote", "add", "origin", "git@github.com:acme/widgets.git")
    monkeypatch.delenv("GITHUB_REPOSITORY")
    assert make_adapter(profile).repo == "acme/widgets"  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("url", "repo"),
    [
        ("git@github.com:acme/widgets.git", "acme/widgets"),
        ("https://github.com/acme/widgets", "acme/widgets"),
        ("https://github.com/acme/widgets.git\n", "acme/widgets"),
        ("git@example.org:acme/widgets.git", None),
    ],
)
def test_repository_from_remote(url: str, repo: str | None) -> None:
    assert repository_from_remote(url) == repo
