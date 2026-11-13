"""The release archive: a reproducible tar of the bundle, its checksum and its manifest (SDD I-12, ADR-004).

The archive is built from the files in git at a commit, not from the working tree, so a rebuild from the tag gives
the same bytes. Entries are sorted by path, modes are normalised, owner and group are 0 with empty names, and
every modification time is the commit's timestamp. The gzip stream depends on the zlib in use (zlib-ng differs from
zlib), so the canonical hash is the SHA-256 of the uncompressed tar; the ``.tar.gz`` digest is compared only when
the Python and zlib versions recorded in the manifest are the ones running now.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import platform
import posixpath
import re
import tarfile
import zlib
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from okfprofile.bundle import RESERVED_NAMES
from okfprofile.config import Profile
from okfprofile.document import parse_concept
from okfprofile.gitutil import commit_info, read_blobs, tree_entries
from okfprofile.history import history_lines
from okfprofile.revision import concept_tier

RELEASE_FILE = "RELEASE"
ARCHIVE_FOLDERS = ("knowledge", "profile", ".agents/skills/use-bundle")
ARCHIVE_FILES = ("AGENTS.md", "README.md", "CITATION.cff", "LICENSE", "LICENSE-content", "LICENSE-template", "NOTICE")
SEMVER_TAG = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z][0-9A-Za-z.-]*)?$")
EXECUTABLE = "100755"
MODE_FILE, MODE_EXECUTABLE = 0o644, 0o755


class ArchiveError(Exception):
    """The archive cannot be built or does not match its manifest."""


@dataclass(frozen=True)
class Member:
    """A file that goes into the archive.

    Attributes:
        path: Path in the repository, forward slashes.
        mode: Normalised permission bits (0o644, or 0o755 for an executable).
        data: File content as committed.
    """

    path: str
    mode: int
    data: bytes


@dataclass(frozen=True)
class Archive:
    """A built archive.

    Attributes:
        name: Base name, ``<library>-<tag>``.
        tar: The uncompressed tar.
        tar_gz: The compressed archive.
        manifest: The manifest as a dict.
    """

    name: str
    tar: bytes
    tar_gz: bytes
    manifest: dict[str, Any]

    @property
    def tar_sha256(self) -> str:
        """SHA-256 of the uncompressed tar: the canonical content hash."""
        return hashlib.sha256(self.tar).hexdigest()

    @property
    def tar_gz_sha256(self) -> str:
        """SHA-256 of the ``.tar.gz``."""
        return hashlib.sha256(self.tar_gz).hexdigest()


def check_tag(tag: str) -> str:
    """Return ``tag`` if it is a semantic-version tag such as ``v1.2.3`` or ``v1.0.0-beta.1``.

    Raises:
        ArchiveError: Otherwise.
    """
    if not SEMVER_TAG.match(tag):
        msg = f"'{tag}' is not a semantic-version tag (vMAJOR.MINOR.PATCH, optional -prerelease)"
        raise ArchiveError(msg)
    return tag


def select_members(root: Path, ref: str) -> list[Member]:
    """The files of the archive, read from git at ``ref`` and sorted by path.

    Args:
        root: Repository root.
        ref: Commit, tag or branch.

    Returns:
        The bundle, the profile, the consuming skill and the entry-point and licence files that exist at ``ref``.
    """
    wanted = [
        (mode, blob, path)
        for mode, blob, path in tree_entries(root, ref)
        if path in ARCHIVE_FILES or any(path.startswith(f"{folder}/") for folder in ARCHIVE_FOLDERS)
    ]
    blobs = read_blobs(root, [blob for _, blob, _ in wanted])
    members = [
        Member(path, MODE_EXECUTABLE if mode == EXECUTABLE else MODE_FILE, blobs[blob]) for mode, blob, path in wanted
    ]
    return sorted(members, key=lambda m: m.path.encode("utf-8"))


def release_file(library: str, tag: str, sha: str, stamp: int) -> Member:
    """The release-identity file ``RELEASE``: the tag, commit and commit date an agent cites (FR7.2).

    It is made from the commit's own data, never from the clock, so a rebuild from the tag is identical (ADR-004).
    """
    date = datetime.fromtimestamp(stamp, UTC).isoformat().replace("+00:00", "Z")
    text = f"library: {library}\ntag: {tag}\ncommit: {sha}\ndate: {date}\n"
    return Member(RELEASE_FILE, MODE_FILE, text.encode("utf-8"))


def build_tar(top: str, members: list[Member], mtime: int) -> bytes:
    """A deterministic tar of ``members`` under the folder ``top``.

    Args:
        top: Folder name inside the archive.
        members: Files, already sorted.
        mtime: Modification time of every entry, seconds since the epoch.

    Returns:
        The tar bytes (GNU format, files only, owner and group 0 with empty names).
    """
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for member in members:
            info = tarfile.TarInfo(posixpath.join(top, member.path))
            info.size = len(member.data)
            info.mtime = mtime
            info.mode = member.mode
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(member.data))
    return buffer.getvalue()


def gzip_bytes(tar: bytes) -> bytes:
    """Compress ``tar`` with no file name and no timestamp in the gzip header."""
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0, compresslevel=9) as stream:
        stream.write(tar)
    return buffer.getvalue()


def concept_counts(profile: Profile, members: list[Member]) -> dict[str, Any]:
    """Count the concepts in the archive by type, status and trust tier."""
    bundle = profile.bundle_root.relative_to(profile.root).as_posix() + "/"
    types: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    tiers: Counter[str] = Counter()
    for member in members:
        name = posixpath.basename(member.path)
        if not member.path.startswith(bundle) or not name.endswith(".md") or name in RESERVED_NAMES:
            continue
        concept = parse_concept(member.data.decode("utf-8"), member.path)
        meta = concept.frontmatter or {}
        types[str(meta.get("type", ""))] += 1
        statuses[str(meta.get("status", ""))] += 1
        tiers[concept_tier(history_lines(profile, concept), profile.rules.require_non_author_approver).label] += 1
    return {
        "total": sum(types.values()),
        "by_type": dict(sorted(types.items())),
        "by_status": dict(sorted(statuses.items())),
        "by_tier": dict(sorted(tiers.items())),
    }


def build_archive(profile: Profile, tag: str, ref: str = "HEAD") -> Archive:
    """Build the release archive from the files in git at ``ref``.

    Args:
        profile: The loaded profile (library name, versions and platform go into the manifest).
        tag: The release tag, for example ``v0.2.0``.
        ref: The commit to build from; for a release, the tag itself.

    Returns:
        The archive. Trust-tier counts use the profile in the working tree.

    Raises:
        ArchiveError: If the tag is malformed or the commit holds nothing to archive.
    """
    check_tag(tag)
    sha, stamp = commit_info(profile.root, ref)
    members = select_members(profile.root, ref)
    if not members:
        msg = f"nothing to archive at {ref}"
        raise ArchiveError(msg)
    members = sorted([*members, release_file(profile.library_name, tag, sha, stamp)], key=lambda m: m.path.encode())
    name = f"{profile.library_name}-{tag}"
    tar = build_tar(name, members, stamp)
    tar_gz = gzip_bytes(tar)
    manifest = {
        "tag": tag,
        "commit": sha,
        "commit_time": datetime.fromtimestamp(stamp, UTC).isoformat().replace("+00:00", "Z"),
        "library": profile.library_name,
        "platform": profile.platform,
        "profile": {"name": profile.name, "version": profile.profile_version},
        "okf": {"version": profile.okf_version, "spec_commit": profile.okf_spec_commit},
        "template_version": profile.template_version,
        "concepts": concept_counts(profile, members),
        "files": len(members),
        "archive": {
            "name": f"{name}.tar.gz",
            "tar_sha256": hashlib.sha256(tar).hexdigest(),
            "tar_gz_sha256": hashlib.sha256(tar_gz).hexdigest(),
            "python": platform.python_version(),
            "zlib": zlib.ZLIB_RUNTIME_VERSION,
        },
    }
    return Archive(name, tar, tar_gz, manifest)


def write_archive(archive: Archive, out_dir: Path) -> list[Path]:
    """Write the ``.tar.gz``, its ``.sha256`` (``sha256sum`` format) and the manifest into ``out_dir``.

    Returns:
        The three paths.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    gz = out_dir / f"{archive.name}.tar.gz"
    gz.write_bytes(archive.tar_gz)
    checksum = out_dir / f"{archive.name}.tar.gz.sha256"
    checksum.write_text(f"{archive.tar_gz_sha256}  {gz.name}\n", encoding="utf-8", newline="\n")
    manifest = out_dir / f"{archive.name}.manifest.json"
    manifest.write_text(json.dumps(archive.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return [gz, checksum, manifest]


def verify_archive(path: Path, manifest: dict[str, Any]) -> list[str]:
    """Check an archive against its manifest.

    The tar digest is always compared. The ``.tar.gz`` digest is compared only when the Python and zlib versions
    recorded in the manifest are the ones running now (ADR-004).

    Args:
        path: The ``.tar.gz``.
        manifest: The manifest.

    Returns:
        Problems found; empty if the archive matches.
    """
    recorded = manifest.get("archive", {})
    data = path.read_bytes()
    problems = []
    try:
        tar = gzip.decompress(data)
    except (OSError, EOFError) as exc:
        return [f"{path.name}: not a readable gzip file: {exc}"]
    if hashlib.sha256(tar).hexdigest() != recorded.get("tar_sha256"):
        problems.append(f"{path.name}: the tar digest differs from the manifest")
    same_build = (recorded.get("python"), recorded.get("zlib")) == (
        platform.python_version(),
        zlib.ZLIB_RUNTIME_VERSION,
    )
    if same_build and hashlib.sha256(data).hexdigest() != recorded.get("tar_gz_sha256"):
        problems.append(f"{path.name}: the .tar.gz digest differs from the manifest (same Python and zlib)")
    return problems


def rebuild_problems(profile: Profile, manifest: dict[str, Any], ref: str) -> list[str]:
    """Rebuild the archive from ``ref`` and compare its tar digest with the manifest's (W-12 step 5).

    Args:
        profile: The loaded profile.
        manifest: The recorded manifest.
        ref: Tag or commit to rebuild from.

    Returns:
        Problems found; empty if the rebuilt tar matches.
    """
    archive = build_archive(profile, str(manifest.get("tag", "")), ref)
    if archive.tar_sha256 != manifest.get("archive", {}).get("tar_sha256"):
        return [f"the tar rebuilt from {ref} differs from the manifest"]
    return []
