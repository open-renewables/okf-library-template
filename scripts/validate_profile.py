"""Thin command-line wrapper over okfprofile.cli (SDD C-04)."""

from okfprofile.cli import validate_main

if __name__ == "__main__":
    raise SystemExit(validate_main())
