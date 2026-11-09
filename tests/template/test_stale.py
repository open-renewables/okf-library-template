"""The staleness report (plan step 6, FR3.11, QA-49)."""

import json
import shutil
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from okfprofile.config import Profile, load_profile
from okfprofile.document import Concept, parse_concept
from okfprofile.report import Finding
from okfprofile.revision_cli import stale_main
from okfprofile.stale import DurationError, StaleReport, add_duration, find_stale
from support import PATH, ROOT, edit, git

NOW = datetime(2026, 11, 3, tzinfo=UTC)


@pytest.fixture
def profile(tmp_path: Path) -> Profile:
    shutil.copytree(ROOT / "profile", tmp_path / "profile")
    return load_profile(tmp_path)


def concept(name: str, extra: str = "", lines: tuple[str, ...] = (), status: str = "stable") -> Concept:
    history = "".join(f"- {line}\n" for line in lines)
    text = (
        f"---\ntype: Item\nuid: ITM-{abs(hash(name)) % 9000 + 1000}\nstatus: {status}\n{extra}---\n\n# T\n\n"
        f"## Revision history\n\n<!-- Maintained by CI. Do not edit. -->\n\n{history}"
    )
    parsed = parse_concept(text, f"knowledge/{name}.md")
    parsed.concept_id = name
    return parsed


def line(day: str) -> str:
    return f"{day} · author @bob · approved @alice (owner) · PR #1"


@pytest.mark.parametrize(
    ("start", "text", "expected"),
    [
        (date(2024, 11, 3), "P2Y", date(2026, 11, 3)),
        (date(2024, 2, 29), "P1Y", date(2025, 2, 28)),
        (date(2026, 1, 31), "P1M", date(2026, 2, 28)),
        (date(2026, 11, 30), "P3M", date(2027, 2, 28)),
        (date(2026, 1, 1), "P1Y2M10D", date(2027, 3, 11)),
        (date(2026, 1, 1), "P2W", date(2026, 1, 15)),
        (date(2026, 12, 15), "P1M", date(2027, 1, 15)),
    ],
)
def test_durations_add_calendar_months_and_years(start: date, text: str, expected: date) -> None:
    assert add_duration(start, text) == expected


@pytest.mark.parametrize("text", ["", "P", "2Y", "PT5H", "P1.5Y", "p2y"])
def test_unreadable_durations_are_refused(text: str) -> None:
    with pytest.raises(DurationError, match="cannot read duration"):
        add_duration(date(2026, 1, 1), text)


def test_the_default_interval_makes_a_concept_stale(profile: Profile) -> None:
    fresh = concept("fresh", lines=(line("2025-11-04"),))
    old = concept("old", lines=(line("2024-11-02"),))
    report = find_stale(profile, [fresh, old], NOW)
    assert [(e.concept_id, e.basis, e.due.date().isoformat()) for e in report.stale] == [
        ("old", "default interval", "2026-11-02")
    ]
    assert report.unrevised == []


def test_stale_after_can_only_bring_review_forward(profile: Profile) -> None:
    earlier = concept("earlier", "stale_after: 2026-06-01T00:00:00Z\n", (line("2026-01-01"),))
    later = concept("later", "stale_after: 2030-01-01T00:00:00Z\n", (line("2024-01-01"),))
    report = find_stale(profile, [earlier, later], NOW)
    assert [(e.concept_id, e.basis) for e in report.stale] == [
        ("later", "default interval"),
        ("earlier", "stale_after"),
    ]


def test_a_stale_after_with_another_offset_is_compared_as_an_instant(profile: Profile) -> None:
    edge = concept("edge", "stale_after: 2026-11-03T05:00:00+06:00\n", (line("2026-10-01"),))
    assert find_stale(profile, [edge], NOW).stale[0].due == datetime(2026, 11, 2, 23, 0, tzinfo=UTC)


