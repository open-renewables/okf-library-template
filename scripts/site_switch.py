"""Thin command-line wrapper over okfprofile.site_cli (SDD C-04)."""

from okfprofile.site_cli import site_switch_main

if __name__ == "__main__":
    raise SystemExit(site_switch_main())
