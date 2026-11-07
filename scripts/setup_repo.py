"""Thin command-line wrapper over okfprofile.setup_cli (SDD C-04)."""

from okfprofile.setup_cli import setup_repo_main

if __name__ == "__main__":
    raise SystemExit(setup_repo_main())
