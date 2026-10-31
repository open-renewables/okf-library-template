"""Thin command-line wrapper over okfprofile.cli (SDD C-04)."""

from okfprofile.cli import renumber_main

if __name__ == "__main__":
    raise SystemExit(renumber_main())
