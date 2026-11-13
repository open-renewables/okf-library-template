"""Turn a copy of the template into a library (SDD W-01 step 3, C-04 ``init_library.py``).

The tool rewrites what is specific to a library (names, platform, maintainers, licences, decision record), removes
what belongs to the template only, and leaves the profile, the example bundle and the tooling in place. Every step
derives its result from the answers and the current files, so running it again with the same answers changes
nothing.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from okfprofile.bundle import load_bundle
from okfprofile.config import load_profile
from okfprofile.document import parse_yaml
from okfprofile.indexes import expected_indexes
from okfprofile.registry import Registry, load_registry, save_registry
from okfprofile.revision_writer import reset_history

PLATFORMS = ("github", "git-local")
CODE_LICENCES = ("Apache-2.0", "MIT", "proprietary")
CONTENT_LICENCES = ("CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0", "proprietary")
TEMPLATE_LOGIN = "richard-gledhill"
TEMPLATE_REPOSITORY = "https://github.com/open-renewables/okf-library-template"
TEMPLATE_NAME = "okf-library-template"
TEMPLATE_MARKERS = (TEMPLATE_LOGIN, "open-renewables", TEMPLATE_NAME)
MARKER_ALLOWED = ("NOTICE", "LICENSE-template", "DECISIONS.md", "scripts/", "tests/")
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EXAMPLE_FOLDER = "example-group"
CONTENT_URLS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/legalcode",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/legalcode",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
}
LICENCE_FOLDER = "licences"
TEMPLATE_ONLY = ("CLAUDE.md", "docs", LICENCE_FOLDER)
TEMPLATE_TESTS = ("tests/template", ".github/workflows/template-tests.yml")
PLATFORM_ONLY = (
    ".github/ISSUE_TEMPLATE",
    ".github/pull_request_template.md",
    ".github/workflows",
    ".github/dependabot.yml",
    ".github/labels.yml",
)
MIT_TEXT = """MIT License

Copyright (c) {year} {holder}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


class InitError(Exception):
    """The answers are invalid, or the folder is not a template copy."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Answers:
    """What the library owner tells ``init_library``.

    Attributes:
        platform: ``github`` or ``git-local``.
        name: Library name: lower case letters, digits and hyphens. It becomes the project and archive name.
        title: Display title.
        description: One sentence about the library.
        login: The maintainer's platform login (the first code owner).
        email: The maintainer's email address, which resolves commit authors in ``git-local`` mode.
        maintainer_name: The maintainer's name, for the citation file.
        licence_holder: Who holds the copyright.
        content_licence: Licence of the bundle.
        code_licence: Licence of the owner's own code and changes.
        repository: Repository URL (``github``); empty if there is none.
        keep_examples: Keep the example concept.
        keep_tests: Keep ``tests/template`` and the template's own workflow.
        year: Copyright year.
    """

    platform: str
    name: str
    title: str
    description: str
    login: str
    email: str
    maintainer_name: str = ""
    licence_holder: str = ""
    content_licence: str = "CC-BY-4.0"
    code_licence: str = "Apache-2.0"
    repository: str = ""
    keep_examples: bool = True
    keep_tests: bool = False
    year: int = field(default_factory=lambda: date.today().year)

    @property
    def holder(self) -> str:
        """The copyright holder: the stated holder, else the maintainer's name, else their login."""
        return self.licence_holder or self.maintainer_name or self.login


