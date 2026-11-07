"""Thin command-line wrapper over okfprofile.ci_cli (SDD C-05)."""

from okfprofile.ci_cli import ci_validate_main

if __name__ == "__main__":
    raise SystemExit(ci_validate_main())
