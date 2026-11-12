"""Thin command-line wrapper over okfprofile.skills_cli (SDD C-04)."""

from okfprofile.skills_cli import check_skills_main

if __name__ == "__main__":
    raise SystemExit(check_skills_main())
