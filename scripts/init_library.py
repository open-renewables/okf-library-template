"""Thin command-line wrapper over okfprofile.init_cli (SDD C-04)."""

from okfprofile.init_cli import init_library_main

if __name__ == "__main__":
    raise SystemExit(init_library_main())
