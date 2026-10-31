"""The revision-line grammar (SDD I-08)."""

from datetime import date

import pytest
from okfprofile.revision import parse_revision_line

OWNER = "2026-10-20 · author @alice · approved @bob (owner) · PR #12"


def test_a_full_line_is_parsed() -> None:
    line = parse_revision_line(OWNER + " · full-review · agent-drafted")
    assert line is not None
    assert line.date == date(2026, 10, 20)
    assert (line.author, line.approval, line.approver, line.owner) == ("alice", "approved", "bob", True)
    assert (line.change, line.reference) == ("pr", "12")
    assert line.full_review
    assert line.agent_drafted


@pytest.mark.parametrize(
    ("text", "approval", "approver", "owner", "change", "reference"),
    [
        ("2026-10-20 · author @a · approved (stale) @b (non-owner) · PR #3", "approved-stale", "b", False, "pr", "3"),
        ("2026-10-20 · author @a · self-approved (owner) · PR none", "self-approved", None, True, "pr-none", None),
        (
            "2026-10-20 · author @a · self-approved (non-owner) · commit 1a2b3c4",
            "self-approved",
            None,
            False,
            "commit",
            "1a2b3c4",
        ),
        (
            "2026-10-20 · author @a · merged without approval @m · PR #9",
            "merged-without-approval",
            "m",
            None,
            "pr",
            "9",
        ),
        ("2026-10-20 · author @first.last · approved @b_c (owner) · PR #1", "approved", "b_c", True, "pr", "1"),
    ],
)
def test_each_approval_and_change_form(
    text: str, approval: str, approver: str | None, owner: bool | None, change: str, reference: str | None
) -> None:
    line = parse_revision_line(text)
    assert line is not None
    assert (line.approval, line.approver, line.owner, line.change, line.reference) == (
        approval,
        approver,
        owner,
        change,
        reference,
    )
    assert not line.full_review
    assert not line.agent_drafted


def test_flags_individually() -> None:
    assert parse_revision_line(OWNER + " · agent-drafted").agent_drafted  # type: ignore[union-attr]  # parse result checked by the next line
    only_full = parse_revision_line(OWNER + " · full-review")
    assert only_full is not None
    assert only_full.full_review
    assert not only_full.agent_drafted


@pytest.mark.parametrize(
    "text",
    [
        "",
        "edited by hand",
        "2026-13-45 · author @a · approved @b (owner) · PR #1",
        "20261020 · author @a · approved @b (owner) · PR #1",
        "2026-10-20 · by @a · approved @b (owner) · PR #1",
        "2026-10-20 · author @a · approved @b · PR #1",
        "2026-10-20 · author @a · approved @b (maybe) · PR #1",
        "2026-10-20 · author @a · approved @b (owner) · PR 1",
        "2026-10-20 · author @a · approved @b (owner) · commit 1a2b3c",
        "2026-10-20 · author @a · approved @b (owner) · commit 1A2B3C4",
        OWNER + " · agent-drafted · full-review",
        OWNER + " · full-review · full-review",
        OWNER + " · reviewed",
        "2026-10-20 · author @a · approved @b (owner)",
    ],
)
def test_lines_outside_the_grammar_are_rejected(text: str) -> None:
    assert parse_revision_line(text) is None
