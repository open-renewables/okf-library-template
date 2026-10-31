"""Shared helpers for the template tests."""

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
