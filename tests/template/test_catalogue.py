"""The finding-code catalogue lists every code with a fixture or test that exists."""

import re
from pathlib import Path

from okfprofile.codes import CODES

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "development"
CATALOGUE = DOCS / "architecture" / "finding-codes.md"
ROW = re.compile(r"^\| (OKF\d{3}) \|.*\| (?P<fixture>[^|]+) \|\s*$")
PATH = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\]\(([^)#\s][^)\s]*|<[^>]+>)\)")


def catalogue_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in CATALOGUE.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if match:
            rows[match.group(1)] = match.group("fixture")
    return rows


def test_every_code_has_a_catalogue_row_and_no_row_is_unknown() -> None:
    rows = catalogue_rows()
    assert sorted(set(CODES) - set(rows)) == [], "codes missing from finding-codes.md"
    assert sorted(set(rows) - set(CODES)) == [], "rows in finding-codes.md for codes that do not exist"


def test_every_listed_fixture_path_exists() -> None:
    missing = []
    for code, cell in catalogue_rows().items():
        paths = [p for p in PATH.findall(cell) if "/" in p]
        if not paths:
            missing.append(f"{code}: no path in '{cell.strip()}'")
        missing.extend(f"{code}: {p}" for p in paths if not (ROOT / p).exists())
    assert missing == []


def test_relative_links_in_testing_documents_resolve() -> None:
    broken = []
    for doc in sorted((DOCS / "testing").glob("*.md")):
        for target in LINK.findall(doc.read_text(encoding="utf-8")):
            target = target.strip("<>")
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (doc.parent / target.replace("%20", " ")).exists():
                broken.append(f"{doc.name}: {target}")
    assert broken == []
