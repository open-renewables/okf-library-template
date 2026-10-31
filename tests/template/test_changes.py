"""Change rules, directory owners, the approval pre-check, profile warnings and the history rule."""

import json
from pathlib import Path
from typing import Any

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.changes import ChangeContext, Review, check_change_rules, classify, maintainer_logins
from okfprofile.checks import BaseState, check_history_appends, check_profile_warnings, publishing_precheck
from okfprofile.checks.publishing import has_citation
from okfprofile.codeowners import CodeOwners, load_codeowners, parse_codeowners, pattern_regex
from okfprofile.document import parse_concept
from okfprofile.registry import RegistryEntry
from okfprofile.validate import validate_bundle
from support import MakeRepo, item_text

ITEM = "example-group/example-category/example-item.md"
REG = {"ITM-0001": RegistryEntry("example-group/example-category/example-item", "Item")}
SHOWN = f"knowledge/{ITEM}"


def codes(found) -> list[str]:  # type: ignore[no-untyped-def]  # list of Finding
    return sorted(f.code for f in found)


def test_classify_sorts_paths() -> None:
    grouped = classify(
        [
            "scripts/a.py",
            "profile/profile.yaml",
            "profile/uid-registry.yaml",
            "knowledge/x.md",
            "README.md",
            "docs/a.md",
            "uv.lock",
        ],
        "knowledge",
    )
    assert grouped.tooling == ["scripts/a.py", "profile/profile.yaml", "docs/a.md", "uv.lock"]
    assert grouped.content == ["profile/uid-registry.yaml", "knowledge/x.md"]
    assert grouped.other == ["README.md"]


def test_change_context_round_trips_through_json(tmp_path: Path) -> None:
    change = ChangeContext(
        paths=["a"],
        labels={"x"},
        author="al",
        head_sha="h",
        reviews=[Review("bo", True, "h")],
        agent_markers=True,
        reviews_known=True,
    )
    file = tmp_path / "change.json"
    file.write_text(json.dumps(change.to_dict()), encoding="utf-8")
    assert ChangeContext.from_file(file) == change
    assert "reviews" not in ChangeContext(paths=["a"]).to_dict()
    assert not ChangeContext.from_dict({"paths": ["a\\b"]}).reviews_known
    assert ChangeContext.from_dict({"paths": ["a\\b"]}).paths == ["a/b"]


@pytest.mark.parametrize(
    ("pattern", "path", "matches"),
    [
        ("*", "a/b.md", True),
        ("*.md", "docs/a.md", True),
        ("/docs/", "docs/a/b.md", True),
        ("/docs/", "other/docs/a.md", False),
        ("docs/", "a/docs/b.md", True),
        ("/knowledge/*/", "knowledge/group/x.md", True),
        ("/knowledge/a/*.md", "knowledge/a/b/c.md", False),
        ("/knowledge/**/x.md", "knowledge/a/b/x.md", True),
        ("/knowledge/**", "knowledge/a/b/x.md", True),
        ("/scripts/?.py", "scripts/a.py", True),
        ("/scripts/?.py", "scripts/ab.py", False),
        ("/.github/", ".github/CODEOWNERS", True),
    ],
)
def test_owner_patterns(pattern: str, path: str, matches: bool) -> None:
    assert bool(pattern_regex(pattern).match(path)) is matches


def test_last_matching_rule_wins_and_ownership_is_per_file() -> None:
    owners = parse_codeowners(
        "# comment\n\n* @root\n/knowledge/ @group-owner  # trailing comment\n/knowledge/example-group/other.md @someone @org/team\n/knowledge/free.md\n"
    )
    assert owners.owners_for("README.md") == ("@root",)
    assert owners.owners_for("knowledge/example-group/x.md") == ("@group-owner",)
    assert owners.owners_for("./knowledge\\example-group\\other.md") == ("@someone", "@org/team")
    assert owners.owners_for("knowledge/free.md") == ()
    assert owners.is_owner("Group-Owner", "knowledge/a.md")
    assert owners.is_owner("@someone", "knowledge/example-group/other.md")
    assert not owners.is_owner("someone", "knowledge/a.md")
    assert owners.is_owner("org/team", "knowledge/example-group/other.md")
    assert CodeOwners().owners_for("a") == ()


def test_codeowners_files_are_found_in_the_usual_places(tmp_path: Path) -> None:
    assert load_codeowners(tmp_path).rules == []
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CODEOWNERS").write_text("* @docs\n", encoding="utf-8")
    assert load_codeowners(tmp_path).owners_for("x") == ("@docs",)
    (tmp_path / "CODEOWNERS").write_text("* @root\n", encoding="utf-8")
    assert load_codeowners(tmp_path).owners_for("x") == ("@root",)
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("* @github\n", encoding="utf-8")
    assert load_codeowners(tmp_path).owners_for("x") == ("@github",)


MIXED = ["profile/profile.yaml", SHOWN]


