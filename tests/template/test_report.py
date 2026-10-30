"""Findings, code registry and the three output formats."""

import json

import pytest
from okfprofile.codes import CODES, Level
from okfprofile.report import Finding, Report


def _finding(code: str = "OKF101", file: str = "a.md", line: int = 1, message: str = "m") -> Finding:
    return Finding.make(code, file, line, message)


def test_every_code_is_well_formed() -> None:
    for code, info in CODES.items():
        assert info.code == code
        assert code.startswith("OKF")
        assert len(code) == 6
        assert info.title


def test_make_takes_default_level_and_allows_override() -> None:
    assert _finding().level is Level.ERROR
    assert Finding.make("OKF101", "a.md", 1, "m", Level.WARNING).level is Level.WARNING


def test_undefined_code_is_rejected() -> None:
    with pytest.raises(ValueError, match="undefined finding code"):
        Finding.make("OKF999", "a.md", 1, "m")


def test_ok_ignores_warnings() -> None:
    report = Report()
    report.add(Finding.make("OKF101", "a.md", 1, "m", Level.WARNING))
    assert report.ok
    assert len(report.warnings) == 1
    report.extend([_finding()])
    assert not report.ok
    assert len(report.errors) == 1


def test_json_and_annotations_agree_and_are_sorted() -> None:
    report = Report([_finding(file="b.md", line=2), _finding(file="a.md", line=9, message="x,y: z")])
    data = json.loads(report.to_json())
    assert [f["file"] for f in data["findings"]] == ["a.md", "b.md"]
    assert data["counts"] == {"error": 2, "warning": 0}
    notes = report.annotations()
    assert len(notes) == len(data["findings"])
    assert notes[0] == "::error file=a.md,line=9,title=OKF101::x,y: z"


def test_annotation_escapes_properties_and_data() -> None:
    report = Report([_finding(file="a:b,c.md", line=0, message="50%\nnext")])
    assert report.annotations() == ["::error file=a%3Ab%2Cc.md,title=OKF101::50%25%0Anext"]


def test_summary_and_human_output() -> None:
    assert Report().summary() == "No findings.\n"
    report = Report([_finding(message="a | b")])
    summary = report.summary()
    assert "1 error(s), 0 warning(s)." in summary
    assert "a \\| b" in summary
    assert report.human() == "a.md:1: error OKF101 a | b"
    assert Report([_finding(line=0)]).human().startswith("a.md:1:")
