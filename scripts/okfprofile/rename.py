"""Rename a concept type and its ``uid`` prefix (known gap G23; ``rename_type.py``).

A library starts with the template's primary type. Renaming it touches the profile, the type's schema file, every
concept of the type, the registry and the library's own fixtures, so it is a tool rather than a hand edit. The
rename is textual and limited to the places a type name and prefix appear:

- in YAML and JSON files under ``profile/`` (not its meta-schemas in ``profile/schemas/``) and ``tests/library/``: the type name as a whole word, the prefix where
  it starts a ``uid`` (``ITM-``) or follows ``uid_prefix:``, and the schema file name;
- in Markdown files under the bundle and ``tests/library/``: the ``type:`` line and the ``uid`` prefix in the
  frontmatter only, so prose is never changed.

It runs before a library has a history worth keeping: a ``uid`` is permanent once released (FR1.3), so a library
that has released concepts of the type must not rename its prefix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from okfprofile.config import PROFILE_DIR, Profile

TYPE_NAME = re.compile(r"[A-Z][A-Za-z0-9]*")
PREFIX = re.compile(r"[A-Z]{2,5}")
DATA_SUFFIXES = (".yaml", ".yml", ".json")
LIBRARY_TESTS = Path("tests") / "library"


@dataclass
class RenameResult:
    """What a rename changed.

    Attributes:
        changed: Repository-relative paths whose text changed.
        moved: ``(old, new)`` repository-relative paths of renamed files.
    """

    changed: list[str] = field(default_factory=list)
    moved: list[tuple[str, str]] = field(default_factory=list)


def _replace_data(text: str, old: str, new: str, old_prefix: str, new_prefix: str, old_slug: str, new_slug: str) -> str:
    text = re.sub(rf"\b{re.escape(old_slug)}\.schema\.json\b", f"{new_slug}.schema.json", text)
    text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    text = re.sub(rf"(uid_prefix:\s*){re.escape(old_prefix)}\b", rf"\g<1>{new_prefix}", text)
    return re.sub(rf"\b{re.escape(old_prefix)}-", f"{new_prefix}-", text)


def _replace_frontmatter(text: str, old: str, new: str, old_prefix: str, new_prefix: str) -> str:
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return text
    for index in range(1, len(lines)):
        line = lines[index]
        if line.rstrip("\r") == "---":
            break
        line = re.sub(rf"^(type:\s*){re.escape(old)}(\s*\r?)$", rf"\g<1>{new}\g<2>", line)
        lines[index] = re.sub(rf"^(uid:\s*){re.escape(old_prefix)}-", rf"\g<1>{new_prefix}-", line)
    return "\n".join(lines)


def _files(root: Path, folders: list[Path]) -> list[Path]:
    """Files under the folders, leaving out the profile's meta-schemas, which name no type."""
    meta = root / PROFILE_DIR / "schemas"
    found: list[Path] = []
    for folder in folders:
        if folder.is_dir():
            found.extend(p for p in folder.rglob("*") if p.is_file() and meta not in p.parents)
    return sorted(set(found))


def _check_names(profile: Profile, old: str, new: str, new_prefix: str) -> str:
    """Check the rename and return the old ``uid`` prefix."""
    declared = profile.type_named(old)
    if declared is None:
        msg = f"type '{old}' is not declared; declared: {', '.join(t.name for t in profile.types)}"
        raise ValueError(msg)
    if not TYPE_NAME.fullmatch(new):
        msg = f"'{new}' must start with a capital letter and hold only letters and digits"
        raise ValueError(msg)
    if not PREFIX.fullmatch(new_prefix):
        msg = f"'{new_prefix}' must be two to five capital letters"
        raise ValueError(msg)
    others = [t for t in profile.types if t.name != old]
    if any(t.name == new for t in others) or any(t.uid_prefix == new_prefix for t in others):
        msg = f"'{new}' or '{new_prefix}' is already used by another type"
        raise ValueError(msg)
    return declared.uid_prefix


def rename_type(profile: Profile, old: str, new: str, new_prefix: str, dry_run: bool = False) -> RenameResult:
    """Rename a declared type and its ``uid`` prefix everywhere the library uses them.

    Args:
        profile: The loaded profile.
        old: The declared type name, such as ``Item``.
        new: The new type name, such as ``Risk``.
        new_prefix: The new ``uid`` prefix, such as ``RSK``.
        dry_run: Report what would change without writing.

    Returns:
        The files changed and moved.

    Raises:
        ValueError: If the old type is not declared, the new name or prefix is malformed, or either is already
            used by another type.
    """
    old_prefix = _check_names(profile, old, new, new_prefix)
    root = profile.root
    old_slug, new_slug = old.lower(), new.lower()
    result = RenameResult()
    for file in _files(root, [root / PROFILE_DIR, profile.bundle_root, root / LIBRARY_TESTS]):
        text = file.read_bytes().decode("utf-8", errors="strict")
        if file.suffix in DATA_SUFFIXES:
            updated = _replace_data(text, old, new, old_prefix, new_prefix, old_slug, new_slug)
        elif file.suffix == ".md":
            updated = _replace_frontmatter(text, old, new, old_prefix, new_prefix)
        else:
            continue
        if updated != text:
            result.changed.append(file.relative_to(root).as_posix())
            if not dry_run:
                file.write_bytes(updated.encode("utf-8"))
    for file in _files(root, [root / PROFILE_DIR, root / LIBRARY_TESTS]):
        if file.name == f"{old_slug}.schema.json":
            target = file.with_name(f"{new_slug}.schema.json")
            result.moved.append((file.relative_to(root).as_posix(), target.relative_to(root).as_posix()))
            if not dry_run:
                file.rename(target)
    return result
