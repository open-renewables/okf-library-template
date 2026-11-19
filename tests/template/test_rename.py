"""Renaming the primary type and its uid prefix (G23, ``rename_type.py``)."""

import shutil
from pathlib import Path

import pytest
from okfprofile.bundle import load_bundle
from okfprofile.changes import ChangeContext
from okfprofile.cli import rename_type_main
from okfprofile.config import load_profile
from okfprofile.indexes import write_indexes
from okfprofile.rename import rename_type
from okfprofile.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A copy of the parts of the repository that a rename touches."""
    for part in ("profile", "knowledge", "tests/library"):
        shutil.copytree(ROOT / part, tmp_path / part)
    return tmp_path


def _fixture_codes(library: Path, fixture: Path, scratch: Path) -> set[str]:
    shutil.copytree(library / "profile", scratch / "profile")
    if (fixture / "profile").is_dir():
        shutil.copytree(fixture / "profile", scratch / "profile", dirs_exist_ok=True)
    shutil.copytree(fixture / "knowledge", scratch / "knowledge")
    if (fixture / "CODEOWNERS").is_file():
        (scratch / ".github").mkdir()
        shutil.copy2(fixture / "CODEOWNERS", scratch / ".github" / "CODEOWNERS")
    profile = load_profile(scratch)
    if not (fixture / "no-indexes").exists():
        write_indexes(profile, load_bundle(profile.bundle_root, scratch), only_missing=True)
    change = ChangeContext.from_file(fixture / "change.json") if (fixture / "change.json").exists() else None
    return {f.code for f in validate_bundle(profile, None, change).findings}


def test_renaming_the_primary_type_keeps_the_library_valid(library: Path, tmp_path: Path) -> None:
    profile = load_profile(library)
    result = rename_type(profile, "Item", "Risk", "RSK")
    assert ("profile/types/item.schema.json", "profile/types/risk.schema.json") in result.moved
    renamed = load_profile(library)
    assert next(t.name for t in renamed.types) == "Risk"
    assert renamed.type_named("Risk").uid_prefix == "RSK"  # type: ignore[union-attr]
    write_indexes(renamed, load_bundle(renamed.bundle_root, library))
    assert validate_bundle(renamed).errors == []
    for folder in ("profile", "knowledge"):
        for file in (library / folder).rglob("*"):
            if file.is_file() and "schemas" not in file.parts:
                text = file.read_text(encoding="utf-8")
                assert "ITM-" not in text, file
                assert "type: Item" not in text, file
    fixtures = library / "tests" / "library" / "fixtures"
    for kind in ("pass", "fail"):
        for fixture in sorted(p for p in (fixtures / kind).iterdir() if p.is_dir()):
            if (fixture / "base").is_dir():
                continue  # base-state fixtures need a base commit; the library's own test run covers them
            scratch = tmp_path / "runs" / kind / fixture.name
            codes = _fixture_codes(library, fixture, scratch)
            if kind == "fail":
                assert codes == {fixture.name}, fixture.name
            else:
                errors = validate_bundle(load_profile(scratch)).errors
                assert errors == [], fixture.name


def test_prose_and_meta_schemas_are_left_alone(library: Path) -> None:
    concept = library / "knowledge" / "example-group" / "example-category" / "example-item.md"
    concept.write_text(concept.read_text(encoding="utf-8") + "\nAn Item is cited as ITM-0001.\n", encoding="utf-8")
    meta = (library / "profile" / "schemas" / "profile.schema.json").read_text(encoding="utf-8")
    rename_type(load_profile(library), "Item", "Risk", "RSK")
    text = concept.read_text(encoding="utf-8")
    assert "type: Risk" in text
    assert "uid: RSK-0001" in text
    assert "An Item is cited as ITM-0001." in text
    assert (library / "profile" / "schemas" / "profile.schema.json").read_text(encoding="utf-8") == meta


def test_a_dry_run_writes_nothing(library: Path) -> None:
    before = (library / "profile" / "profile.yaml").read_text(encoding="utf-8")
    result = rename_type(load_profile(library), "Item", "Risk", "RSK", dry_run=True)
    assert "profile/profile.yaml" in result.changed
    assert (library / "profile" / "profile.yaml").read_text(encoding="utf-8") == before
    assert (library / "profile" / "types" / "item.schema.json").is_file()


@pytest.mark.parametrize(
    ("old", "new", "prefix", "message"),
    [
        ("Widget", "Risk", "RSK", "not declared"),
        ("Item", "risk", "RSK", "capital letter"),
        ("Item", "Risk", "rsk", "two to five capital letters"),
        ("Item", "Risk", "R", "two to five capital letters"),
        ("Item", "Glossary", "RSK", "already used"),
        ("Item", "Risk", "VOC", "already used"),
    ],
)
def test_bad_renames_are_refused(library: Path, old: str, new: str, prefix: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        rename_type(load_profile(library), old, new, prefix)


def test_the_command_line(library: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert rename_type_main(["--root", str(library), "Item", "Risk", "RSK", "--dry-run", "--json"]) == 0
    assert '"dry_run": true' in capsys.readouterr().out
    assert rename_type_main(["--root", str(library), "Widget", "Risk", "RSK"]) == 2
    assert rename_type_main(["--root", str(library), "Item", "Risk", "RSK"]) == 0
    assert (library / "profile" / "types" / "risk.schema.json").is_file()
    assert (library / "knowledge" / "index.md").is_file()


def test_a_binary_file_is_skipped_and_bad_text_changes_nothing(library: Path) -> None:
    (library / "knowledge" / "diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe\x00")
    rename_type(load_profile(library), "Item", "Risk", "RSK")
    assert (library / "profile" / "types" / "risk.schema.json").is_file()
    profile_text = (library / "profile" / "profile.yaml").read_text(encoding="utf-8")
    bad = library / "knowledge" / "notes.md"
    bad.write_bytes(b"---\ntype: Risk\n---\n\xff\xfe")
    with pytest.raises(ValueError, match="not UTF-8 text; nothing was changed"):
        rename_type(load_profile(library), "Risk", "Hazard", "HAZ")
    assert (library / "profile" / "profile.yaml").read_text(encoding="utf-8") == profile_text
    assert (library / "profile" / "types" / "risk.schema.json").is_file()


def test_another_types_schema_file_name_is_left_alone(library: Path) -> None:
    profile_file = library / "profile" / "profile.yaml"
    profile_file.write_text(
        profile_file.read_text(encoding="utf-8") + "# see types/work-item.schema.json\n", encoding="utf-8"
    )
    rename_type(load_profile(library), "Item", "Risk", "RSK")
    text = profile_file.read_text(encoding="utf-8")
    assert "types/work-item.schema.json" in text
    assert "schema: types/risk.schema.json" in text


def test_an_existing_target_schema_refuses_before_writing(library: Path) -> None:
    (library / "profile" / "types" / "risk.schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "risk.schema.json"}', encoding="utf-8"
    )
    before = (library / "profile" / "profile.yaml").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="already exists; nothing was changed"):
        rename_type(load_profile(library), "Item", "Risk", "RSK")
    assert (library / "profile" / "profile.yaml").read_text(encoding="utf-8") == before


def test_the_command_line_warns_when_the_registry_is_committed(
    library: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import subprocess

    def run(*args: str) -> None:
        subprocess.run(["git", *args], cwd=library, check=True, capture_output=True)  # noqa: S603, S607

    run("init", "-q")
    assert rename_type_main(["--root", str(library), "Item", "Risk", "RSK", "--dry-run"]) == 0
    assert "already committed" not in capsys.readouterr().err
    run("add", "-A")
    run("-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "-m", "init")
    assert rename_type_main(["--root", str(library), "Item", "Risk", "RSK", "--dry-run"]) == 0
    assert "already committed" in capsys.readouterr().err
