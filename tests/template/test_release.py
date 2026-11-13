"""The release gate and the annotated tag (plan step 8, FR7.3, FR7.4, W-07)."""

import json
import shutil
from pathlib import Path

import pytest
from okfprofile import release_cli
from okfprofile.archive import build_archive, rebuild_problems
from okfprofile.codeowners import parse_codeowners
from okfprofile.config import load_profile
from okfprofile.platforms.git_local import GitLocalAdapter
from okfprofile.release import ReleaseError, prepare, previous_tag, run_gate, tag_digest, tag_message
from okfprofile.release_cli import release_main
from okfprofile.revision_writer import catch_up, commit_revision
from support import PATH, edit, git

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def record(root: Path) -> None:
    """Run the revision writer from the beginning of history and commit its result, as `poe revision` does."""
    profile = load_profile(root)
    owners = parse_codeowners((root / ".github" / "CODEOWNERS").read_text(encoding="utf-8"))
    commit_revision(root, catch_up(profile, GitLocalAdapter(profile), owners).files)


def test_the_previous_release_is_the_latest_semantic_version_tag(library: Path) -> None:
    profile = load_profile(library)
    assert previous_tag(profile) is None
    for tag in ("v0.0.1", "v0.0.10", "v0.0.2", "notes", "v1.0"):
        git(library, "tag", tag)
    assert previous_tag(profile) == "v0.0.10"
    git(library, "tag", "v0.1.0")
    assert previous_tag(profile) == "v0.1.0"


def test_a_release_needs_a_clean_tree_a_new_tag_and_a_semantic_version(library: Path) -> None:
    profile = load_profile(library)
    prepare(profile, "v0.1.0")
    with pytest.raises(ReleaseError, match="semantic-version"):
        prepare(profile, "latest")
    git(library, "tag", "v0.1.0")
    with pytest.raises(ReleaseError, match="already exists"):
        prepare(profile, "v0.1.0")
    (library / "README.md").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ReleaseError, match="uncommitted"):
        prepare(profile, "v0.2.0")


def test_the_gate_lists_every_merged_change_without_a_line(library: Path) -> None:
    git(library, "tag", "v0.0.1")
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00", tag="one")
    profile = load_profile(library)
    result = run_gate(profile, GitLocalAdapter(profile), "v0.1.0")
    assert result.previous == "v0.0.1"
    assert [f.code for f in result.gaps] == ["OKF901"]


def test_a_release_with_a_missing_revision_line_fails_and_changes_nothing(
    library: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    out = tmp_path / "dist"
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(out)]) == 1
    assert "have no revision line" in capsys.readouterr().err
    assert not out.exists()
    assert git(library, "tag", "--list") == ""


def test_a_git_local_release_builds_the_archive_and_tags_it_with_its_digest(
    library: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    record(library)
    out = tmp_path / "dist"
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(out), "--dry-run", "--json"]) == 0
    dry = json.loads(capsys.readouterr().out)
    assert dry["tagged"] is False and dry["previous"] is None
    assert git(library, "tag", "--list") == ""
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(out), "--json"]) == 0
    done = json.loads(capsys.readouterr().out)
    assert done["tagged"] is True
    assert git(library, "cat-file", "-t", "v0.1.0") == "tag"
    assert tag_digest(library, "v0.1.0") == done["archive"]["tar_sha256"] == dry["archive"]["tar_sha256"]
    manifest = json.loads((out / "okf-library-template-v0.1.0.manifest.json").read_text(encoding="utf-8"))
    assert manifest["platform"] == "git-local"
    assert manifest["concepts"]["by_tier"] == {"machine-confirmed": 4}
    assert rebuild_problems(load_profile(library), manifest, "v0.1.0") == []
    message = git(library, "tag", "--list", "v0.1.0", "--format=%(contents)")
    assert message.startswith("okf-library-template v0.1.0\n")
    assert "Archive: okf-library-template-v0.1.0.tar.gz" in message


def test_the_tag_message_records_the_digests_and_the_build(library: Path) -> None:
    profile = load_profile(library)
    archive = build_archive(profile, "v0.1.0")
    message = tag_message(profile, "v0.1.0", archive)
    assert f"Archive-Tar-SHA256: {archive.tar_sha256}\n" in message
    assert f"Archive-SHA256: {archive.tar_gz_sha256}\n" in message
    assert "Python: " in message and "zlib: " in message
    assert tag_digest(library, "v0.1.0") is None