def test_the_mixed_change_rule(make_repo: MakeRepo) -> None:
    profile = make_repo({ITEM: item_text()}, REG)
    owners = parse_codeowners("/profile/ @bob\n")
    assert check_change_rules(profile, ChangeContext(paths=[SHOWN]), owners) == []
    assert check_change_rules(profile, ChangeContext(paths=["scripts/a.py"]), owners) == []
    assert codes(check_change_rules(profile, ChangeContext(paths=MIXED), owners)) == ["OKF001"]
    docs_and_content = ChangeContext(paths=["docs/a.md", SHOWN])
    assert codes(check_change_rules(profile, docs_and_content, owners)) == ["OKF001"]


def test_a_migration_needs_approval_and_a_decision_entry(make_repo: MakeRepo) -> None:
    profile = make_repo({ITEM: item_text()}, REG)
    owners = parse_codeowners("/profile/ @bob\n")
    base = {"paths": MIXED, "labels": ["profile-migration"], "author": "alice", "head_sha": "h1"}
    approved = [Review("bob", True, "h1")]
    assert codes(check_change_rules(profile, ChangeContext.from_dict({**base}), owners)) == ["OKF002", "OKF003"]
    stale_change = ChangeContext.from_dict({**base, "reviews": [{"login": "bob", "approved": True, "commit_id": "h0"}]})
    assert codes(check_change_rules(profile, stale_change, owners)) == ["OKF002", "OKF003"]
    good = ChangeContext(
        paths=[*MIXED, "DECISIONS.md"], labels={"profile-migration"}, author="alice", head_sha="h1", reviews=approved
    )
    assert check_change_rules(profile, good, owners) == []
    solo = ChangeContext(paths=[*MIXED, "DECISIONS.md"], labels={"profile-migration"}, author="bob", head_sha="h1")
    assert check_change_rules(profile, solo, owners) == []
    assert maintainer_logins(profile, owners) == {"bob"}


def test_self_approval_of_a_migration_can_be_switched_off(make_repo: MakeRepo) -> None:
    profile = make_repo(
        {ITEM: item_text()},
        REG,
        lambda text: text.replace("require_non_author_approver: false", "require_non_author_approver: true"),
    )
    solo = ChangeContext(paths=[*MIXED, "DECISIONS.md"], labels={"profile-migration"}, author="bob", head_sha="h1")
    assert codes(check_change_rules(profile, solo, parse_codeowners("/profile/ @bob\n"))) == ["OKF002"]


STABLE = item_text().replace("status: draft", "status: stable").replace("Text.", "See [source](https://example.org).")


def precheck(make_repo: MakeRepo, change: ChangeContext, owners: str, text: str = STABLE, edit=None):  # type: ignore[no-untyped-def]
    profile = make_repo({ITEM: text}, REG, edit)
    concepts = load_bundle(profile.bundle_root, profile.root)
    return publishing_precheck(profile, concepts, change, parse_codeowners(owners))


def test_precheck_cases(make_repo: MakeRepo) -> None:
    owners = "/knowledge/ @bob\n"
    change: dict[str, Any] = {"paths": [SHOWN], "author": "alice", "head_sha": "h1", "reviews_known": True}
    assert precheck(make_repo, ChangeContext(**change, reviews=[Review("bob", True, "h1")]), owners) == []
    assert codes(precheck(make_repo, ChangeContext(**change), owners)) == ["OKF701"]
    stale = precheck(make_repo, ChangeContext(**change, reviews=[Review("bob", True, "h0")]), owners)
    assert codes(stale) == ["OKF701"]
    assert "different commit" in stale[0].message
    assert codes(precheck(make_repo, ChangeContext(**change, reviews=[Review("carol", True, "h1")]), owners)) == [
        "OKF701"
    ]
    assert codes(precheck(make_repo, ChangeContext(**change, reviews=[Review("bob", False, "h1")]), owners)) == [
        "OKF701"
    ]
    assert codes(precheck(make_repo, ChangeContext(**change), "/knowledge/ @alice\n")) == ["OKF702"]
    own_review = ChangeContext(**change, reviews=[Review("alice", True, "h1")])
    assert codes(precheck(make_repo, own_review, "/knowledge/ @alice\n")) == ["OKF702"]


def test_precheck_respects_the_profile_switches(make_repo: MakeRepo) -> None:
    change = ChangeContext(paths=[SHOWN], author="alice", head_sha="h1", reviews_known=True)
    owners = "/knowledge/ @alice\n"

    def no_self(text: str) -> str:
        return text.replace("allow_recorded_self_approval: true", "allow_recorded_self_approval: false")

    def off(text: str) -> str:
        return text.replace("stable_requires_human_approval: true", "stable_requires_human_approval: false")

    def two(text: str) -> str:
        return text.replace("stable_approvals: 1", "stable_approvals: 2")

    assert codes(precheck(make_repo, change, owners, edit=no_self)) == ["OKF701"]
    assert precheck(make_repo, change, owners, edit=off) == []
    assert codes(precheck(make_repo, change, owners, edit=two)) == ["OKF701"]
    assert precheck(make_repo, ChangeContext(paths=[SHOWN], author="alice"), owners) == []
    untouched = ChangeContext(paths=["knowledge/other.md"], author="alice", head_sha="h1", reviews_known=True)
    assert precheck(make_repo, untouched, owners) == []
    assert precheck(make_repo, change, owners, text=item_text()) == []


