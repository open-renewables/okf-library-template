"""Build and check the static site (SDD C-07, W-08, I-13; ADR-001).

One ``mkdocs.yml`` is read by two builders, MkDocs with Material and Zensical. The profile's ``site.generator`` names the
primary (blocking, default ``mkdocs``); the other builds as a non-blocking comparison. The site is built from
``knowledge/`` in place. Zensical skips settings it does not support without a warning, so its output is
judged by page lists and link checks, not by its exit code.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

BUILDERS = ("mkdocs", "zensical")
DEFAULT_GENERATOR = "mkdocs"
PRIMARY_OUT = "site"
ALT_OUT = "site-alt"
CONFIG = "mkdocs.yml"
SEMVER = re.compile(r"^v(?P<major>0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?P<pre>-[0-9A-Za-z][0-9A-Za-z.-]*)?$")
NOT_PAGES = ("assets", "search", "tags", "css", "javascripts")
MANIFEST = "release.json"


class SiteError(Exception):
    """The site cannot be built or checked."""


@dataclass(frozen=True)
class PageComparison:
    """The result of comparing the pages a build produced with the pages the bundle should give.

    Attributes:
        missing: Expected pages the build did not produce.
        extra: Built pages no concept explains.
    """

    missing: tuple[str, ...]
    extra: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True when the build holds exactly the expected pages."""
        return not self.missing and not self.extra


def generator(root: Path) -> str:
    """The blocking site builder, ``site.generator`` from the profile (``mkdocs`` if the key is absent).

    Args:
        root: Repository root.

    Returns:
        ``mkdocs`` or ``zensical``.

    Raises:
        SiteError: If the profile names another generator.
    """
    path = root / "profile" / "profile.yaml"
    try:
        data = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except (OSError, YAMLError):
        return DEFAULT_GENERATOR
    section = data.get("site") if isinstance(data, dict) else None
    value = str(section.get("generator", DEFAULT_GENERATOR)) if isinstance(section, dict) else DEFAULT_GENERATOR
    if value not in BUILDERS:
        msg = f"site.generator '{value}' is not one of {', '.join(BUILDERS)}"
        raise SiteError(msg)
    return value


def resolve(root: Path, name: str) -> str:
    """Turn ``primary`` or ``alt`` into the builder it means for this library; a builder name stays as it is.

    Raises:
        SiteError: If ``name`` is none of ``primary``, ``alt``, ``mkdocs`` or ``zensical``.
    """
    chosen = generator(root)
    if name == "primary":
        return chosen
    if name == "alt":
        return next(b for b in BUILDERS if b != chosen)
    if name not in BUILDERS:
        msg = f"unknown builder '{name}'; use primary, alt or one of {', '.join(BUILDERS)}"
        raise SiteError(msg)
    return name


def default_out(root: Path, builder: str) -> Path:
    """Where a builder writes by default: ``site/`` for the library's generator, ``site-alt/`` for the other."""
    return root / (PRIMARY_OUT if builder == generator(root) else ALT_OUT)


def docs_dir(root: Path) -> Path:
    """The folder the site is built from, read from ``mkdocs.yml``.

    Args:
        root: Repository root.

    Returns:
        Absolute path of ``docs_dir``.

    Raises:
        SiteError: If ``mkdocs.yml`` is missing or unreadable.
    """
    config = root / CONFIG
    if not config.is_file():
        msg = f"no {CONFIG} under {root}"
        raise SiteError(msg)
    try:
        data = YAML(typ="safe").load(config.read_text(encoding="utf-8"))
    except YAMLError as exc:
        msg = f"{CONFIG} is not readable YAML: {exc}"
        raise SiteError(msg) from exc
    folder = data.get("docs_dir", "docs") if isinstance(data, dict) else "docs"
    return (root / str(folder)).resolve()


def expected_pages(folder: Path) -> set[str]:
    """The page each Markdown file should give, as a path under the site folder (directory URLs).

    Args:
        folder: The ``docs_dir`` folder.

    Returns:
        Site-relative paths such as ``a/b/index.html``.
    """
    pages = set()
    for file in folder.rglob("*.md"):
        stem = file.relative_to(folder).as_posix().removesuffix(".md")
        if stem == "index":
            pages.add("index.html")
        elif stem.endswith("/index"):
            pages.add(f"{stem}.html")
        else:
            pages.add(f"{stem}/index.html")
    return pages


def built_pages(site: Path) -> set[str]:
    """The content pages a build produced (not the 404 page, search or asset folders).

    Args:
        site: The built site folder.

    Returns:
        Site-relative paths of ``.html`` files.
    """
    pages = set()
    for file in site.rglob("*.html"):
        relative = file.relative_to(site).as_posix()
        if relative == "404.html" or relative.split("/")[0] in NOT_PAGES:
            continue
        pages.add(relative)
    return pages


