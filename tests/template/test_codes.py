"""The code registry rejects duplicates."""

import pytest
from okfprofile.codes import CodeInfo, Level, _define


def test_duplicate_code_is_rejected() -> None:
    info = CodeInfo("OKF900", Level.ERROR, "test", "title")
    with pytest.raises(ValueError, match="duplicate finding code OKF900"):
        _define(info, info)
