"""Shared helpers for the template tests."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from okfprofile.config import Profile
from okfprofile.registry import RegistryEntry

ROOT = Path(__file__).resolve().parents[2]

REVISION = "## Revision history\n\n<!-- Maintained by CI. Do not edit. -->\n"


def vocab_text(namespace: str, uid: str, body: str) -> str:
    return (
        f"---\ntype: Vocabulary\nuid: {uid}\ntitle: {namespace.title()}\ndescription: D\nstatus: draft\n"
        f"namespace: {namespace}\n---\n\n# {namespace.title()}\n\n{body}\n\n{REVISION}"
    )


def item_text(
    uid: str = "ITM-0001", tags: str = "group:example-group, category:example-category", description: str = "Text."
) -> str:
    return (
        f"---\ntype: Item\nuid: {uid}\ntitle: T\ndescription: D\ntags: [{tags}]\nstatus: draft\n---\n\n# T\n\n"
        f"## Description\n\n{description}\n\n{REVISION}"
    )


DEFAULT_VOCABS = {
    "vocab/group.md": vocab_text("group", "VOC-0001", "- `example-group`: The group."),
    "vocab/category.md": vocab_text("category", "VOC-0002", "- `example-category`: The category."),
}
DEFAULT_REGISTRY = {
    "VOC-0001": RegistryEntry("vocab/group", "Vocabulary"),
    "VOC-0002": RegistryEntry("vocab/category", "Vocabulary"),
}

MakeRepo = Callable[..., Profile]

PATH = "knowledge/example-group/example-category/example-item.md"


def git(root: Path, *args: str, when: str | None = None) -> str:
    env = dict(os.environ)
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True, env=env, text=True)  # noqa: S603, S607
    return done.stdout.strip()


def edit(root: Path, who: str, subject: str, when: str, trailers: str = "", tag: str = "x") -> str:
    file = root / PATH
    file.write_text(
        file.read_text(encoding="utf-8").replace("plain prose", f"plain prose ({tag})", 1),
        encoding="utf-8",
        newline="\n",
    )
    git(root, "add", "-A")
    args = ["commit", "-q", f"--author={who} <{who}@example.org>", "-m", subject]
    if trailers:
        args += ["-m", trailers]
    git(root, *args, when=when)
    return git(root, "rev-parse", "--short=7", "HEAD")
