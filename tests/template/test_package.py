"""Smoke test: the shared module imports from the configured path."""

import okfprofile


def test_version_is_declared() -> None:
    assert okfprofile.__version__.startswith("0.1.0")
