"""The identifier registry (SDD I-06, SRS FR1.3 to FR1.7).

``profile/uid-registry.yaml`` maps each ``uid`` to the concept's type, current path and earlier paths. It is
written by tooling, never by hand. Numbers are never reused: the next number for a prefix is one more than the
highest ever registered.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field, replace
from pathlib import Path

from jsonschema import Draft202012Validator
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from okfprofile.document import Concept, parse_yaml

REGISTRY_FILE = "uid-registry.yaml"
MAX_NUMBER = 9999
DIGITS = 4


class RegistryError(Exception):
    """The registry file is unreadable or invalid.

    Attributes:
        problems: One message per problem.
    """

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class RegistryEntry:
    """One registered concept.

    Attributes:
        path: Concept ID (path under the bundle root, without ``.md``).
        type: Concept type name.
        moved_from: Earlier paths of the concept.
    """

    path: str
    type: str
    moved_from: tuple[str, ...] = ()


@dataclass
class Registry:
    """The identifier registry.

    Attributes:
        entries: Entries by ``uid``.
    """

    entries: dict[str, RegistryEntry] = field(default_factory=dict)

    def get(self, uid: str) -> RegistryEntry | None:
        """The entry for ``uid``, if registered."""
        return self.entries.get(uid)

    def highest(self, prefix: str) -> int:
        """Highest number registered for a prefix, or 0."""
        numbers = [number_of(uid) for uid in self.entries if uid.startswith(f"{prefix}-")]
        return max([n for n in numbers if n is not None], default=0)

    def next_uid(self, prefix: str, also_taken: set[str] | None = None) -> str:
        """The next unused ``uid`` for a prefix.

        Args:
            prefix: Type prefix.
            also_taken: Further ``uid`` values to treat as used, such as those found in concept files.

        Returns:
            The ``uid``, one above the highest number registered or taken.

        Raises:
            ValueError: If the prefix already uses its last number (widening the sequence is a breaking
                profile change).
        """
        taken = [self.highest(prefix)]
        taken += [n for u in also_taken or set() if u.startswith(f"{prefix}-") and (n := number_of(u)) is not None]
        number = max(taken) + 1
        if number > MAX_NUMBER:
            msg = f"prefix {prefix} has no numbers left; widening the sequence is a breaking profile change"
            raise ValueError(msg)
        return f"{prefix}-{number:0{DIGITS}d}"

    def to_text(self) -> str:
        """Canonical YAML: entries sorted by ``uid``, block style."""
        plain: dict[str, dict[str, object]] = {}
        for uid in sorted(self.entries):
            entry = self.entries[uid]
            data: dict[str, object] = {"path": entry.path, "type": entry.type}
            if entry.moved_from:
                data["moved_from"] = list(entry.moved_from)
            plain[uid] = data
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        stream = io.StringIO()
        yaml.dump(plain, stream)
        return stream.getvalue()


def number_of(uid: str) -> int | None:
    """The numeric part of a ``uid`` such as ``ITM-0042``, or None if it has none."""
    _, _, tail = uid.rpartition("-")
    return int(tail) if tail.isdigit() else None


def parse_registry(text: str, schema: dict[str, object], label: str) -> Registry:
    """Parse registry text and check it against the registry meta-schema.

    Args:
        text: YAML source.
        schema: The registry meta-schema.
        label: File name used in messages.

    Returns:
        The registry.

    Raises:
        RegistryError: If the text is not valid YAML or does not satisfy the schema.
    """
    try:
        data, _ = parse_yaml(text)
    except YAMLError as exc:
        raise RegistryError([f"{label}: invalid YAML: {exc}"]) from exc
    if data is None:
        data = {}
    problems = [
        f"{label}: {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
        for e in Draft202012Validator(schema).iter_errors(data)
    ]
    if problems:
        raise RegistryError(sorted(problems))
    return Registry(
        {uid: RegistryEntry(e["path"], e["type"], tuple(e.get("moved_from", []))) for uid, e in data.items()}
    )


def registry_path(root: Path) -> Path:
    """Where the registry lives in a repository."""
    return root / "profile" / REGISTRY_FILE


def load_registry(root: Path) -> Registry:
    """Load ``profile/uid-registry.yaml``; a missing file is an empty registry.

    Args:
        root: Repository root.

    Returns:
        The registry.

    Raises:
        RegistryError: If the file or the meta-schema cannot be read, or the file is invalid.
    """
    schema_file = root / "profile" / "schemas" / "uid-registry.schema.json"
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError([f"{schema_file}: cannot read the registry meta-schema: {exc}"]) from exc
    file = registry_path(root)
    if not file.is_file():
        return Registry()
    return parse_registry(file.read_text(encoding="utf-8"), schema, str(file))


def save_registry(root: Path, registry: Registry) -> None:
    """Write the registry in canonical form."""
    registry_path(root).write_text(registry.to_text(), encoding="utf-8", newline="\n")


def apply_moves(registry: Registry, uid_of: dict[str, str]) -> Registry:
    """Bring the registry in step with moved concept files (``--fix-registry``).

    For each concept whose path differs from its entry, the entry takes the concept's path and keeps the old one
    in ``moved_from``. Entries for concepts that no longer exist are left alone.

    Args:
        registry: The current registry.
        uid_of: The ``uid`` of each concept, keyed by concept ID.

    Returns:
        A new registry; the argument is not changed.
    """
    entries = dict(registry.entries)
    for concept_id, uid in uid_of.items():
        entry = entries.get(uid)
        if entry is not None and entry.path != concept_id:
            earlier = (*entry.moved_from, entry.path) if entry.path not in entry.moved_from else entry.moved_from
            entries[uid] = replace(entry, path=concept_id, moved_from=earlier)
    return Registry(entries)


def uid_of_concept(concept: Concept) -> str | None:
    """The ``uid`` frontmatter value of a concept, if it is a string."""
    value = (concept.frontmatter or {}).get("uid")
    return value if isinstance(value, str) else None


def renumber(registry: Registry, concepts: list[Concept], concept_id: str) -> tuple[str, str, Registry]:
    """Give a concept whose ``uid`` clashes with another the next free number (SRS FR1.6).

    The registry keeps the old ``uid`` for the other concept; the renumbered concept is registered under
    the new one. The caller rewrites the concept file's ``uid`` line.

    Args:
        registry: The current registry.
        concepts: Every concept of the bundle.
        concept_id: ID of the concept to renumber.

    Returns:
        The old ``uid``, the new ``uid`` and the updated registry.

    Raises:
        ValueError: If the concept is not found, has no ``uid``, or shares its ``uid`` with no other concept.
    """
    target = next((c for c in concepts if c.concept_id == concept_id), None)
    old = uid_of_concept(target) if target else None
    if target is None or old is None:
        msg = f"concept '{concept_id}' not found or has no uid"
        raise ValueError(msg)
    others = [c for c in concepts if c.concept_id != concept_id and uid_of_concept(c) == old]
    if not others:
        msg = f"uid {old} is not shared with another concept"
        raise ValueError(msg)
    prefix = old.rpartition("-")[0]
    taken = {u for c in concepts if (u := uid_of_concept(c))}
    new = registry.next_uid(prefix, taken)
    entries = dict(registry.entries)
    type_name = str((target.frontmatter or {}).get("type"))
    current = entries.get(old)
    if current is not None and current.path == concept_id:
        keeper = others[0]
        entries[old] = RegistryEntry(keeper.concept_id, str((keeper.frontmatter or {}).get("type")), current.moved_from)
    entries[new] = RegistryEntry(concept_id, type_name)
    return old, new, Registry(entries)