def test_citations(make_repo: MakeRepo) -> None:
    def citations(text: str) -> list[str]:
        profile = make_repo({ITEM: text}, REG)
        return codes(f for f in validate_bundle(profile).findings if f.code == "OKF703")

    assert citations(STABLE) == []
    assert citations(item_text().replace("status: draft", "status: stable")) == ["OKF703"]
    assert (
        citations(
            item_text().replace("status: draft", "status: stable").replace("Text.", "A claim.[^1]\n\n[^1]: Source.")
        )
        == []
    )
    assert citations(item_text()) == []
    assert not has_citation(
        parse_concept("---\ntype: T\n---\n[local](other.md) and ![img](https://example.org/i.png)\n")
    )


def test_profile_warnings(make_repo: MakeRepo) -> None:
    def extra(text: str) -> str:
        return text.replace(
            "warnings:\n",
            "warnings:\n  - id: restates\n    kind: tag_not_equal_segment\n    namespace: category\n    segments: [1]\n    level: low\n    enabled: true\n"
            "  - id: off\n    kind: tag_not_equal_segment\n    namespace: group\n    segments: [0]\n    level: low\n    enabled: false\n",
        )

    profile = make_repo({ITEM: item_text()}, REG, extra)
    concepts = load_bundle(profile.bundle_root, profile.root)
    found = check_profile_warnings(profile, concepts, None)
    assert codes(found) == ["OKF801"]
    assert "[restates]" in found[0].message
    assert all(f.level.value == "warning" for f in found)
    marked = ChangeContext(agent_markers=True)
    assert codes(check_profile_warnings(profile, concepts, marked)) == ["OKF801", "OKF802"]
    labelled = ChangeContext(agent_markers=True, labels={"agent-drafted"})
    assert codes(check_profile_warnings(profile, concepts, labelled)) == ["OKF801"]


def test_history_must_only_grow(make_repo: MakeRepo) -> None:
    line_a = "- 2026-10-20 · author @a · approved @b (owner) · PR #1"
    line_b = "- 2026-10-21 · author @a · approved @b (owner) · PR #2"
    marker = "<!-- Maintained by CI. Do not edit. -->"

    def text(*lines: str) -> str:
        return item_text().replace(marker, "\n".join([marker, *lines]))

    def run(head: str, base: str | None, bot: bool = False) -> list[str]:
        profile = make_repo({ITEM: head}, REG)
        concepts = load_bundle(profile.bundle_root, profile.root)
        earlier = [parse_concept(base, "b.md")] if base else []
        for concept in earlier:
            concept.concept_id = "example-group/example-category/example-item"
        return codes(
            check_history_appends(
                profile, concepts, earlier if base is not None else None, ChangeContext(revision_bot=bot)
            )
        )

    assert run(text(line_a), text(line_a)) == []
    assert run(text(line_a, line_b), text(line_a), bot=True) == []
    assert run(text(line_a, line_b), text(line_a)) == ["OKF315"]
    assert run(text(line_b), text(line_a)) == ["OKF315"]
    assert run(text(), text(line_a)) == ["OKF315"]
    assert run(text(line_a), None) == []
    assert run(text(line_a), "---\ntype: Item\n---\n") == ["OKF315"]
    profile = make_repo({ITEM: text(line_a)}, REG)
    concepts = load_bundle(profile.bundle_root, profile.root)
    assert codes(check_history_appends(profile, concepts, BaseState().concepts, None)) == ["OKF315"]
    assert check_history_appends(profile, concepts, None, None) == []


def test_base_index_matches_a_moved_concept_by_uid() -> None:
    from okfprofile.bundle import BaseIndex

    old = parse_concept("---\ntype: Item\nuid: ITM-0001\n---\n", "old.md")
    old.concept_id = "a/b/old"
    plain = parse_concept("---\ntype: Item\n---\n", "plain.md")
    plain.concept_id = "a/b/plain"
    index = BaseIndex([old, plain])
    moved = parse_concept("---\ntype: Item\nuid: ITM-0001\n---\n", "new.md")
    moved.concept_id = "a/b/new"
    assert index.find(moved) is old
    same_place = parse_concept("---\ntype: Item\nuid: ITM-0009\n---\n", "plain.md")
    same_place.concept_id = "a/b/plain"
    assert index.find(same_place) is plain
    brand_new = parse_concept("---\ntype: Item\n---\n", "x.md")
    brand_new.concept_id = "a/b/x"
    assert index.find(brand_new) is None
