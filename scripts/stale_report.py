"""Thin command-line wrapper over okfprofile.revision_cli (SDD C-04)."""

from okfprofile.revision_cli import stale_main

if __name__ == "__main__":
    raise SystemExit(stale_main())
