"""Thin command-line wrapper over okfprofile.supply_cli (SDD C-04)."""

from okfprofile.supply_cli import licences_main

if __name__ == "__main__":
    raise SystemExit(licences_main())
