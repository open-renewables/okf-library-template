"""Fixtures: build a scratch repository from the real profile and a few files."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.config import Profile, load_profile
from okfprofile.indexes import write_indexes
from okfprofile.registry import Registry, RegistryEntry, save_registry
from okfprofile.revision_writer import reset_history
from support import DEFAULT_REGISTRY, DEFAULT_VOCABS, ROOT, MakeRepo, git


@pytest.fixture
def make_repo(tmp_path: Path) -> MakeRepo:
    """Factory: ``make_repo(files, registry=None, profile_edit=None, vocabs=True)`` returns the loaded profile.

    ``files`` maps paths under ``knowledge/`` to text. Vocabulary concepts for the two example namespaces and their
    registry entries are added unless ``vocabs`` is false. ``profile_edit`` is a function applied to the text of
    ``profile.yaml``. Indexes are generated unless ``indexes`` is false.
    """
    count = 0

    def build(
        files: dict[str, str],
        registry: dict[str, RegistryEntry] | None = None,
        profile_edit: Callable[[str], str] | None = None,
        vocabs: bool = True,
        indexes: bool = True,
    ) -> Profile:
        nonlocal count
        count += 1
        repo = tmp_path / f"repo{count}"
        shutil.copytree(ROOT / "profile", repo / "profile")
        if profile_edit:
            path = repo / "profile" / "profile.yaml"
            path.write_text(profile_edit(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        everything = {**(DEFAULT_VOCABS if vocabs else {}), **files}
        for rel, text in everything.items():
            target = repo / "knowledge" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        entries = {**(DEFAULT_REGISTRY if vocabs else {}), **(registry or {})}
        save_registry(repo, Registry(entries))
        profile = load_profile(repo)
        if indexes:
            write_indexes(profile, load_bundle(profile.bundle_root, repo))
        return profile

    return build


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
    reset_history(load_profile(root), root)  # the template's own bot commits have written lines into the examples
    write_indexes(load_profile(root), load_bundle(root / "knowledge", root))
    (root / ".github").mkdir()
    (root / ".github" / "CODEOWNERS").write_text("/knowledge/ @alice\n", encoding="utf-8", newline="\n")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "bot@example.org")
    git(root, "config", "user.name", "Bot")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base", when="2026-10-31T09:00:00+00:00")
    return root
