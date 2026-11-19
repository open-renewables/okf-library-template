"""Create and renumber concept files (SDD C-04 ``new_concept.py`` and ``renumber.py``).

These functions write files and the registry; the command-line scripts are thin wrappers over them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ruamel.yaml.error import YAMLError

from okfprofile.bundle import glob_match, load_bundle
from okfprofile.config import Profile
from okfprofile.document import parse_yaml
from okfprofile.registry import Registry, RegistryEntry, load_registry, renumber, save_registry, uid_of_concept

SEGMENT = re.compile(r"[a-z0-9][a-z0-9-]*")
PLAIN_SCALAR = re.compile(r"[A-Za-z][A-Za-z0-9 ._,()/-]*[A-Za-z0-9.)]")
RESERVED_WORDS = frozenset({"true", "false", "null", "yes", "no", "on", "off", "y", "n", "~"})
DEFAULT_DESCRIPTION = "To be completed."
CI_COMMENT = "<!-- Maintained by CI. Do not edit. -->"

WRITTEN_KEYS = frozenset({"type", "uid", "title", "description", "tags", "status"})


def _schema_keys(file: Path, seen: set[Path] | None = None) -> set[str]:
    """Property names a type schema declares, following a ``$ref`` to a schema file beside it."""
    seen = seen if seen is not None else set()
    if file in seen or not file.is_file():
        return set()
    seen.add(file)
    schema = json.loads(file.read_text(encoding="utf-8"))
    keys = set(schema.get("properties", {}))
    ref = schema.get("$ref")
    if isinstance(ref, str) and not ref.startswith("#"):
        keys |= _schema_keys(file.parent / ref.split("#", 1)[0], seen)
    return keys


def parse_settings(profile: Profile, type_name: str, settings: list[str]) -> dict[str, object]:
    """Read ``key=value`` frontmatter settings for a new concept (``new_concept.py --set``).

    A value is a YAML scalar or flow list, such as ``namespace=hazard`` or ``aliases=[PV, solar PV]``.

    Args:
        profile: The loaded profile.
        type_name: Declared type name.
        settings: The ``key=value`` strings, in order.

    Returns:
        The values by key.

    Raises:
        ValueError: If a setting has no ``=``, names a key the tool writes itself or the type's schema does not
            declare, repeats a key, or has a value that is not a scalar or a list of scalars.
    """
    declared = profile.type_named(type_name)
    if declared is None:
        msg = f"type '{type_name}' is not declared; declared: {', '.join(t.name for t in profile.types)}"
        raise ValueError(msg)
    allowed = _schema_keys(declared.schema_path) - WRITTEN_KEYS
    values: dict[str, object] = {}
    for setting in settings:
        key, sep, raw = setting.partition("=")
        key = key.strip()
        if not sep or not key:
            msg = f"'{setting}' must be key=value"
            raise ValueError(msg)
        if key in WRITTEN_KEYS:
            msg = f"'{key}' is written by new_concept.py itself (use --title or --description; status starts as draft)"
            raise ValueError(msg)
        if key not in allowed:
            msg = f"'{key}' is not declared by the {type_name} schema; declared: {', '.join(sorted(allowed))}"
            raise ValueError(msg)
        if key in values:
            msg = f"'{key}' is set twice"
            raise ValueError(msg)
        try:
            value, _ = parse_yaml(raw)
        except YAMLError as exc:
            msg = f"the value of '{key}' is not valid YAML: {exc}"
            raise ValueError(msg) from exc
        items = value if isinstance(value, list) else [value]
        if value is None or any(isinstance(v, (dict, list)) or v is None for v in items):
            msg = f"the value of '{key}' must be a scalar or a list of scalars"
            raise ValueError(msg)
        values[key] = value
    return values


def _yaml_value(value: object) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_value(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _scalar(str(value))


def _scalar(value: str) -> str:
    """A YAML scalar for ``value``: plain when it is safe, otherwise double-quoted."""
    if PLAIN_SCALAR.fullmatch(value) and value.lower() not in RESERVED_WORDS:
        return value
    return json.dumps(value, ensure_ascii=False)


def _title_from(concept_id: str) -> str:
    words = concept_id.rsplit("/", 1)[-1].replace("-", " ")
    return words[:1].upper() + words[1:]


def _tags(profile: Profile, type_name: str, folders: list[str]) -> list[str]:
    tags = []
    for rule in profile.path_rules:
        if rule.kind != "tag_equals_segment" or (rule.types and type_name not in rule.types):
            continue
        segment = rule.params["segment"]
        if segment >= len(folders):
            msg = f"the path needs a folder at index {segment} for the '{rule.namespace}:' tag"
            raise ValueError(msg)
        tags.append(f"{rule.namespace}:{folders[segment]}")
    return tags


def concept_text(
    profile: Profile,
    type_name: str,
    concept_id: str,
    uid: str,
    title: str,
    description: str,
    extra: dict[str, object] | None = None,
) -> str:
    """The text of a new concept: frontmatter, title heading and every declared section with its placeholder.

    Args:
        profile: The loaded profile.
        type_name: Declared type name.
        concept_id: Path under the bundle root without ``.md``.
        uid: The new concept's ``uid``.
        title: Display title.
        description: One-sentence description.
        extra: Further frontmatter keys from ``parse_settings``, written after ``status`` in the given order.

    Returns:
        The file text, with LF line endings.

    Raises:
        ValueError: If the path lacks a folder that a tag rule needs.
    """
    declared = profile.type_named(type_name)
    assert declared is not None  # noqa: S101 - the caller checked the type
    tags = _tags(profile, type_name, concept_id.split("/")[:-1])
    status = "draft" if "draft" in profile.statuses else profile.statuses[0]
    lines = ["---", f"type: {_scalar(type_name)}", f"uid: {uid}", f"title: {_scalar(title)}"]
    lines.append(f"description: {_scalar(description)}")
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append(f"status: {status}")
    lines.extend(f"{key}: {_yaml_value(value)}" for key, value in (extra or {}).items())
    lines.extend(["---", "", f"# {title}"])
    body = declared.body
    placeholder = body.empty_placeholder if body else ""
    for section in body.sections if body else ():
        lines.extend(["", f"## {section.heading}", ""])
        lines.append(CI_COMMENT if section.managed_by_ci else placeholder)
    return "\n".join(lines) + "\n"


def create_concept(
    profile: Profile,
    type_name: str,
    concept_id: str,
    title: str | None = None,
    description: str | None = None,
    extra: dict[str, object] | None = None,
) -> Path:
    """Create a concept file and register its ``uid``.

    Args:
        profile: The loaded profile.
        type_name: Declared type name.
        concept_id: Path under the bundle root without ``.md``, such as ``group/category/name``.
        title: Display title; derived from the last path segment if omitted.
        description: One-sentence description; a placeholder if omitted.
        extra: Further frontmatter keys, checked by ``parse_settings``.

    Returns:
        The path of the new file.

    Raises:
        ValueError: If the type is undeclared, the path is malformed or outside the type's paths, the file exists,
            or a tag rule needs a folder the path lacks.
    """
    declared = profile.type_named(type_name)
    if declared is None:
        msg = f"type '{type_name}' is not declared; declared: {', '.join(t.name for t in profile.types)}"
        raise ValueError(msg)
    if not all(SEGMENT.fullmatch(part) for part in concept_id.split("/")):
        msg = f"'{concept_id}' must be lower-case words joined by hyphens, folders separated by '/', without .md"
        raise ValueError(msg)
    file = profile.bundle_root / f"{concept_id}.md"
    if declared.paths and not any(glob_match(p, f"{concept_id}.md") for p in declared.paths):
        msg = f"type '{type_name}' belongs at {', '.join(declared.paths)}"
        raise ValueError(msg)
    if file.exists():
        msg = f"{file} already exists"
        raise ValueError(msg)
    registry = load_registry(profile.root)
    taken = {u for c in load_bundle(profile.bundle_root, profile.root) if (u := uid_of_concept(c))}
    uid = registry.next_uid(declared.uid_prefix, taken)
    text = concept_text(
        profile, type_name, concept_id, uid, title or _title_from(concept_id), description or DEFAULT_DESCRIPTION, extra
    )
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding="utf-8", newline="\n")
    registry.entries[uid] = RegistryEntry(concept_id, type_name)
    save_registry(profile.root, registry)
    return file


def renumber_concept(profile: Profile, concept_id: str) -> tuple[str, str]:
    """Give a concept whose ``uid`` clashes with another the next free number (SRS FR1.6).

    Rewrites the concept's ``uid`` line (other lines and line endings are untouched) and updates the registry.

    Args:
        profile: The loaded profile.
        concept_id: ID of the concept to renumber.

    Returns:
        The old and the new ``uid``.

    Raises:
        ValueError: If the concept is not found or shares its ``uid`` with no other concept.
    """
    concepts = load_bundle(profile.bundle_root, profile.root)
    registry: Registry = load_registry(profile.root)
    old, new, updated = renumber(registry, concepts, concept_id)
    concept = next(c for c in concepts if c.concept_id == concept_id)
    file = profile.bundle_root / f"{concept_id}.md"
    lines = file.read_bytes().decode("utf-8").splitlines(keepends=True)
    index = concept.line_of("uid") - 1
    if not lines[index].startswith("uid:"):
        msg = f"cannot find the uid line of {concept_id}"
        raise ValueError(msg)
    ending = lines[index][len(lines[index].rstrip("\r\n")) :]
    lines[index] = f"uid: {new}{ending}"
    file.write_bytes("".join(lines).encode("utf-8"))
    save_registry(profile.root, updated)
    return old, new
