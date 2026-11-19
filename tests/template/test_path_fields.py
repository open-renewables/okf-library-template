"""Check 4 path fields: frontmatter path values resolve by OKF v0.3 section 6.2 (RFC-002 item 4, OKF412)."""

from okfprofile.bundle import load_bundle
from okfprofile.checks.links import check_links, path_fields
from okfprofile.registry import RegistryEntry
from support import MakeRepo, item_text

ITEM_ID = "example-group/example-category/example-item"


def test_path_fields_resolve_by_okf_v0_3_section_6_2(make_repo: MakeRepo) -> None:
    """Relative to the concept's folder, or from the bundle root with a leading `/`; URIs and scope text skipped."""
    item = item_text().replace(
        "status: draft\n",
        "status: draft\n"
        "resource: ../example-category/example-item.md\n"
        "computation: /vocab/group.md\n"
        "executor: { resource: https://example.org/run }\n"
        "sources:\n"
        "  - resource: the whole orders table\n"
        "  - resource: //cdn.example.org/x\n"
        "  - resource: nowhere.md\n",
    )
    profile = make_repo(
        {"example-group/example-category/example-item.md": item}, {"ITM-0001": RegistryEntry(ITEM_ID, "Item")}
    )
    concepts = load_bundle(profile.bundle_root, profile.root)
    found = [f for f in check_links(profile, concepts) if f.code == "OKF412"]
    assert [(f.code, f.line) for f in found] == [("OKF412", 14)]
    assert "`sources.2.resource` 'nowhere.md'" in found[0].message


def test_path_fields_lists_only_path_values() -> None:
    front = {
        "resource": "a.md",
        "superseded_by": 5,
        "attester": {"resource": "/refs/check.py"},
        "executor": "not a mapping",
        "sources": [{"resource": "urn:isbn:1"}, "x", {"resource": ""}],
    }
    assert path_fields(front) == [(("resource",), "a.md"), (("attester", "resource"), "/refs/check.py")]
