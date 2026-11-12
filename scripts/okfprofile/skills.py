"""Static checks for agent skills and the optional provider adapter (SDD C-08, I-14; ADR-002).

A skill is a folder ``.agents/skills/<name>/`` holding ``SKILL.md`` in the Agent Skills format. Only the six
specification frontmatter fields are allowed, and nothing a skill or ``AGENTS.md`` says may name a concept type,
``uid`` prefix or tag namespace the profile declares, so the same text serves every library.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from okfprofile.config import Profile

SKILLS_DIR = Path(".agents") / "skills"
ALLOWED_FIELDS = frozenset({"name", "description", "license", "compatibility", "metadata", "allowed-tools"})
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500
LINK = re.compile(r"\]\((?!https?:|#|mailto:)([^)\s#]+)")
SCRIPT = re.compile(r"(?<![\w/.-])scripts/([a-z_]+)\.py")
MANAGED_MARKER = ".okf-adapter"
ADAPTERS = {"claude": Path(".claude") / "skills"}


@dataclass(frozen=True)
class SkillFinding:
    """A fault in a skill or entry-point file.

    Attributes:
        file: Path relative to the repository root, forward slashes.
        message: What is wrong.
    """

    file: str
    message: str

    def human(self) -> str:
        """One line for a person."""
        return f"{self.file}: {self.message}"


def _split(text: str) -> tuple[dict[str, Any] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            try:
                data = YAML(typ="safe").load("\n".join(lines[1:index]))
            except YAMLError:
                return None, text
            return (data if isinstance(data, dict) else None), "\n".join(lines[index + 1 :])
    return None, text


def forbidden_terms(profile: Profile) -> dict[str, re.Pattern[str]]:
    """Patterns for what a skill must not name: declared type names, uid prefixes and tag namespaces.

    Args:
        profile: The loaded profile.

    Returns:
        Map of a description of the term to its compiled pattern.
    """
    terms: dict[str, re.Pattern[str]] = {}
    for decl in profile.types:
        terms[f"concept type {decl.name}"] = re.compile(rf"(?<![\w-]){re.escape(decl.name)}(?![\w-])")
        terms[f"uid prefix {decl.uid_prefix}"] = re.compile(rf"(?<![\w-]){re.escape(decl.uid_prefix)}-")
    for ns in profile.namespaces:
        terms[f"tag namespace {ns.name}"] = re.compile(rf"(?<![\w-]){re.escape(ns.name)}:[a-z0-9]")
    return terms


def check_text(relative: str, text: str, terms: dict[str, re.Pattern[str]]) -> list[SkillFinding]:
    """Report every profile-specific term in a text.

    Args:
        relative: Path shown in findings.
        text: The text to check.
        terms: Terms from ``forbidden_terms``.

    Returns:
        One finding per term found.
    """
    return [
        SkillFinding(relative, f"names {what}; a skill must read it from the profile")
        for what, pattern in terms.items()
        if pattern.search(text)
    ]


def _frontmatter_findings(relative: str, folder: Path, data: dict[str, Any]) -> list[SkillFinding]:
    found = [
        SkillFinding(relative, f"frontmatter field '{key}' is not in the Agent Skills specification")
        for key in sorted(set(data) - ALLOWED_FIELDS)
    ]
    name = data.get("name")
    if not isinstance(name, str) or not name:
        found.append(SkillFinding(relative, "name is missing"))
    else:
        if name != folder.name:
            found.append(SkillFinding(relative, f"name '{name}' differs from its folder '{folder.name}'"))
        if not NAME.match(name) or len(name) > MAX_NAME:
            found.append(
                SkillFinding(relative, f"name '{name}' is not lower-case hyphenated within {MAX_NAME} characters")
            )
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        found.append(SkillFinding(relative, "description is missing"))
    elif len(description) > MAX_DESCRIPTION:
        found.append(SkillFinding(relative, f"description is over {MAX_DESCRIPTION} characters"))
    return found


def _body_findings(relative: str, root: Path, folder: Path, body: str) -> list[SkillFinding]:
    found: list[SkillFinding] = []
    if len(body.splitlines()) > MAX_BODY_LINES:
        found.append(SkillFinding(relative, f"body is over {MAX_BODY_LINES} lines; move detail to a references file"))
    for target in sorted(set(LINK.findall(body))):
        if not (folder / target).exists():
            found.append(SkillFinding(relative, f"links to {target}, which does not exist"))
    for script in sorted(set(SCRIPT.findall(body))):
        if not (root / "scripts" / f"{script}.py").is_file():
            found.append(SkillFinding(relative, f"names scripts/{script}.py, which does not exist"))
    return found


def check_skill(root: Path, folder: Path, terms: dict[str, re.Pattern[str]]) -> list[SkillFinding]:
    """Check one skill folder.

    Args:
        root: Repository root.
        folder: The skill folder.
        terms: Terms the skill must not contain (``forbidden_terms``).

    Returns:
        The findings, empty when the skill is sound.
    """
    file = folder / "SKILL.md"
    relative = file.relative_to(root).as_posix()
    if not file.is_file():
        return [SkillFinding(folder.relative_to(root).as_posix(), "has no SKILL.md")]
    data, body = _split(file.read_text(encoding="utf-8"))
    if data is None:
        return [SkillFinding(relative, "frontmatter is missing or unreadable")]
    found = _frontmatter_findings(relative, folder, data) + _body_findings(relative, root, folder, body)
    for path in sorted(folder.rglob("*.md")):
        found.extend(check_text(path.relative_to(root).as_posix(), path.read_text(encoding="utf-8"), terms))
    return found


def check_skills(profile: Profile, extra_files: tuple[str, ...] = ("AGENTS.md",)) -> tuple[list[SkillFinding], int]:
    """Check every skill and the entry-point files.

    Args:
        profile: The loaded profile.
        extra_files: Files, relative to the root, that must also name no profile-specific term.

    Returns:
        The findings and the number of skills checked.
    """
    root = profile.root
    terms = forbidden_terms(profile)
    base = root / SKILLS_DIR
    folders = sorted(p for p in base.glob("*") if p.is_dir()) if base.is_dir() else []
    found: list[SkillFinding] = []
    for folder in folders:
        found.extend(check_skill(root, folder, terms))
    for name in extra_files:
        path = root / name
        if path.is_file():
            found.extend(check_text(name, path.read_text(encoding="utf-8"), terms))
    return found, len(folders)


@dataclass(frozen=True)
class LinkResult:
    """What ``link_skills`` did to one skill.

    Attributes:
        skill: Skill name.
        action: ``created``, ``updated``, ``unchanged`` or ``refused``.
        target: Path of the adapter folder, relative to the root.
    """

    skill: str
    action: str
    target: str


def _same(source: Path, copy: Path) -> bool:
    files = sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file())
    made = sorted(p.relative_to(copy).as_posix() for p in copy.rglob("*") if p.is_file() and p.name != MANAGED_MARKER)
    return files == made and all((source / f).read_bytes() == (copy / f).read_bytes() for f in files)


def link_skills(root: Path, adapter: str = "claude", *, link: bool = False, dry_run: bool = False) -> list[LinkResult]:
    """Make the skills visible to one provider by copying (or linking) them into its folder.

    The copy carries a marker file, so a later run replaces only what this function made and refuses a folder
    that someone else created.

    Args:
        root: Repository root.
        adapter: Provider name, a key of ``ADAPTERS``.
        link: Create a directory link instead of a copy.
        dry_run: Report without changing anything.

    Returns:
        One result per skill.
    """
    destination = root / ADAPTERS[adapter]
    results: list[LinkResult] = []
    for source in sorted(p for p in (root / SKILLS_DIR).glob("*") if (p / "SKILL.md").is_file()):
        target = destination / source.name
        shown = target.relative_to(root).as_posix()
        exists = target.exists() or target.is_symlink()
        if exists:
            managed = target.is_symlink() or (target / MANAGED_MARKER).is_file()
            if not managed:
                results.append(LinkResult(source.name, "refused", shown))
                continue
            if target.is_symlink():
                unchanged = link and target.resolve() == source.resolve()
            else:
                unchanged = not link and _same(source, target)
            if unchanged:
                results.append(LinkResult(source.name, "unchanged", shown))
                continue
            action = "updated"
        else:
            action = "created"
        results.append(LinkResult(source.name, action, shown))
        if dry_run:
            continue
        destination.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        elif target.exists():
            shutil.rmtree(target)
        if link:
            os.symlink(source.resolve(), target, target_is_directory=True)
        else:
            shutil.copytree(source, target)
            (target / MANAGED_MARKER).write_text("Copied by `poe link-skills`; safe to delete.\n", encoding="utf-8")
    return results