def parse_answers(data: Any) -> Answers:
    """Validate an answers mapping.

    Args:
        data: The parsed answers file.

    Returns:
        The answers, with defaults filled in.

    Raises:
        InitError: Listing every problem found.
    """
    if not isinstance(data, dict):
        raise InitError(["the answers must be a mapping"])
    raw_maintainer = data.get("maintainer")
    maintainer: dict[str, Any] = raw_maintainer if isinstance(raw_maintainer, dict) else {}
    known = set(Answers.__dataclass_fields__) - {"login", "email", "maintainer_name"} | {"maintainer"}
    problems = [f"unknown answer '{key}'" for key in sorted(set(data) - known)]
    text = {k: str(data.get(k, "")).strip() for k in ("platform", "name", "title", "description", "repository")}
    login = str(maintainer.get("login", "")).strip()
    email = str(maintainer.get("email", "")).strip()
    content = str(data.get("content_licence", "CC-BY-4.0"))
    code = str(data.get("code_licence", "Apache-2.0"))
    checks = [
        (text["platform"] in PLATFORMS, f"platform must be one of {', '.join(PLATFORMS)}"),
        (
            bool(NAME_PATTERN.match(text["name"])),
            "name must be lower case letters, digits and hyphens, starting with a letter",
        ),
        (
            bool(login and LOGIN_PATTERN.match(login)),
            "maintainer.login is required (letters, digits, '.', '_' and '-')",
        ),
        (bool(EMAIL_PATTERN.match(email)), "maintainer.email is required and must be an email address"),
        (content in CONTENT_LICENCES, f"content_licence must be one of {', '.join(CONTENT_LICENCES)}"),
        (code in CODE_LICENCES, f"code_licence must be one of {', '.join(CODE_LICENCES)}"),
        (isinstance(data.get("keep_examples", True), bool), "keep_examples must be true or false"),
        (isinstance(data.get("keep_tests", False), bool), "keep_tests must be true or false"),
        (isinstance(data.get("year", 2000), int), "year must be a number"),
    ]
    problems += [message for ok, message in checks if not ok]
    if problems:
        raise InitError(problems)
    return Answers(
        platform=text["platform"],
        name=text["name"],
        title=text["title"] or text["name"].replace("-", " ").title(),
        description=text["description"] or "An OKF knowledge library.",
        login=login,
        email=email,
        maintainer_name=str(maintainer.get("name", "")).strip(),
        licence_holder=str(data.get("licence_holder", "")).strip(),
        content_licence=content,
        code_licence=code,
        repository=text["repository"].rstrip("/"),
        keep_examples=bool(data.get("keep_examples", True)),
        keep_tests=bool(data.get("keep_tests", False)),
        year=int(data.get("year", date.today().year)),
    )


