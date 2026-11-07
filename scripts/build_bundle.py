"""Thin command-line wrapper over okfprofile.release_cli (SDD C-04)."""

from okfprofile.release_cli import build_bundle_main

if __name__ == "__main__":
    raise SystemExit(build_bundle_main())
