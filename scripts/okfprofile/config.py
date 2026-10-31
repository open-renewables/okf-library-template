"""Load and validate a library's profile (SDD C-02, C-03, I-02 to I-04).

``profile/profile.yaml`` is checked against ``profile/schemas/profile.schema.json``, then its
cross-references are resolved: type schemas, section formats, vocabulary namespaces and rule
targets. The loader holds no domain value; everything a library customises comes from its files.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError, best_match
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from ruamel.yaml.error import YAMLError

from okfprofile.document import KeyPath, parse_concept, parse_yaml

PROFILE_DIR = "profile"
PROFILE_FILE = "profile.yaml"


class ProfileError(Exception):
    """The profile or one of its files is invalid.

    Attributes:
        problems: One message per problem, each starting with the file and line where known.
    """

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class SectionDecl:
    """A declared body section (I-02 ``types[].body.sections[]``)."""

    heading: str
    required: bool
    format: str | None
    managed_by_ci: bool


@dataclass(frozen=True)
class BodyDecl:
    """A declared body structure for a type."""

    title_heading: str
    order: str
    empty_placeholder: str
    sections: tuple[SectionDecl, ...]


@dataclass(frozen=True)
class TypeDecl:
    """A declared concept type.

    Attributes:
        name: Value of the ``type`` frontmatter key.
        uid_prefix: Prefix of the type's ``uid`` values.
        schema_path: Frontmatter schema file.
        schema_id: The schema's ``$id``, used to reference it.
        paths: Glob patterns, relative to the bundle root, where the type may live (empty: anywhere).
        body: Declared body structure, or None when the type has none.
    """

    name: str
    uid_prefix: str
    schema_path: Path
    schema_id: str
    paths: tuple[str, ...]
    body: BodyDecl | None


@dataclass(frozen=True)
class NamespaceDecl:
    """A declared vocabulary namespace."""

    name: str
    kinds: bool
    values_unique_across_kinds: bool


@dataclass(frozen=True)
class PathRule:
    """A declarative path rule (closed set of kinds, I-02).

    Attributes:
        kind: Rule kind.
        namespace: Tag namespace the rule concerns.
        types: Type names the rule applies to; empty means every type.
        params: The kind's remaining parameters.
    """

    kind: str
    namespace: str
    types: tuple[str, ...]
    params: dict[str, Any]


@dataclass(frozen=True)
class StatusExtension:
    """A profile-declared ``status`` value beyond OKF's three."""

    value: str
    trust_tier: str
    publishing: str


@dataclass(frozen=True)
class Rules:
    """Provenance and publishing settings (I-02 ``rules``)."""

    provenance: str
    revision_write: str
    revision_token: str
    write_okf_verified: bool
    agent_label: str
    full_review_label: str
    migration_label: str
    stable_requires_human_approval: bool
    stable_approvals: int
    allow_recorded_self_approval: bool
    require_non_author_approver: bool
    stable_requires_citation: bool
    reject_unknown_fields: bool
    stale_after_default: str


@dataclass(frozen=True)
class WarningDecl:
    """A profile-declared warning (closed set of kinds, I-02)."""

    id: str
    kind: str
    priority: str
    enabled: bool
    params: dict[str, Any]


@dataclass(frozen=True)
class ChildDecl:
    """A required or optional child of a format's list items."""

    label: str
    required: bool
    enum: tuple[str, ...] | None


@dataclass(frozen=True)
class FormatDecl:
    """A section format (I-04).

    Attributes:
        name: Format name, as referenced by a section.
        pattern: Compiled regular expression for the first line of each item.
        enums: Allowed values per named group of the pattern.
        vocab: Vocabulary namespace per named group of the pattern.
        children: Child labels expected under each item, in order.
    """

    name: str
    pattern: re.Pattern[str]
    enums: dict[str, tuple[str, ...]]
    vocab: dict[str, str]
    children: tuple[ChildDecl, ...]


@dataclass(frozen=True)
class IndexDecl:
    """Index settings (I-02 ``index``)."""

    show_status: bool
    show_tier: bool
    max_concepts_per_directory: int


