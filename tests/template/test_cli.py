"""The command-line scripts, run against scratch git repositories."""

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from okfprofile.cli import build_indexes_main, new_concept_main, renumber_main, validate_main
from support import ROOT

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

FIXTURE = ROOT / "tests" / "library" / "fixtures" / "pass" / "item"
ITEM = "knowledge/example-group/example-category/example-item.md"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, text=True)  # noqa: S603, S607
    return done.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A scratch repository whose first commit holds this repository's tooling and profile, and no content."""
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("scripts", "profile"):
        shutil.copytree(ROOT / name, root / name, ignore=IGNORE)
    for name in ("pyproject.toml", "uv.lock", ".python-version", ".gitattributes"):
        shutil.copy2(ROOT / name, root / name)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.org")
    git(root, "config", "user.name", "Tester")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return root


Cli = Callable[..., tuple[int, str, str]]


@pytest.fixture
def cli(capfd: pytest.CaptureFixture[str]) -> Cli:
    def run(main: Callable[[list[str]], int], root: Path, *args: str) -> tuple[int, str, str]:
        code = main(["--root", str(root), *args])
        captured = capfd.readouterr()
        return code, captured.out, captured.err

    return run


def add_content(root: Path) -> None:
    """Copy the passing fixture's bundle and registry into the repository and generate its indexes."""
    shutil.copytree(FIXTURE / "knowledge", root / "knowledge")
    shutil.copy2(FIXTURE / "profile" / "uid-registry.yaml", root / "profile" / "uid-registry.yaml")
    assert build_indexes_main(["--root", str(root)]) == 0


def commit(root: Path, message: str = "content") -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def test_a_clean_library_validates(repo: Path, cli: Cli) -> None:
    add_content(repo)
    code, out, err = cli(validate_main, repo, "--json")
    assert code == 0
    assert json.loads(out)["counts"] == {"error": 0, "warning": 0}
    assert "0 error(s), 0 warning(s)" in err


def test_errors_exit_one_and_can_be_written_as_annotations_and_a_summary(repo: Path, cli: Cli, tmp_path: Path) -> None:
    add_content(repo)
    item = repo / ITEM
    item.write_text(item.read_text(encoding="utf-8").replace("description: One sentence.\n", ""), encoding="utf-8")
    summary = tmp_path / "summary.md"
    code, out, err = cli(validate_main, repo, "--annotations", "--summary", str(summary))
    assert code == 1
    assert "OKF202" in err
    assert out.startswith("::error file=knowledge/example-group/example-category/example-item.md")
    assert "OKF202" in summary.read_text(encoding="utf-8")


def test_an_unusable_profile_exits_two(repo: Path, cli: Cli) -> None:
    (repo / "profile" / "profile.yaml").unlink()
    code, _, err = cli(validate_main, repo)
    assert code == 2
    assert err.startswith("error:")


def test_only_findings_in_changed_files_can_be_shown(repo: Path, cli: Cli) -> None:
    add_content(repo)
    vocab = repo / "knowledge" / "vocab" / "group.md"
    vocab.write_text(
        vocab.read_text(encoding="utf-8").replace("namespace: group\n", "namespace: other\n"), encoding="utf-8"
    )
    commit(repo)
    item = repo / ITEM
    item.write_text(
        item.read_text(encoding="utf-8").replace("status: draft\n", "status: draft\ncolour: red\n"), encoding="utf-8"
    )
    everything = cli(validate_main, repo, "--json")
    only_changed = cli(validate_main, repo, "--changed", "--json")
    named = cli(validate_main, repo, ITEM, "--json")
    files = lambda out: {f["file"] for f in json.loads(out)["findings"]}
    assert files(everything[1]) == {ITEM, "knowledge/vocab/group.md"}
    assert files(only_changed[1]) == {ITEM}
    assert files(named[1]) == {ITEM}


