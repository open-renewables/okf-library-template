"""Thin command-line wrapper over okfprofile.release_cli (SDD C-04)."""

from okfprofile.release_cli import release_main

if __name__ == "__main__":
    raise SystemExit(release_main())
