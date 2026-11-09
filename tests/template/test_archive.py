"""The reproducible release archive (plan step 8, FR7.3, SDD I-12, ADR-004, V-12)."""

import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

import pytest
from okfprofile.archive import (
    ARCHIVE_FILES,
    ArchiveError,
    Member,
    build_archive,
    build_tar,
    check_tag,
    gzip_bytes,
    rebuild_problems,
    select_members,
    verify_archive,
    write_archive,
)
from okfprofile.bundle import load_bundle
from okfprofile.config import Profile, load_profile
from okfprofile.indexes import write_indexes
from okfprofile.release_cli import build_bundle_main
from okfprofile.revision_writer import reset_history
from support import ROOT

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

# The tar of a fixed set of files, with a fixed timestamp, is the same on every system and Python (V-12).
GOLDEN_FILES = [
    Member("README.md", 0o644, b"# T\r\nline\n"),
    Member("knowledge/a.md", 0o644, "café\n".encode()),
    Member("profile/run.sh", 0o755, b"#!/bin/sh\n"),
    Member("x" * 120 + "/long.md", 0o644, b"long\n"),
]
GOLDEN_TAR_SHA256 = "c6a50787a6187ee79aeba45efee7eeff8cc0d25a05774fa2526550980258abe5"
STAMP = "2026-11-01T10:00:00+00:00"


