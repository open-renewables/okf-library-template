"""Thin command-line wrapper over okfprofile.supply_cli (SDD C-04)."""

from okfprofile.supply_cli import audit_main

if __name__ == "__main__":
    raise SystemExit(audit_main())