def test_a_second_release_checks_only_the_changes_since_the_first(library: Path, tmp_path: Path) -> None:
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00", tag="one")
    record(library)
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(tmp_path / "a")]) == 0
    assert release_main(["v0.2.0", "--root", str(library), "--out", str(tmp_path / "b")]) == 0
    edit(library, "alice", "Edit two", "2026-11-02T10:00:00+00:00", tag="two")
    assert release_main(["v0.3.0", "--root", str(library), "--out", str(tmp_path / "c")]) == 1
    record(library)
    assert release_main(["v0.3.0", "--root", str(library), "--out", str(tmp_path / "c")]) == 0


def test_a_failed_validation_stops_the_release(
    library: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    record(library)
    file = library / PATH
    file.write_text(
        file.read_text(encoding="utf-8").replace("status: draft", "status: bogus"), encoding="utf-8", newline="\n"
    )
    git(library, "commit", "-qam", "break it", when="2026-11-02T10:00:00+00:00")
    record(library)
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(tmp_path / "d")]) == 1
    assert "validation failed" in capsys.readouterr().err
    assert git(library, "tag", "--list") == ""


def test_a_github_release_only_checks(
    library: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    record(library)
    profile_file = library / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8").replace("platform: git-local", "platform: github"),
        encoding="utf-8",
        newline="\n",
    )
    git(library, "commit", "-qam", "move to github", when="2026-11-02T10:00:00+00:00")
    record(library)
    monkeypatch.setattr(release_cli, "make_adapter", lambda profile, _repo=None: GitLocalAdapter(profile))
    out = tmp_path / "dist"
    assert release_main(["v0.1.0", "--root", str(library), "--out", str(out)]) == 0
    assert "push the tag v0.1.0 to run the release workflow" in capsys.readouterr().err
    assert not out.exists()
    assert git(library, "tag", "--list") == ""


def test_the_tag_run_gates_against_the_tag_before_it_and_not_against_itself(library: Path) -> None:
    profile = load_profile(library)
    git(library, "tag", "v0.0.1")
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00", tag="one")
    git(library, "tag", "v0.1.0")
    assert previous_tag(profile) == "v0.1.0"
    assert previous_tag(profile, exclude="v0.1.0") == "v0.0.1"
    result = run_gate(profile, GitLocalAdapter(profile), "v0.1.0")
    assert result.previous == "v0.0.1"
    assert [f.code for f in result.gaps] == ["OKF901"]


def test_a_tag_run_needs_the_tag_to_exist_and_point_at_the_checked_out_commit(library: Path) -> None:
    profile = load_profile(library)
    with pytest.raises(ReleaseError, match="does not exist or does not point"):
        prepare(profile, "v0.1.0", from_tag=True)
    git(library, "tag", "v0.1.0")
    prepare(profile, "v0.1.0", from_tag=True)
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    with pytest.raises(ReleaseError, match="does not exist or does not point"):
        prepare(profile, "v0.1.0", from_tag=True)
    with pytest.raises(ReleaseError, match="semantic-version"):
        prepare(profile, "latest", from_tag=True)


def test_a_deleted_revision_line_fails_the_tag_run_and_the_restored_line_passes(
    library: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """AT-FR7.4-01 on the command line the release workflow calls (`--from-tag`)."""
    edit(library, "alice", "Edit one", "2026-11-01T10:00:00+00:00")
    record(library)
    git(library, "tag", "v0.0.1")
    edit(library, "alice", "Edit two", "2026-11-02T10:00:00+00:00", tag="two")  # merged; its line is missing
    git(library, "tag", "v0.0.2")
    monkeypatch.setattr(release_cli, "make_adapter", lambda profile, _repo=None: GitLocalAdapter(profile))
    args = ["v0.0.2", "--root", str(library), "--out", str(tmp_path / "dist"), "--from-tag"]
    assert release_main(args) == 1
    assert "OKF901" in capsys.readouterr().err
    record(library)
    git(library, "tag", "-d", "v0.0.2")
    git(library, "tag", "v0.0.2")
    assert release_main(args) == 0


def test_the_command_line_reports_what_it_cannot_do(library: Path, tmp_path: Path) -> None:
    assert release_main(["latest", "--root", str(library)]) == 2
    (library / "README.md").write_text("dirty\n", encoding="utf-8")
    assert release_main(["v0.1.0", "--root", str(library)]) == 2
    assert release_main(["v0.1.0", "--root", str(tmp_path / "nowhere")]) == 2