def test_comparing_with_a_base_catches_a_changed_uid(repo: Path, cli: Cli) -> None:
    add_content(repo)
    commit(repo)
    item = repo / ITEM
    item.write_text(item.read_text(encoding="utf-8").replace("ITM-0001", "ITM-0002"), encoding="utf-8")
    registry = repo / "profile" / "uid-registry.yaml"
    registry.write_text(
        registry.read_text(encoding="utf-8").replace("VOC-0001", "ITM-0002")
        if False
        else registry.read_text(encoding="utf-8")
        + "ITM-0002:\n  path: example-group/example-category/example-item\n  type: Item\n",
        encoding="utf-8",
    )
    code, _, err = cli(validate_main, repo, "--base", "HEAD")
    assert code == 1
    assert "OKF606" in err


def test_the_mixed_change_rule_through_the_command_line(repo: Path, cli: Cli) -> None:
    add_content(repo)
    commit(repo)
    (repo / "scripts" / "extra.py").write_text("x = 1\n", encoding="utf-8")
    item = repo / ITEM
    item.write_text(item.read_text(encoding="utf-8").replace("One sentence.", "Another sentence."), encoding="utf-8")
    assert "OKF001" in cli(validate_main, repo, "--base", "HEAD")[2]
    migration = cli(validate_main, repo, "--base", "HEAD", "--label", "profile-migration")[2]
    assert "OKF001" not in migration
    assert "OKF002" in migration
    assert "OKF003" in migration


def test_a_change_file_supplies_the_labels_reviews_and_paths(repo: Path, cli: Cli, tmp_path: Path) -> None:
    add_content(repo)
    item = repo / ITEM
    item.write_text(
        item.read_text(encoding="utf-8")
        .replace("status: draft", "status: stable")
        .replace("Some text with", "See [x](https://example.org). Some text with"),
        encoding="utf-8",
    )
    build_indexes_main(["--root", str(repo)])
    change = tmp_path / "change.json"
    change.write_text(
        json.dumps({"paths": [ITEM], "author": "alice", "head_sha": "h1", "reviews": []}), encoding="utf-8"
    )
    code, _, err = cli(validate_main, repo, "--change", str(change))
    assert code == 1
    assert "OKF701" in err


def test_registering_a_move_needs_the_approved_move_label(repo: Path, cli: Cli) -> None:
    add_content(repo)
    commit(repo)
    moved = repo / "knowledge" / "example-group" / "example-category" / "renamed-item.md"
    (repo / ITEM).rename(moved)
    build_indexes_main(["--root", str(repo)])
    assert "OKF605" in cli(validate_main, repo)[2]
    code, _, err = cli(validate_main, repo, "--fix-registry")
    assert code == 2
    assert "approved-move" in err
    code, _, err = cli(validate_main, repo, "--fix-registry", "--label", "approved-move")
    assert code == 0
    assert "1 registry entry updated" in err
    code, _, err = cli(validate_main, repo, "--base", "HEAD", "--label", "approved-move")
    assert code == 0, err
    assert "OKF605" in cli(validate_main, repo, "--base", "HEAD")[2]


def test_build_indexes_writes_checks_and_restricts(repo: Path, cli: Cli) -> None:
    add_content(repo)
    (repo / "knowledge" / "index.md").unlink()
    (repo / "knowledge" / "vocab" / "index.md").unlink()
    assert cli(build_indexes_main, repo, "--check")[0] == 1
    code, out, err = cli(build_indexes_main, repo, "vocab/group", "--json")
    assert code == 0
    assert sorted(json.loads(out)["written"]) == ["knowledge/index.md", "knowledge/vocab/index.md"]
    assert "knowledge/vocab/index.md" in err
    assert cli(build_indexes_main, repo)[0] == 0
    assert cli(build_indexes_main, repo, "--check")[0] == 0
    code, _, err = cli(build_indexes_main, repo, "no/such")
    assert code == 2
    assert "no such concept" in err


