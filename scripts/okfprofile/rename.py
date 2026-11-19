"""Rename a concept type and its ``uid`` prefix (known gap G23; ``rename_type.py``).

A library starts with the template's primary type. Renaming it touches the profile, the type's schema file, every
concept of the type, the registry and the library's own fixtures, so it is a tool rather than a hand edit. The
rename is textual and limited to the places a type name and prefix appear:

- in YAML and JSON files under ``profile/`` (not its meta-schemas in ``profile/schemas/``) and ``tests/library/``: the type name as a whole word, the prefix where
  it starts a ``uid`` (``ITM-``) or follows ``uid_prefix:``, and the schema file name;
- in Markdown files under the bundle and ``tests/library/``: the ``type:`` line and the ``uid`` prefix in the
  frontmatter only, so prose is never changed.

It runs before a library has a history worth keeping: a ``uid`` is permanent once released (FR1.3), so a library
that has released concepts of the type must not rename its prefix. Run it before the library's first commit: once
the registry is committed, check 6 compares with that commit and reports every renamed ``uid`` as changed
(``OKF606``) and every old registry entry as removed (``OKF607``).
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
    text = re.sub(rf"(?<![\w-]){re.escape(old_slug)}\.schema\.json\b", f"{new_slug}.schema.json", text)
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


def _planned_writes(root: Path, bundle: Path, names: tuple[str, str, str, str, str, str]) -> list[tuple[Path, str]]:
    """The new text of every file the rename changes; nothing is written here."""
    old, new, old_prefix, new_prefix, old_slug, new_slug = names
    writes: list[tuple[Path, str]] = []
    for file in _files(root, [root / PROFILE_DIR, bundle, root / LIBRARY_TESTS]):
        if file.suffix not in DATA_SUFFIXES and file.suffix != ".md":
            continue
        try:
            text = file.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            msg = f"{file.relative_to(root).as_posix()} is not UTF-8 text; nothing was changed"
            raise ValueError(msg) from exc
        if file.suffix == ".md":
            updated = _replace_frontmatter(text, old, new, old_prefix, new_prefix)
        else:
            updated = _replace_data(text, old, new, old_prefix, new_prefix, old_slug, new_slug)
        if updated != text:
            writes.append((file, updated))
    return writes


def _planned_moves(root: Path, old_slug: str, new_slug: str) -> list[tuple[Path, Path]]:
    """The schema files to rename; refuses if a target already exists."""
    moves: list[tuple[Path, Path]] = []
    for file in _files(root, [root / PROFILE_DIR, root / LIBRARY_TESTS]):
        if file.name == f"{old_slug}.schema.json":
            target = file.with_name(f"{new_slug}.schema.json")
            if target.exists():
                msg = f"{target.relative_to(root).as_posix()} already exists; nothing was changed"
                raise ValueError(msg)
            moves.append((file, target))
    return moves


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
        ValueError: If the old type is not declared, the new name or prefix is malformed, either is already
            used by another type, a Markdown or data file is not UTF-8, or the new schema file already exists. Every
            change is worked out before anything is written, so a refusal leaves the repository unchanged.
    """
    old_prefix = _check_names(profile, old, new, new_prefix)
    root = profile.root
    old_slug, new_slug = old.lower(), new.lower()
    result = RenameResult()
    writes = _planned_writes(root, profile.bundle_root, (old, new, old_prefix, new_prefix, old_slug, new_slug))
    moves = _planned_moves(root, old_slug, new_slug)
    result.changed = [file.relative_to(root).as_posix() for file, _ in writes]
    result.moved = [(f.relative_to(root).as_posix(), t.relative_to(root).as_posix()) for f, t in moves]
    if not dry_run:
        for file, updated in writes:
            file.write_bytes(updated.encode("utf-8"))
        for file, target in moves:
            file.rename(target)
    return result