@pytest.mark.parametrize("value", ["2026-01-01", "2026-01-01T00:00:00", "not a date", "42"])
def test_a_stale_after_without_an_offset_or_unreadable_is_ignored(profile: Profile, value: str) -> None:
    c = concept("c", f'stale_after: "{value}"\n', (line("2026-10-01"),))
    assert find_stale(profile, [c], NOW).stale == []


def test_a_concept_with_no_revision_is_unverified_not_stale(profile: Profile) -> None:
    report = find_stale(profile, [concept("never")], NOW)
    assert (report.stale, report.unrevised) == ([], ["knowledge/never.md"])


def test_a_concept_with_no_revision_is_stale_if_its_own_date_has_passed(profile: Profile) -> None:
    report = find_stale(profile, [concept("c", "stale_after: 2026-01-01T00:00:00Z\n")], NOW)
    assert [(e.basis, e.last_revision) for e in report.stale] == [("stale_after", None)]
    assert report.unrevised == ["knowledge/c.md"]


def test_deprecated_concepts_are_left_out(profile: Profile) -> None:
    old = concept("old", lines=(line("2020-01-01"),), status="deprecated")
    assert find_stale(profile, [old], NOW).stale == []


def test_the_latest_revision_counts_whatever_the_order(profile: Profile) -> None:
    c = concept("c", lines=(line("2026-09-01"), line("2020-01-01")))
    assert find_stale(profile, [c], NOW).stale == []


def test_the_report_renders_every_form(profile: Profile) -> None:
    report = find_stale(profile, [concept("old", lines=(line("2020-01-01"),)), concept("never")], NOW)
    report.gaps = [Finding.make("OKF901", "knowledge/x.md", 3, "merged change PR #4 (abc1234) has no revision line")]
    markdown = report.to_markdown()
    assert markdown.startswith("<!-- stale-report -->\n")
    assert "| `knowledge/old.md` | ITM-" in markdown
    assert "| 2022-01-01 | default interval | 2020-01-01 |" in markdown
    assert "- `knowledge/never.md`" in markdown
    assert "- `knowledge/x.md`: merged change PR #4" in markdown
    data = json.loads(report.to_json())
    assert data["as_of"] == "2026-11-03T00:00:00Z"
    assert data["stale"][0]["due"] == "2022-01-01T00:00:00Z"
    assert data["revision_gaps"][0]["line"] == 3
    assert "stale since 2022-01-01 (default interval)" in report.human()
    empty = StaleReport(NOW)
    assert "None." in empty.to_markdown()
    assert json.loads(empty.to_json())["revision_gaps"] is None
    assert empty.human() == ""


def test_the_command_line_reports_and_never_fails_on_findings(
    tmp_path: Path, library: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "issue.md"
    assert stale_main(["--root", str(library), "--now", "2030-01-01T00:00:00Z", "--json", "--markdown", str(out)]) == 0
    assert len(json.loads(capsys.readouterr().out)["unrevised"]) >= 4
    assert out.read_text(encoding="utf-8").startswith("<!-- stale-report -->")
    assert stale_main(["--root", str(ROOT)]) == 0


@pytest.mark.parametrize("args", [["--now", "2026-11-03"], ["--now", "garbage"]])
def test_a_bad_instant_is_a_usage_error(args: list[str]) -> None:
    assert stale_main(["--root", str(ROOT), *args]) == 2


def test_a_missing_profile_is_a_usage_error(tmp_path: Path) -> None:
    assert stale_main(["--root", str(tmp_path)]) == 2


def test_check_since_adds_the_changes_without_a_revision_line(
    library: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    git(library, "tag", "v0.0.1")
    edit(library, "alice", "Edit", "2026-11-01T10:00:00+00:00")
    assert (
        stale_main(["--root", str(library), "--check-since", "v0.0.1", "--now", "2026-11-03T00:00:00Z", "--json"]) == 0
    )
    gaps = json.loads(capsys.readouterr().out)["revision_gaps"]
    assert [g["file"] for g in gaps] == [PATH]
    assert stale_main(["--root", str(library), "--check-since", "no-such-tag"]) == 2
