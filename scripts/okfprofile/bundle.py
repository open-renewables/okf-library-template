"""Find and read the concept files of a bundle."""

from __future__ import annotations

import re
from pathlib import Path

from okfprofile.document import Concept, load_concept

RESERVED_NAMES = frozenset({"index.md", "log.md"})


def glob_match(pattern: str, path: str) -> bool:
    """Match a path against a glob pattern: ``*`` and ``?`` stay inside one folder, ``**`` crosses folders.

    Args:
        pattern: Glob pattern with ``/`` separators, relative to the bundle root.
        path: Path with ``/`` separators.

    Returns:
        True if the whole path matches.
    """
    regex = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            regex += "(?:.*/)?"
            index += 3
        elif pattern.startswith("**", index):
            regex += ".*"
            index += 2
        elif pattern[index] == "*":
            regex += "[^/]*"
            index += 1
        elif pattern[index] == "?":
            regex += "[^/]"
            index += 1
        else:
            regex += re.escape(pattern[index])
            index += 1
    return re.fullmatch(regex, path) is not None


def concept_files(bundle_root: Path) -> list[Path]:
    """Concept files under a bundle root, sorted by path.

    Reserved files (``index.md`` and ``log.md``, OKF section 3.1) are not concepts.

    Args:
        bundle_root: The bundle folder.

    Returns:
        Paths of every other ``.md`` file, or an empty list if the folder does not exist.
    """
    if not bundle_root.is_dir():
        return []
    return sorted(p for p in bundle_root.rglob("*.md") if p.is_file() and p.name not in RESERVED_NAMES)


def display_path(file: Path, root: Path) -> str:
    """Path as shown in findings: relative to the repository root, with forward slashes."""
    try:
        return file.relative_to(root).as_posix()
    except ValueError:
        return file.as_posix()


def load_bundle(bundle_root: Path, root: Path) -> list[Concept]:
    """Read every concept of a bundle.

    Args:
        bundle_root: The bundle folder.
        root: Repository root, used for the paths shown in findings.

    Returns:
        The parsed concepts in path order, each with ``concept_id`` set to its path under the bundle root
        without ``.md``.
    """
    concepts = []
    for file in concept_files(bundle_root):
        concept = load_concept(file, display_path(file, root))
        concept.concept_id = file.relative_to(bundle_root).with_suffix("").as_posix()
        concepts.append(concept)
    return concepts