@dataclass(frozen=True)
class Profile:
    """A loaded profile with its cross-references resolved.

    Attributes:
        root: Repository root the profile was loaded from.
        name: Profile name.
        profile_version: Profile semver.
        okf_version: OKF version the bundle conforms to.
        okf_spec_commit: Pinned OKF specification commit.
        template_version: Template release the library was instantiated from.
        library_name: Library short name.
        platform: ``github`` or ``git-local``.
        maintainers: Map of login to emails.
        bundle_root: Absolute path of the bundle folder.
        types: Declared types in order.
        vocab_path: Folder of vocabulary concepts, relative to the bundle root.
        namespaces: Declared vocabulary namespaces.
        tag_pattern: Compiled pattern every tag must match.
        path_rules: Declared path rules.
        statuses: OKF statuses accepted.
        status_extensions: Profile-declared statuses.
        rules: Provenance and publishing settings.
        warnings: Declared warnings.
        formats: Section formats by name.
        index: Index settings.
        registry: JSON Schema resources of ``profile/types/``.
    """

    root: Path
    name: str
    profile_version: str
    okf_version: str
    okf_spec_commit: str
    template_version: str
    library_name: str
    platform: str
    maintainers: dict[str, tuple[str, ...]]
    bundle_root: Path
    types: tuple[TypeDecl, ...]
    vocab_path: str
    namespaces: tuple[NamespaceDecl, ...]
    tag_pattern: re.Pattern[str]
    path_rules: tuple[PathRule, ...]
    statuses: tuple[str, ...]
    status_extensions: tuple[StatusExtension, ...]
    rules: Rules
    warnings: tuple[WarningDecl, ...]
    formats: dict[str, FormatDecl]
    index: IndexDecl
    registry: Registry[Any] = field(repr=False)

    def type_named(self, name: str) -> TypeDecl | None:
        """The declared type called ``name``, if any."""
        return next((t for t in self.types if t.name == name), None)

    def type_validator(self, name: str) -> Draft202012Validator:
        """A frontmatter validator for a declared type.

        When ``rules.reject_unknown_fields`` is true, ``unevaluatedProperties: false`` is added to the type
        schema, which (unlike ``additionalProperties``) sees properties declared through ``$ref``, so OKF's
        optional keys stay accepted (SDD I-03).

        Args:
            name: Declared type name.

        Returns:
            A validator for the type's frontmatter.

        Raises:
            KeyError: If the type is not declared.
        """
        declared = self.type_named(name)
        if declared is None:
            raise KeyError(name)
        schema: dict[str, Any] = {"$ref": declared.schema_id}
        if self.rules.reject_unknown_fields:
            schema["unevaluatedProperties"] = False
        return Draft202012Validator(schema, registry=self.registry)


def _line_for(lines: dict[KeyPath, int], path: KeyPath) -> int:
    key = path
    while key:
        if key in lines:
            return lines[key] + 1
        key = key[:-1]
    return 1


def _schema_problems(
    schema: dict[str, Any], data: Any, lines: dict[KeyPath, int], label: str, registry: Registry[Any] | None = None
) -> list[str]:
    validator = Draft202012Validator(schema, registry=registry) if registry else Draft202012Validator(schema)
    problems = []
    for error in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
        best: ValidationError = best_match([error]) or error
        path = list(best.absolute_path)
        where = "/".join(str(p) for p in path) or "(root)"
        problems.append(f"{label}:{_line_for(lines, tuple(path))}: {where}: {best.message}")
    return problems