def git(root: Path, *args: str, when: str | None = None) -> str:
    env = dict(os.environ)
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, env=env, text=True)  # noqa: S603, S607
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A scratch repository: the real profile and example bundle, entry-point files, and files that must not ship."""
    root = tmp_path / "lib"
    for name in ("profile", "knowledge"):
        shutil.copytree(ROOT / name, root / name)
    reset_history(load_profile(root), root)  # the template's own bot commits have written lines into the examples
    write_indexes(load_profile(root), load_bundle(root / "knowledge", root))
    for name, text in {
        "README.md": "# Lib\n",
        "LICENSE": "licence\n",
        "NOTICE": "notice\n",
        "AGENTS.md": "agents\n",
    }.items():
        (root / name).write_text(text, encoding="utf-8", newline="\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "tool.py").write_text("print()\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("internal\n", encoding="utf-8")
    (root / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.org")
    git(root, "config", "user.name", "T")
    git(root, "config", "core.autocrlf", "false")
    git(root, "add", "-A")
    git(root, "update-index", "--chmod=+x", "profile/formats/check.md")
    git(root, "commit", "-q", "-m", "base", when=STAMP)
    return root


@pytest.fixture
def profile(repo: Path) -> Profile:
    return load_profile(repo)


@pytest.mark.parametrize("tag", ["v0.0.1", "v1.2.3", "v10.20.30", "v1.0.0-beta.1", "v1.0.0-rc1"])
def test_semantic_version_tags_are_accepted(tag: str) -> None:
    assert check_tag(tag) == tag


@pytest.mark.parametrize("tag", ["1.0.0", "v1.0", "v01.0.0", "v1.0.0+build", "latest", "v1.0.0-", ""])
def test_other_tags_are_refused(tag: str) -> None:
    with pytest.raises(ArchiveError, match="semantic-version tag"):
        check_tag(tag)


def test_the_tar_of_fixed_content_has_a_fixed_digest() -> None:
    tar = build_tar("lib-v1.0.0", GOLDEN_FILES, 1_700_000_000)
    assert hashlib.sha256(tar).hexdigest() == GOLDEN_TAR_SHA256


def test_the_tar_is_normalised() -> None:
    tar = build_tar("lib-v1.0.0", GOLDEN_FILES, 1_700_000_000)
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        members = archive.getmembers()
        assert [m.name for m in members] == ["lib-v1.0.0/" + f.path for f in GOLDEN_FILES]
        assert {(m.uid, m.gid, m.uname, m.gname, m.mtime) for m in members} == {(0, 0, "", "", 1_700_000_000)}
        assert [m.mode for m in members] == [0o644, 0o644, 0o755, 0o644]
        assert all(m.isfile() for m in members)
        assert archive.extractfile(members[0]).read() == b"# T\r\nline\n"  # type: ignore[union-attr]  # a regular file


def test_the_gzip_header_carries_no_name_and_no_timestamp() -> None:
    packed = gzip_bytes(b"data" * 100)
    assert packed[3] == 0
    assert packed[4:8] == b"\0\0\0\0"
    assert gzip.decompress(packed) == b"data" * 100


def test_the_archive_holds_the_bundle_the_profile_and_the_entry_files_only(repo: Path) -> None:
    members = select_members(repo, "HEAD")
    paths = [m.path for m in members]
    assert paths == sorted(paths, key=lambda p: p.encode())
    assert {p.split("/")[0] for p in paths} == {"AGENTS.md", "LICENSE", "NOTICE", "README.md", "knowledge", "profile"}
    assert all(p in ARCHIVE_FILES or p.startswith(("knowledge/", "profile/")) for p in paths)
    assert "knowledge/example-group/example-category/example-item.md" in paths
    assert "profile/uid-registry.yaml" in paths
    modes = {m.path: m.mode for m in members}
    assert modes["profile/formats/check.md"] == 0o755
    assert modes["README.md"] == 0o644


def test_files_are_read_from_git_not_from_the_working_tree(repo: Path) -> None:
    (repo / "README.md").write_text("changed after the commit\n", encoding="utf-8")
    assert {m.path: m.data for m in select_members(repo, "HEAD")}["README.md"] == b"# Lib\n"


def test_committed_line_endings_are_kept(repo: Path) -> None:
    (repo / "NOTICE").write_bytes(b"one\r\ntwo\r\n")
    git(repo, "commit", "-qam", "crlf", when=STAMP)
    assert {m.path: m.data for m in select_members(repo, "HEAD")}["NOTICE"] == b"one\r\ntwo\r\n"


def test_an_archive_is_built_from_the_tag_with_a_manifest(repo: Path, profile: Profile) -> None:
    git(repo, "tag", "v0.1.0")
    archive = build_archive(profile, "v0.1.0", "v0.1.0")
    manifest = archive.manifest
    assert manifest["tag"] == "v0.1.0"
    assert manifest["commit"] == git(repo, "rev-parse", "HEAD")
    assert manifest["commit_time"] == "2026-11-01T10:00:00Z"
    assert manifest["library"] == "okf-library-template"
    assert manifest["okf"] == {"version": "0.2", "spec_commit": "ad30107"}
    assert manifest["concepts"] == {
        "total": 4,
        "by_type": {"Glossary": 1, "Item": 1, "Vocabulary": 2},
        "by_status": {"draft": 4},
        "by_tier": {"unverified": 4},
    }
    assert manifest["archive"]["name"] == "okf-library-template-v0.1.0.tar.gz"
    assert manifest["archive"]["tar_sha256"] == archive.tar_sha256
    assert {"python", "zlib", "tar_gz_sha256"} <= set(manifest["archive"])
    assert manifest["files"] == len(select_members(repo, "HEAD"))
    with tarfile.open(fileobj=io.BytesIO(archive.tar)) as tar:
        assert tar.getnames()[0].startswith("okf-library-template-v0.1.0/")
        assert {m.mtime for m in tar.getmembers()} == {int(datetime.fromisoformat(STAMP).timestamp())}


def test_building_twice_gives_identical_bytes(profile: Profile) -> None:
    first = build_archive(profile, "v0.1.0")
    second = build_archive(profile, "v0.1.0")
    assert (first.tar, first.tar_gz) == (second.tar, second.tar_gz)


def test_a_rebuild_from_a_clone_at_the_tag_reproduces_the_digest(repo: Path, profile: Profile, tmp_path: Path) -> None:
    git(repo, "tag", "v0.1.0")
    recorded = build_archive(profile, "v0.1.0", "v0.1.0")
    (repo / "README.md").write_text("later work\n", encoding="utf-8")
    git(repo, "commit", "-qam", "later", when="2026-11-05T10:00:00+00:00")
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(repo), str(clone))
    git(clone, "checkout", "-q", "v0.1.0")
    assert rebuild_problems(load_profile(clone), recorded.manifest, "v0.1.0") == []
    assert build_archive(load_profile(clone), "v0.1.0", "v0.1.0").tar_sha256 == recorded.tar_sha256


def test_a_rebuild_from_another_commit_does_not_match(repo: Path, profile: Profile) -> None:
    recorded = build_archive(profile, "v0.1.0")
    (repo / "README.md").write_text("later work\n", encoding="utf-8")
    git(repo, "commit", "-qam", "later", when="2026-11-05T10:00:00+00:00")
    assert rebuild_problems(profile, recorded.manifest, "HEAD") == [
        "the tar rebuilt from HEAD differs from the manifest"
    ]


def test_the_archive_files_are_written_with_a_checksum_in_sha256sum_format(profile: Profile, tmp_path: Path) -> None:
    archive = build_archive(profile, "v0.1.0")
    gz, checksum, manifest = write_archive(archive, tmp_path / "dist")
    assert [p.name for p in (gz, checksum, manifest)] == [
        "okf-library-template-v0.1.0.tar.gz",
        "okf-library-template-v0.1.0.tar.gz.sha256",
        "okf-library-template-v0.1.0.manifest.json",
    ]
    assert checksum.read_text(encoding="utf-8") == f"{hashlib.sha256(gz.read_bytes()).hexdigest()}  {gz.name}\n"
    assert json.loads(manifest.read_text(encoding="utf-8")) == archive.manifest
    with tarfile.open(gz) as unpacked:
        assert unpacked.getnames()


def test_verification_compares_the_tar_digest_and_the_gzip_digest_only_for_the_same_build(
    profile: Profile, tmp_path: Path
) -> None:
    archive = build_archive(profile, "v0.1.0")
    gz = write_archive(archive, tmp_path)[0]
    manifest = json.loads(json.dumps(archive.manifest))
    assert verify_archive(gz, manifest) == []
    other_build = json.loads(json.dumps(manifest))
    other_build["archive"]["zlib"] = "0.0.0"
    other_build["archive"]["tar_gz_sha256"] = "0" * 64
    assert verify_archive(gz, other_build) == []
    same_build = json.loads(json.dumps(manifest))
    same_build["archive"]["tar_gz_sha256"] = "0" * 64
    assert "the .tar.gz digest differs" in verify_archive(gz, same_build)[0]
    wrong_tar = json.loads(json.dumps(manifest))
    wrong_tar["archive"]["tar_sha256"] = "0" * 64
    assert "the tar digest differs" in verify_archive(gz, wrong_tar)[0]


def test_a_file_that_is_not_gzip_is_reported(profile: Profile, tmp_path: Path) -> None:
    bad = tmp_path / "x.tar.gz"
    bad.write_bytes(b"not gzip")
    assert "not a readable gzip file" in verify_archive(bad, {})[0]


def test_an_empty_commit_has_nothing_to_archive(tmp_path: Path) -> None:
    root = tmp_path / "bare"
    shutil.copytree(ROOT / "profile", root / "profile")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.org")
    git(root, "config", "user.name", "T")
    (root / "other.txt").write_text("x\n", encoding="utf-8")
    git(root, "add", "other.txt")
    git(root, "commit", "-q", "-m", "x", when=STAMP)
    with pytest.raises(ArchiveError, match="nothing to archive"):
        build_archive(load_profile(root), "v0.1.0")


def test_the_command_line_builds_verifies_and_rebuild_checks(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "dist"
    assert build_bundle_main(["--root", str(repo), "--tag", "v0.1.0", "--out", str(out), "--json"]) == 0
    built = json.loads(capsys.readouterr().out)
    assert len(built["files"]) == 3
    gz = out / "okf-library-template-v0.1.0.tar.gz"
    manifest = out / "okf-library-template-v0.1.0.manifest.json"
    assert build_bundle_main(["--root", str(repo), "--verify", str(gz), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True, "problems": []}
    assert build_bundle_main(["--root", str(repo), "--rebuild-check", str(manifest)]) == 0
    gz.write_bytes(gzip.compress(b"tampered"))
    assert build_bundle_main(["--root", str(repo), "--verify", str(gz), "--manifest", str(manifest)]) == 1


def test_the_command_line_reports_what_it_cannot_do(repo: Path, tmp_path: Path) -> None:
    assert build_bundle_main(["--root", str(repo)]) == 2
    assert build_bundle_main(["--root", str(repo), "--tag", "latest"]) == 2
    assert build_bundle_main(["--root", str(repo), "--verify", str(tmp_path / "missing.tar.gz")]) == 2
    assert build_bundle_main(["--root", str(tmp_path / "nowhere"), "--tag", "v0.1.0"]) == 2