def compare_pages(folder: Path, site: Path) -> PageComparison:
    """Compare a build with the bundle.

    Args:
        folder: The ``docs_dir`` folder.
        site: The built site folder.

    Returns:
        Missing and extra pages, each sorted.
    """
    expected, built = expected_pages(folder), built_pages(site)
    return PageComparison(tuple(sorted(expected - built)), tuple(sorted(built - expected)))


def _command(builder: str, config: Path, out: Path) -> list[str]:
    if builder == "mkdocs":
        return [sys.executable, "-m", "mkdocs", "build", "--strict", "-f", str(config), "-d", str(out)]
    return [sys.executable, "-m", "zensical", "build", "-f", str(config)]


def installed(builder: str) -> bool:
    """Whether the builder's package can be imported here."""
    probe = subprocess.run(  # noqa: S603 - fixed arguments
        [sys.executable, "-c", f"import {builder}"], capture_output=True, check=False
    )
    return probe.returncode == 0


def build(root: Path, builder: str, out: Path | None = None) -> Path:
    """Build the site with one builder.

    MkDocs builds in place and writes to ``out``. Zensical has no output option, so it builds a temporary copy of the
    configuration and bundle and the result is moved to ``out``; the working tree is never written.

    Args:
        root: Repository root.
        builder: ``mkdocs`` or ``zensical`` (``primary`` and ``alt`` are resolved by the caller with ``resolve``).
        out: Output folder; ``site`` for the profile's generator and ``site-alt`` for the other if omitted.

    Returns:
        The output folder.

    Raises:
        SiteError: If the builder is unknown, not installed or fails.
    """
    if builder not in BUILDERS:
        msg = f"unknown builder '{builder}'; use one of {', '.join(BUILDERS)}"
        raise SiteError(msg)
    if not installed(builder):
        msg = f"{builder} is not installed; run: uv sync --group site-{builder}"
        raise SiteError(msg)
    target = (out or default_out(root, builder)).resolve()
    config = root / CONFIG
    if not config.is_file():
        msg = f"no {CONFIG} under {root}"
        raise SiteError(msg)
    env = {**os.environ, "NO_MKDOCS_2_WARNING": "true", "PYTHONUTF8": "1"}
    if builder == "mkdocs":
        done = subprocess.run(  # noqa: S603 - fixed arguments
            _command(builder, config, target), cwd=root, env=env, capture_output=True, check=False, text=True
        )
        _report(done)
        return target
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        shutil.copy2(config, work / CONFIG)
        shutil.copytree(docs_dir(root), work / docs_dir(root).relative_to(root))
        done = subprocess.run(  # noqa: S603 - fixed arguments
            _command(builder, work / CONFIG, target), cwd=work, env=env, capture_output=True, check=False, text=True
        )
        _report(done)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(work / "site", target)
    return target


def _report(done: subprocess.CompletedProcess[str]) -> None:
    for stream in (done.stdout, done.stderr):
        for line in stream.splitlines():
            if line.strip() and "│" not in line and "└" not in line and "┌" not in line:
                print(line, file=sys.stderr)
    if done.returncode != 0:
        msg = f"the build exited with {done.returncode}"
        raise SiteError(msg)