def _read_json(path: Path, problems: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        problems.append(f"{path}: cannot read: {exc.strerror}")
    except json.JSONDecodeError as exc:
        problems.append(f"{path}:{exc.lineno}: invalid JSON: {exc.msg}")
    else:
        if isinstance(value, dict):
            return value
        problems.append(f"{path}: expected a JSON object")
    return None


def _read_yaml(path: Path, problems: list[str]) -> tuple[Any, dict[KeyPath, int]] | None:
    try:
        return parse_yaml(path.read_text(encoding="utf-8"))
    except OSError as exc:
        problems.append(f"{path}: cannot read: {exc.strerror}")
    except YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        problems.append(f"{path}:{mark.line + 1 if mark else 1}: invalid YAML: {exc}")
    return None


def load_schema_registry(root: Path) -> tuple[Registry[Any], dict[str, str], list[str]]:
    """Load every ``profile/types/*.schema.json`` as a JSON Schema resource.

    Args:
        root: Repository root.

    Returns:
        The registry, a map of schema file name to ``$id``, and any problems found.
    """
    problems: list[str] = []
    registry: Registry[Any] = Registry()
    ids: dict[str, str] = {}
    for file in sorted((root / PROFILE_DIR / "types").glob("*.schema.json")):
        contents = _read_json(file, problems)
        if contents is None:
            continue
        try:
            Draft202012Validator.check_schema(contents)
        except SchemaError as exc:
            problems.append(f"{file}: invalid JSON Schema: {exc.message}")
            continue
        schema_id = contents.get("$id")
        if not isinstance(schema_id, str):
            problems.append(f"{file}: missing $id")
            continue
        ids[file.name] = schema_id
        registry = registry.with_resource(
            schema_id, Resource.from_contents(contents, default_specification=DRAFT202012)
        )
    return registry, ids, problems


def _load_formats(root: Path, namespaces: set[str], problems: list[str]) -> dict[str, FormatDecl]:
    meta = _read_json(root / PROFILE_DIR / "schemas" / "format.schema.json", problems)
    formats: dict[str, FormatDecl] = {}
    if meta is None:
        return formats
    for file in sorted((root / PROFILE_DIR / "formats").glob("*.md")):
        concept = parse_concept(file.read_text(encoding="utf-8"), str(file))
        problems.extend(f"{f.file}:{f.line}: {f.message}" for f in concept.findings)
        if concept.frontmatter is None:
            continue
        found = _schema_problems(meta, concept.frontmatter, concept.key_lines, str(file))
        problems.extend(found)
        if found:
            continue
        fm = concept.frontmatter
        if fm["format"] != file.stem:
            problems.append(f"{file}:{concept.line_of('format')}: format name must equal the file name '{file.stem}'")
            continue
        try:
            pattern = re.compile(fm["item"]["pattern"])
        except re.error as exc:
            problems.append(f"{file}:{concept.line_of('item', 'pattern')}: invalid item pattern: {exc}")
            continue
        enums = {k: tuple(v) for k, v in fm["item"].get("enums", {}).items()}
        vocab = dict(fm["item"].get("vocab", {}))
        for group in [*enums, *vocab]:
            if group not in pattern.groupindex:
                problems.append(f"{file}: '{group}' is not a named group of the item pattern")
        problems.extend(
            f"{file}: vocab group '{g}' names undeclared namespace '{ns}'"
            for g, ns in vocab.items()
            if ns not in namespaces
        )
        children = tuple(
            ChildDecl(c["label"], c["required"], tuple(c["enum"]) if "enum" in c else None)
            for c in fm.get("children", [])
        )
        if len({c.label for c in children}) != len(children):
            problems.append(f"{file}: duplicate child label")
        formats[fm["format"]] = FormatDecl(fm["format"], pattern, enums, vocab, children)
    return formats


def _body(raw: dict[str, Any]) -> BodyDecl:
    sections = tuple(
        SectionDecl(s["heading"], s["required"], s.get("format"), s.get("managed_by") == "ci") for s in raw["sections"]
    )
    return BodyDecl(raw["title_heading"], raw["order"], raw["empty_placeholder"], sections)


def _repeated(values: list[str]) -> list[str]:
    """Values that occur more than once, sorted."""
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _resolve_types(
    data: dict[str, Any],
    lines: dict[KeyPath, int],
    root: Path,
    schema_ids: dict[str, str],
    formats: dict[str, FormatDecl],
    problems: list[str],
) -> list[TypeDecl]:
    path = root / PROFILE_DIR / PROFILE_FILE
    types: list[TypeDecl] = []
    for index, raw in enumerate(data["types"]):
        schema_path = root / PROFILE_DIR / raw["schema"]
        schema_id = schema_ids.get(schema_path.name)
        where = f"{path}:{_line_for(lines, ('types', index, 'schema'))}"
        if schema_id is None or schema_path.parent != root / PROFILE_DIR / "types":
            problems.append(f"{where}: schema '{raw['schema']}' is not a file in profile/types/")
            continue
        body = _body(raw["body"]) if "body" in raw else None
        sections = body.sections if body else ()
        problems.extend(
            f"{where}: type '{raw['name']}' uses undeclared format '{s.format}'"
            for s in sections
            if s.format and s.format not in formats
        )
        if len({s.heading for s in sections}) != len(sections):
            problems.append(f"{where}: type '{raw['name']}' declares a heading twice")
        patterns = tuple(raw.get("paths", []))
        problems.extend(
            f"{where}: type path '{p}' must be relative to the bundle root" for p in patterns if _escapes(p)
        )
        types.append(TypeDecl(raw["name"], raw["uid_prefix"], schema_path, schema_id, patterns, body))
    return types


def _escapes(relative: str) -> bool:
    """True if a path meant to be relative is absolute (on either convention) or climbs out with ``..``."""
    posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
    return posix.is_absolute() or windows.is_absolute() or ".." in posix.parts or ".." in windows.parts


def _check_references(
    data: dict[str, Any], lines: dict[KeyPath, int], path: Path, namespace_names: set[str], problems: list[str]
) -> None:
    type_names = [t["name"] for t in data["types"]]
    problems.extend(f"{path}: type '{n}' is declared twice" for n in _repeated(type_names))
    problems.extend(
        f"{path}: uid prefix '{p}' is used twice" for p in _repeated([t["uid_prefix"] for t in data["types"]])
    )
    if _escapes(data["bundle_root"]):
        problems.append(f"{path}: bundle_root must be a relative path inside the repository")
    for i, rule in enumerate(data["path_rules"]):
        where = f"{path}:{_line_for(lines, ('path_rules', i))}"
        if rule["namespace"] not in namespace_names:
            problems.append(f"{where}: path rule names undeclared namespace '{rule['namespace']}'")
        if "vocabulary" in rule and rule["vocabulary"] not in namespace_names:
            problems.append(f"{where}: path rule names undeclared vocabulary '{rule['vocabulary']}'")
        problems.extend(
            f"{where}: path rule names undeclared type '{t}'" for t in rule.get("types", []) if t not in type_names
        )
    for i, warning in enumerate(data["warnings"]):
        if "namespace" in warning and warning["namespace"] not in namespace_names:
            where = f"{path}:{_line_for(lines, ('warnings', i))}"
            problems.append(f"{where}: warning names undeclared namespace '{warning['namespace']}'")
    problems.extend(f"{path}: warning id '{w}' is used twice" for w in _repeated([w["id"] for w in data["warnings"]]))
    problems.extend(
        f"{path}: status extension '{e['value']}' repeats a status value"
        for e in data["status"]["extensions"]
        if e["value"] in data["status"]["values"]
    )


def _compile_tag_pattern(
    data: dict[str, Any], lines: dict[KeyPath, int], path: Path, problems: list[str]
) -> re.Pattern[str]:
    try:
        return re.compile(data["tags"]["pattern"])
    except re.error as exc:
        problems.append(f"{path}:{_line_for(lines, ('tags', 'pattern'))}: invalid tag pattern: {exc}")
        return re.compile("")


def _path_rules(data: dict[str, Any]) -> tuple[PathRule, ...]:
    shared = {"kind", "namespace", "types"}
    return tuple(
        PathRule(r["kind"], r["namespace"], tuple(r.get("types", [])), {k: v for k, v in r.items() if k not in shared})
        for r in data["path_rules"]
    )


def _warnings(data: dict[str, Any]) -> tuple[WarningDecl, ...]:
    shared = {"id", "kind", "level", "enabled"}
    return tuple(
        WarningDecl(w["id"], w["kind"], w["level"], w["enabled"], {k: v for k, v in w.items() if k not in shared})
        for w in data["warnings"]
    )


def load_profile(root: Path) -> Profile:
    """Load ``profile/profile.yaml`` from a repository and resolve its references.

    Args:
        root: Repository root (the folder that contains ``profile/``).

    Returns:
        The loaded profile.

    Raises:
        ProfileError: If any file is missing or invalid, or a reference does not resolve. All problems
            found are reported together.
    """
    problems: list[str] = []
    path = root / PROFILE_DIR / PROFILE_FILE
    meta = _read_json(root / PROFILE_DIR / "schemas" / "profile.schema.json", problems)
    parsed = _read_yaml(path, problems)
    if meta is None or parsed is None:
        raise ProfileError(problems)
    data, lines = parsed
    problems.extend(_schema_problems(meta, data, lines, str(path)))
    registry, schema_ids, schema_problems = load_schema_registry(root)
    problems.extend(schema_problems)
    if problems:
        raise ProfileError(problems)

    namespaces = tuple(
        NamespaceDecl(n["name"], n["kinds"], n["values_unique_across_kinds"])
        for n in data["vocabularies"]["namespaces"]
    )
    namespace_names = {n.name for n in namespaces}
    formats = _load_formats(root, namespace_names, problems)
    types = _resolve_types(data, lines, root, schema_ids, formats, problems)
    _check_references(data, lines, path, namespace_names, problems)
    tag_pattern = _compile_tag_pattern(data, lines, path, problems)
    if problems:
        raise ProfileError(problems)

    return Profile(
        root=root,
        name=data["profile"],
        profile_version=data["profile_version"],
        okf_version=data["okf_version"],
        okf_spec_commit=data["okf_spec_commit"],
        template_version=data["template_version"],
        library_name=data["library"]["name"],
        platform=data["platform"],
        maintainers={login: tuple(m["emails"]) for login, m in data.get("maintainers", {}).items()},
        bundle_root=root / data["bundle_root"],
        types=tuple(types),
        vocab_path=data["vocabularies"]["path"],
        namespaces=namespaces,
        tag_pattern=tag_pattern,
        path_rules=_path_rules(data),
        statuses=tuple(data["status"]["values"]),
        status_extensions=tuple(
            StatusExtension(e["value"], e["trust_tier"], e["publishing"]) for e in data["status"]["extensions"]
        ),
        rules=Rules(**data["rules"]),
        warnings=_warnings(data),
        formats=formats,
        index=IndexDecl(**data["index"]),
        registry=registry,
    )
