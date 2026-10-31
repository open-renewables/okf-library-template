"""Fixtures: build a scratch repository from the real profile and a few files."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from okfprofile.config import Profile, load_profile
from okfprofile.registry import Registry, RegistryEntry, save_registry
from support import DEFAULT_REGISTRY, DEFAULT_VOCABS, ROOT, MakeRepo


@pytest.fixture
def make_repo(tmp_path: Path) -> MakeRepo:
    """Factory: ``make_repo(files, registry=None, profile_edit=None, vocabs=True)`` returns the loaded profile.

    ``files`` maps paths under ``knowledge/`` to text. Vocabulary concepts for the two example namespaces and their
    registry entries are added unless ``vocabs`` is false. ``profile_edit`` is a function applied to the text of
    ``profile.yaml``.
    """

    def build(
        files: dict[str, str],
        registry: dict[str, RegistryEntry] | None = None,
        profile_edit: Callable[[str], str] | None = None,
        vocabs: bool = True,
    ) -> Profile:
        shutil.copytree(ROOT / "profile", tmp_path / "profile")
        if profile_edit:
            path = tmp_path / "profile" / "profile.yaml"
            path.write_text(profile_edit(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        everything = {**(DEFAULT_VOCABS if vocabs else {}), **files}
        for rel, text in everything.items():
            target = tmp_path / "knowledge" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        entries = {**(DEFAULT_REGISTRY if vocabs else {}), **(registry or {})}
        save_registry(tmp_path, Registry(entries))
        return load_profile(tmp_path)

    return build