def write_manifest(site: Path, tag: str, commit: str) -> Path:
    """Write ``release.json`` into a built site, so the site names the release it was built from (FR8.3).

    Args:
        site: The built site folder.
        tag: The release tag.
        commit: The commit the tag points to.

    Returns:
        The manifest path.

    Raises:
        SiteError: If the tag is not a semantic-version tag or the site folder does not exist.
    """
    if not SEMVER.match(tag):
        msg = f"'{tag}' is not a version tag such as v1.2.3"
        raise SiteError(msg)
    if not site.is_dir():
        msg = f"{site} is not a built site"
        raise SiteError(msg)
    path = site / MANIFEST
    path.write_text(json.dumps({"tag": tag, "commit": commit}, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def site_url(root: Path) -> str:
    """``library.site_url`` from the profile; empty if unset.

    Args:
        root: Repository root.

    Returns:
        The URL, or an empty string.
    """
    path = root / "profile" / "profile.yaml"
    try:
        data = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
    except (OSError, YAMLError):
        return ""
    library = data.get("library") if isinstance(data, dict) else None
    value = library.get("site_url") if isinstance(library, dict) else ""
    return str(value or "")


def should_deploy(root: Path, ref: str) -> bool:
    """Whether a tag run publishes the site (FR8.5): a stable tag of v1.0.0 or later, and a site URL in the profile.

    Args:
        root: Repository root.
        ref: A tag name, or a ref such as ``refs/tags/v1.0.0``.

    Returns:
        True only for a tag with major version 1 or more and no pre-release suffix, in a library with a site URL.
    """
    match = SEMVER.match(ref.removeprefix("refs/tags/"))
    if match is None or match["pre"] or int(match["major"]) < 1:
        return False
    return bool(site_url(root))


def serve(root: Path) -> int:
    """Serve the site with live reload using the profile's generator; returns the builder's exit code.

    Raises:
        SiteError: If the generator is not installed.
    """
    builder = generator(root)
    if not installed(builder):
        msg = f"{builder} is not installed; run: uv sync --group site-{builder}"
        raise SiteError(msg)
    env = {**os.environ, "NO_MKDOCS_2_WARNING": "true", "PYTHONUTF8": "1"}
    return subprocess.run(  # noqa: S603 - fixed arguments
        [sys.executable, "-m", builder, "serve", "-f", str(root / CONFIG)], cwd=root, env=env, check=False
    ).returncode


_GENERATOR_LINE = re.compile(r"^(  generator: )\S+", re.MULTILINE)
_PLATFORM_LINE = re.compile(r"^platform: .*$", re.MULTILINE)
_README_SENTENCE = re.compile(r"^The site is built with .*$", re.MULTILINE)


def _profile_with(text: str, new: str) -> str:
    """The profile text with ``site.generator`` set to ``new``: the existing line, or a new ``site`` block."""
    if _GENERATOR_LINE.search(text):
        return _GENERATOR_LINE.sub(rf"\g<1>{new}", text, count=1)
    block = f"site:\n  generator: {new}"
    if "\nsite:" in text or text.startswith("site:") or not _PLATFORM_LINE.search(text):
        msg = "profile.yaml has a site key without site.generator, or no platform line to place one after"
        raise SiteError(msg)
    return _PLATFORM_LINE.sub(lambda m: f"{m.group(0)}\n{block}", text, count=1)


def _readme_with(text: str, new: str) -> str:
    """The README's generated sentence about the site, pointing at ``new``; unchanged if the README has none."""

    def fix(match: re.Match[str]) -> str:
        line = re.sub(r"built with \w+ ", f"built with {new.title()} ", match.group(0), count=1)
        return re.sub(r"site-(?:mkdocs|zensical)", f"site-{new}", line, count=1)

    return _README_SENTENCE.sub(fix, text, count=1)


def _verify_build(root: Path, builder: str) -> None:
    """Build the site with ``builder`` into a scratch folder and require exactly the bundle's pages."""
    with tempfile.TemporaryDirectory() as scratch:
        result = compare_pages(docs_dir(root), build(root, builder, Path(scratch) / "site"))
    if not result.ok:
        msg = f"the {builder} build lacks pages {list(result.missing)} or has extra pages {list(result.extra)}"
        raise SiteError(msg)


def switch_generator(root: Path, new: str, verify: bool = True) -> list[str]:
    """Make ``new`` the library's blocking site generator (ADR-011).

    Rewrites ``site.generator`` in ``profile/profile.yaml`` and the generated sentence in ``README.md``. With
    ``verify`` it then builds the site with ``new`` (strict) and compares the pages with the bundle; if that fails
    both files are put back as they were.

    Args:
        root: Repository root.
        new: ``mkdocs`` or ``zensical``.
        verify: Build the site with ``new`` after the switch and check its pages.

    Returns:
        The files changed, relative to the root; empty if ``new`` is already the generator.

    Raises:
        SiteError: If ``new`` is unknown, the profile cannot be edited, or the verifying build fails.
    """
    if new not in BUILDERS:
        msg = f"unknown generator '{new}'; use one of {', '.join(BUILDERS)}"
        raise SiteError(msg)
    if generator(root) == new:
        return []
    profile = root / "profile" / "profile.yaml"
    readme = root / "README.md"
    before = {path: path.read_bytes() for path in (profile, readme) if path.is_file()}
    try:
        profile.write_text(_profile_with(profile.read_text(encoding="utf-8"), new), encoding="utf-8", newline="\n")
        if readme.is_file():
            readme.write_text(_readme_with(readme.read_text(encoding="utf-8"), new), encoding="utf-8", newline="\n")
        if verify:
            _verify_build(root, new)
    except (SiteError, OSError):
        for path, data in before.items():
            path.write_bytes(data)
        raise
    return [path.relative_to(root).as_posix() for path, data in before.items() if path.read_bytes() != data]
