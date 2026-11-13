"""The release gate and the annotated tag (SDD W-07, C-04 ``release.py``, FR7.3, FR7.4).

A release first checks that every change merged since the previous release has its revision line, then validates
the tree, builds the archive and, in ``git-local`` mode, tags the commit with a message that records the archive's
digest. In ``github`` mode it checks only: pushing the tag runs ``release.yml``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from okfprofile.archive import SEMVER_TAG, Archive, ArchiveError, build_archive, check_tag, write_archive
from okfprofile.config import Profile
from okfprofile.gitutil import git
from okfprofile.platforms import PlatformAdapter
from okfprofile.report import Finding
from okfprofile.revision_writer import check_since

TAG_PREFIX_DIGEST = "Archive-Tar-SHA256"


class ReleaseError(Exception):
    """A release cannot start: a dirty tree, a tag that exists, or a malformed tag."""


@dataclass
class ReleaseResult:
    """What a release did.

    Attributes:
        tag: The release tag.
        previous: The tag the gate compared against, if any.
        gaps: Merged changes without a revision line (``OKF901``); a release with any stops here.
        files: Archive files written.
        tagged: True if an annotated tag was created.
        archive: The built archive, if one was built.
    """

    tag: str
    previous: str | None = None
    gaps: list[Finding] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)
    tagged: bool = False
    archive: Archive | None = None


def previous_tag(profile: Profile, ref: str = "HEAD", exclude: str | None = None) -> str | None:
    """The latest semantic-version tag reachable from ``ref``, or None before the first release.

    Args:
        profile: The loaded profile.
        ref: Where to look from.
        exclude: A tag to skip: the release being cut, which on a tag run is itself reachable from HEAD.
    """
    out = git(profile.root, "tag", "--merged", ref, "--list", "v*", "--sort=-v:refname")
    return next((t for t in out.split() if SEMVER_TAG.match(t) and t != exclude), None)


def tag_message(profile: Profile, tag: str, archive: Archive) -> str:
    """The annotated tag's message: the digests W-12 compares a rebuilt archive with."""
    archive_info = archive.manifest["archive"]
    return (
        f"{profile.library_name} {tag}\n\n"
        f"Archive: {archive_info['name']}\n"
        f"{TAG_PREFIX_DIGEST}: {archive.tar_sha256}\n"
        f"Archive-SHA256: {archive.tar_gz_sha256}\n"
        f"Python: {archive_info['python']}\n"
        f"zlib: {archive_info['zlib']}\n"
    )


def tag_digest(root: Path, tag: str) -> str | None:
    """The tar digest recorded in an annotated tag's message, or None if it records none."""
    body = git(root, "tag", "--list", tag, "--format=%(contents)")
    for line in body.splitlines():
        if line.startswith(f"{TAG_PREFIX_DIGEST}: "):
            return line.split(": ", 1)[1].strip()
    return None


def prepare(profile: Profile, tag: str, from_tag: bool = False) -> None:
    """Refuse to release from a dirty tree or over an existing tag.

    Args:
        profile: The loaded profile.
        tag: The release tag.
        from_tag: The run is the tag run itself (``release.yml``): the tag must already exist and point at HEAD.

    Raises:
        ReleaseError: If the tag is malformed, exists (or, with ``from_tag``, does not point at HEAD), or the
            working tree has uncommitted changes.
    """
    try:
        check_tag(tag)
    except ArchiveError as exc:
        raise ReleaseError(str(exc)) from exc
    exists = bool(git(profile.root, "tag", "--list", tag).strip())
    if from_tag:
        if not exists or git(profile.root, "rev-list", "-n", "1", tag) != git(profile.root, "rev-parse", "HEAD"):
            msg = f"tag {tag} does not exist or does not point at the commit checked out"
            raise ReleaseError(msg)
    elif exists:
        msg = f"tag {tag} already exists"
        raise ReleaseError(msg)
    if git(profile.root, "status", "--porcelain").strip():
        msg = "the working tree has uncommitted changes; commit or stash them before a release"
        raise ReleaseError(msg)


def run_gate(profile: Profile, adapter: PlatformAdapter, tag: str, previous: str | None = None) -> ReleaseResult:
    """The revision-line gate (FR7.4): every change merged since the previous release must have its line.

    Args:
        profile: The loaded profile.
        adapter: The platform adapter.
        tag: The release tag.
        previous: The tag to compare against; default is the latest release tag before HEAD.

    Returns:
        A result whose ``gaps`` lists each missing line.
    """
    result = ReleaseResult(tag, previous or previous_tag(profile, exclude=tag))
    result.gaps = check_since(profile, adapter, result.previous)
    return result


def finish(profile: Profile, result: ReleaseResult, out_dir: Path, create_tag: bool, sign: bool) -> ReleaseResult:
    """Build the archive and, when asked, create the annotated tag that records its digest.

    Args:
        profile: The loaded profile.
        result: The gate's result.
        out_dir: Where the archive, checksum and manifest go (``dist/``; not committed).
        create_tag: Create the annotated tag (``git-local`` only).
        sign: Sign the tag with ``git tag -s``.

    Returns:
        The result with ``archive``, ``files`` and ``tagged`` filled in.

    Raises:
        GitError: If git cannot create the tag.
    """
    archive = build_archive(profile, result.tag, "HEAD")
    result.archive = archive
    result.files = write_archive(archive, out_dir)
    if create_tag:
        flag = "-s" if sign else "-a"
        git(profile.root, "tag", flag, result.tag, "-m", tag_message(profile, result.tag, archive))
        result.tagged = True
    return result