def test_build_indexes_removes_indexes_that_should_not_exist(repo: Path, cli: Cli) -> None:
    add_content(repo)
    stray = repo / "knowledge" / "empty" / "index.md"
    stray.parent.mkdir()
    stray.write_text("# Empty\n", encoding="utf-8")
    assert cli(build_indexes_main, repo, "--check")[0] == 1
    cli(build_indexes_main, repo)
    assert not stray.exists()


def test_new_concept_and_renumber(repo: Path, cli: Cli) -> None:
    add_content(repo)
    code, out, _ = cli(
        new_concept_main, repo, "Item", "example-group/example-category/second", "--title", "Second", "--json"
    )
    assert code == 0
    assert json.loads(out) == {"path": "knowledge/example-group/example-category/second.md", "uid": "ITM-0002"}
    assert cli(new_concept_main, repo, "Widget", "a/b/c")[0] == 2
    second = repo / "knowledge" / "example-group" / "example-category" / "second.md"
    second.write_text(second.read_text(encoding="utf-8").replace("ITM-0002", "ITM-0001"), encoding="utf-8")
    code, out, err = cli(renumber_main, repo, "example-group/example-category/second", "--json")
    assert code == 0
    assert json.loads(out) == {"concept": "example-group/example-category/second", "old": "ITM-0001", "new": "ITM-0003"}
    assert "ITM-0001 -> ITM-0003" in err
    assert cli(renumber_main, repo, "example-group/example-category/second")[0] == 2


def test_fr_2_5_the_base_tooling_judges_content_that_comes_with_a_relaxed_profile(repo: Path, cli: Cli) -> None:
    add_content(repo)
    profile_file = repo / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8").replace("reject_unknown_fields: true", "reject_unknown_fields: false"),
        encoding="utf-8",
    )
    item = repo / ITEM
    item.write_text(
        item.read_text(encoding="utf-8").replace("status: draft\n", "status: draft\ncolour: red\n"), encoding="utf-8"
    )
    assert cli(validate_main, repo)[0] == 0
    code, _, err = cli(validate_main, repo, "--tooling-from", "HEAD")
    assert code == 1
    assert "OKF203" in err


def test_a_local_run_and_a_ci_style_run_give_the_same_findings(
    repo: Path, cli: Cli, capfd: pytest.CaptureFixture[str]
) -> None:
    add_content(repo)
    commit(repo)
    local = cli(validate_main, repo, "--json")
    capfd.readouterr()
    code = validate_main(["--root", str(repo), "--tooling-from", "HEAD", "--base", "HEAD", "--json"])
    ci = capfd.readouterr().out
    assert local[0] == code == 0
    assert json.loads(ci) == json.loads(local[1])


def test_tooling_from_needs_a_ref_with_tooling(repo: Path, cli: Cli) -> None:
    add_content(repo)
    empty = git(repo, "commit-tree", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "-m", "empty").strip()
    code, _, err = cli(validate_main, repo, "--tooling-from", empty)
    assert code == 2
    assert "no tooling" in err


def test_git_problems_exit_two(repo: Path, cli: Cli, tmp_path: Path) -> None:
    add_content(repo)
    assert cli(validate_main, repo, "--base", "no-such-branch")[0] == 2
    outside = tmp_path / "not-a-repo"
    shutil.copytree(repo / "profile", outside / "profile")
    assert cli(validate_main, outside, "--base", "main")[0] == 2


def test_the_thin_scripts_run(repo: Path) -> None:
    add_content(repo)
    for script in ("validate_profile.py", "build_indexes.py"):
        done = subprocess.run(  # noqa: S603
            [sys.executable, str(repo / "scripts" / script), "--root", str(repo)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0, done.stderr
    help_text = subprocess.run(  # noqa: S603
        [sys.executable, str(repo / "scripts" / "new_concept.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "usage: new_concept.py" in help_text.stdout
