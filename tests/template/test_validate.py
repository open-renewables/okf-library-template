"""The validation orchestrator."""

from pathlib import Path

from okfprofile.config import load_profile
from okfprofile.validate import validate_bundle

ROOT = Path(__file__).resolve().parents[2]


def test_a_missing_bundle_folder_has_no_findings(tmp_path: Path) -> None:
    profile = load_profile(ROOT)
    absent = tmp_path / "nowhere"
    object.__setattr__(profile, "bundle_root", absent)
    assert validate_bundle(profile).findings == []
