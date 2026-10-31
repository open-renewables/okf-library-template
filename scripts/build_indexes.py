"""Thin command-line wrapper over okfprofile.cli (SDD C-04)."""

from okfprofile.cli import build_indexes_main

if __name__ == "__main__":
    raise SystemExit(build_indexes_main())