def load_answers(path: Path) -> Answers:
    """Read an answers file (YAML).

    Raises:
        InitError: If the file cannot be read or the answers are invalid.
    """
    try:
        data, _lines = parse_yaml(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InitError([f"cannot read {path}: {exc.strerror}"]) from exc
    except Exception as exc:
        raise InitError([f"{path}: invalid YAML: {exc}"]) from exc
    return parse_answers(data)


def quote(value: str) -> str:
    """A YAML double-quoted scalar (JSON strings are valid YAML)."""
    return json.dumps(value, ensure_ascii=False)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def _sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    new, count = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        msg = f"cannot find {label}; is this a copy of the template?"
        raise InitError([msg])
    return new


def rewrite_profile(text: str, a: Answers) -> str:
    """Set the library's name, platform, maintainers and revision token in ``profile.yaml``, keeping its comments."""
    site = _sub_once(text, r"^profile: .*$", f"profile: {a.name}", "the profile name")
    site = _sub_once(site, r"^  name: .*$", f"  name: {a.name}", "library.name")
    site = _sub_once(site, r"^  title: .*$", f"  title: {quote(a.title)}", "library.title")
    site = _sub_once(site, r"^  repository: .*$", f"  repository: {quote(a.repository)}", "library.repository")
    site = _sub_once(site, r"^platform: .*$", f"platform: {a.platform}", "platform")
    maintainers = f"maintainers:\n  {a.login}:\n    emails: [{quote(a.email)}]\n    role: maintainer"
    site = _sub_once(site, r"^maintainers:.*(?:\n[ \t]+\S.*)*", maintainers, "maintainers")
    return _sub_once(site, r"^  revision_token: \S+", "  revision_token: github-token", "rules.revision_token")


def rewrite_pyproject(text: str, a: Answers, drop_coverage_gate: bool) -> str:
    """Name the project after the library, set its licence, and drop the coverage gate if the template tests go."""
    out = _sub_once(text, r'^name = "[^"]*"$', f'name = "{a.name}"', "the project name")
    out = _sub_once(out, r'^description = "[^"]*"$', f"description = {quote(a.description)}", "the project description")
    spdx = a.code_licence if a.code_licence != "proprietary" else "LicenseRef-Proprietary"
    out = _sub_once(out, r'^license = "[^"]*"$', f'license = "{spdx}"', "the project licence")
    if drop_coverage_gate:
        out = re.sub(r'^addopts = ".*"$', 'addopts = ""', out, flags=re.MULTILINE)
        out = re.sub(r"^fail_under = .*\n", "", out, flags=re.MULTILINE)
    return out


def rewrite_mkdocs(text: str, a: Answers) -> str:
    """Name the library's site and point its edit and issue links at the library's repository.

    Without a repository (``git-local``, or none given) the repository-based settings are dropped, so a local site
    shows no dead "Suggest an edit" or "Raise an issue" link.

    Args:
        text: The template's ``mkdocs.yml``.
        a: The answers.

    Returns:
        The library's ``mkdocs.yml``, comments kept.
    """
    out = _sub_once(text, r"^site_name: .*$", f"site_name: {quote(a.title)}", "site_name")
    if a.platform == "github" and a.repository:
        return out.replace(TEMPLATE_REPOSITORY, a.repository)
    out = re.sub(r"^(?:repo_url|edit_uri): .*\n", "", out, flags=re.MULTILINE)
    out = re.sub(r"^ {4}- content\.action\.edit\n", "", out, flags=re.MULTILINE)
    return re.sub(r"^ {2}social:\n(?: {4,}.*\n)+", "", out, flags=re.MULTILINE)


def rewrite_lock(text: str, a: Answers) -> str:
    """Rename the project's own entry in ``uv.lock`` so the lock still matches ``pyproject.toml``."""
    return re.sub(rf'^name = "{re.escape(TEMPLATE_NAME)}"$', f'name = "{a.name}"', text, count=1, flags=re.MULTILINE)


SEPARATOR = "=" * 71


def _legal_code(root: Path, licence: str) -> str:
    """The legal code of a content licence: from the template's folder, or kept from an earlier run.

    ``licences/`` is removed after the first run, so a rerun keeps the code already in ``LICENSE-content`` when it is
    for the same licence.
    """
    source = root / LICENCE_FOLDER / f"{licence}.txt"
    if source.is_file():
        return _read(source)
    existing = root / "LICENSE-content"
    if existing.is_file():
        head, found, body = _read(existing).partition(f"\n{SEPARATOR}\n\n")
        if found and f"licensed under {licence}." in head:
            return body
    return ""


def code_licence_text(a: Answers, apache: str) -> str:
    """The text of ``LICENSE``: the Apache 2.0 text, the MIT text, or a proprietary notice."""
    if a.code_licence == "Apache-2.0":
        return apache
    if a.code_licence == "MIT":
        return MIT_TEXT.format(year=a.year, holder=a.holder)
    return (
        f"Copyright (c) {a.year} {a.holder}. All rights reserved.\n\n"
        "The code and changes in this repository that the owner wrote are proprietary.\n"
        "Files inherited from the OKF library template remain under the Apache License 2.0:\n"
        "see LICENSE-template and NOTICE.\n"
    )


def content_licence_text(a: Answers, legal_code: str = "") -> str:
    """The text of ``LICENSE-content``: a notice that names the licence, then its full legal code when known."""
    if a.content_licence == "proprietary":
        return f"Copyright (c) {a.year} {a.holder}. All rights reserved.\n\nThe knowledge bundle is proprietary.\n"
    notice = (
        f"Copyright (c) {a.year} {a.holder}\n\n"
        f"The knowledge bundle (the files under knowledge/) is licensed under {a.content_licence}.\n"
        f"Read the licence at {CONTENT_URLS[a.content_licence]}\n"
    )
    return f"{notice}\n{SEPARATOR}\n\n{legal_code}" if legal_code else notice


def readme_text(a: Answers) -> str:
    """The library's ``README.md``: what it is, how to work on it, and which licence covers which path."""
    code = "proprietary" if a.code_licence == "proprietary" else a.code_licence
    platform_note = (
        "It runs on GitHub: pull requests are validated by CI and revision history is written after each merge."
        if a.platform == "github"
        else "It runs on git and Python alone: run `uv run poe check` before each commit and `uv run poe revision` after each merge."
    )
    return (
        f"# {a.title}\n\n{a.description}\n\n"
        "This is an OKF v0.2 knowledge library built from the OKF library template. "
        f"{platform_note}\n\n"
        "## Working on the library\n\n"
        "```bash\nuv sync --all-groups\nuv run poe check\nuv run poe test\n```\n\n"
        "Create a concept with `uv run python scripts/new_concept.py <Type> <path>`.\n\n"
        "## Licences\n\n"
        "| Path | Licence |\n| --- | --- |\n"
        f"| `knowledge/` | {a.content_licence}: see `LICENSE-content` |\n"
        f"| Code and changes by the owner | {code}: see `LICENSE` |\n"
        "| Files inherited from the template | Apache-2.0: see `NOTICE` and, if the code licence differs, `LICENSE-template` |\n"
    )


def citation_text(a: Answers) -> str:
    """The library's ``CITATION.cff``."""
    lines = [
        "cff-version: 1.2.0",
        "message: If you use this library, please cite it using these metadata.",
        f"title: {quote(a.title)}",
        f"abstract: {quote(a.description)}",
        "authors:",
        f"  - name: {quote(a.maintainer_name or a.login)}",
    ]
    if a.content_licence != "proprietary":
        lines.append(f"license: {a.content_licence}")
    if a.repository:
        lines.append(f"repository-code: {quote(a.repository)}")
    return "\n".join(lines) + "\n"


def decisions_text(a: Answers, template_version: str) -> str:
    """``DECISIONS.md`` with the instantiation entry (DR-01, FR5.5)."""
    entry = (
        f"Instantiated from okf-library-template v{template_version} on platform {a.platform}. "
        f"Content licence {a.content_licence}; code licence {a.code_licence}; copyright holder {a.holder}. "
        f"Examples {'kept' if a.keep_examples else 'removed'}; template tests {'kept' if a.keep_tests else 'removed'}."
    )
    return (
        f"# {a.title}: decision record\n\n"
        "Decisions about this library's profile and structure, with the date and the reason. "
        "Each decision is recorded before or with the change.\n\n"
        "| ID | Date | Decision | Status |\n| --- | --- | --- | --- |\n"
        f"| DR-01 | {date.today().isoformat()} | {entry} | Accepted |\n"
    )


def strip_template_block(text: str) -> str:
    """Remove the lines between the ``template-only`` markers of ``AGENTS.md``, markers included."""
    return re.sub(r"<!-- template-only:start -->.*?<!-- template-only:end -->\n+", "", text, flags=re.DOTALL)


@dataclass
class Result:
    """What an instantiation did."""

    changed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def _remove(root: Path, relative: str, result: Result) -> None:
    target = root / relative
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    else:
        return
    result.removed.append(relative)


def _update(root: Path, relative: str, new: str, result: Result) -> None:
    path = root / relative
    if not path.exists() or _read(path) != new:
        _write(path, new)
        result.changed.append(relative)


def _drop_examples(root: Path, result: Result) -> None:
    folder = f"knowledge/{EXAMPLE_FOLDER}"
    if not (root / folder).exists():
        return
    registry = load_registry(root)
    kept = {uid: e for uid, e in registry.entries.items() if not e.path.startswith(f"{EXAMPLE_FOLDER}/")}
    _remove(root, folder, result)
    save_registry(root, Registry(kept))
    result.changed.append("profile/uid-registry.yaml")


def _regenerate_indexes(root: Path, result: Result) -> None:
    """Rebuild every ``index.md``: the root index carries the library's title, and removed examples leave stale lines."""
    profile = load_profile(root)
    expected = expected_indexes(profile, load_bundle(profile.bundle_root, root))
    for index in sorted(profile.bundle_root.rglob("index.md")):
        if index.relative_to(profile.bundle_root).as_posix() not in expected:
            index.unlink()
            result.removed.append(index.relative_to(root).as_posix())
    for relative, text in expected.items():
        _update(root, f"{profile.bundle_root.relative_to(root).as_posix()}/{relative}", text, result)


def _rewrite_files(root: Path, a: Answers, result: Result, profile_text: str, template_version: str) -> None:
    """Rewrite every file that names the library: profile, project, licences, README, citation, decisions, owners."""
    _update(root, "profile/profile.yaml", rewrite_profile(profile_text, a), result)
    _update(root, "pyproject.toml", rewrite_pyproject(_read(root / "pyproject.toml"), a, not a.keep_tests), result)
    if (root / "uv.lock").is_file():
        _update(root, "uv.lock", rewrite_lock(_read(root / "uv.lock"), a), result)
    if (root / "mkdocs.yml").is_file():
        _update(root, "mkdocs.yml", rewrite_mkdocs(_read(root / "mkdocs.yml"), a), result)
    template_licence = root / "LICENSE-template"
    apache = _read(template_licence if template_licence.exists() else root / "LICENSE")
    _update(root, "LICENSE", code_licence_text(a, apache), result)
    if a.code_licence != "Apache-2.0":
        _update(root, "LICENSE-template", apache, result)
    elif template_licence.exists():
        _remove(root, "LICENSE-template", result)
    _update(root, "LICENSE-content", content_licence_text(a, _legal_code(root, a.content_licence)), result)
    _update(root, "README.md", readme_text(a), result)
    _update(root, "CITATION.cff", citation_text(a), result)
    _update(root, "DECISIONS.md", decisions_text(a, template_version), result)
    agents = root / "AGENTS.md"
    if agents.is_file():
        _update(root, "AGENTS.md", strip_template_block(_read(agents)), result)
    owners = root / ".github" / "CODEOWNERS"
    if owners.is_file():
        _update(root, ".github/CODEOWNERS", _read(owners).replace(f"@{TEMPLATE_LOGIN}", f"@{a.login}"), result)
    config = root / ".github" / "ISSUE_TEMPLATE" / "config.yml"
    if config.is_file() and a.platform == "github":
        _update(root, ".github/ISSUE_TEMPLATE/config.yml", issue_config_text(_read(config), a), result)


def instantiate(root: Path, a: Answers) -> Result:
    """Personalise a copy of the template at ``root``.

    Args:
        root: The copy's root folder.
        a: The answers.

    Returns:
        The files changed and removed.

    Raises:
        InitError: If the folder is not a template copy.
        ProfileError: If the profile cannot be loaded (examples are dropped only after a successful load).
    """
    result = Result()
    profile_path = root / "profile" / "profile.yaml"
    if not profile_path.is_file() or not (root / "pyproject.toml").is_file():
        raise InitError(
            [f"{root} does not look like a copy of the template (no profile/profile.yaml or pyproject.toml)"]
        )
    profile_text = _read(profile_path)
    version_match = re.search(r"^template_version: (\S+)", profile_text, re.MULTILINE)
    template_version = version_match[1] if version_match else "unknown"
    _rewrite_files(root, a, result, profile_text, template_version)
    for relative in TEMPLATE_ONLY + (() if a.keep_tests else TEMPLATE_TESTS):
        _remove(root, relative, result)
    if a.platform == "git-local":
        for relative in PLATFORM_ONLY:
            _remove(root, relative, result)
    if not a.keep_examples:
        _drop_examples(root, result)
    result.changed.extend(reset_history(load_profile(root), root))
    _regenerate_indexes(root, result)
    return result


def issue_config_text(text: str, a: Answers) -> str:
    """Point the issue chooser's governance link at the library's repository, or drop the link without one."""
    if a.repository:
        return text.replace(TEMPLATE_REPOSITORY, a.repository)
    return "blank_issues_enabled: false\n"


def leftover_markers(root: Path) -> list[str]:
    """Template identifiers that remain in an instantiated library, outside the places that may name the template.

    The search covers text files only and skips ``NOTICE``, ``LICENSE-template``, ``DECISIONS.md``, ``scripts/``,
    ``tests/``, ``.git/`` and virtual environments.

    Args:
        root: The library's root folder.

    Returns:
        ``path: marker`` for each leftover.
    """
    found: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        skip = (
            relative.startswith((".git/", ".venv"))
            or "/.venv" in relative
            or any(relative == a or relative.startswith(a) for a in MARKER_ALLOWED)
        )
        if skip or not path.is_file():
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        found.extend(f"{relative}: {m}" for m in TEMPLATE_MARKERS if m in text)
    return found
