"""Directory owners from a CODEOWNERS file, with GitHub's last-match-wins rule (SDD C-03, I-15, FR5.4).

Ownership is assessed per file: each concept path gets the owners of the last pattern that matches it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LOCATIONS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")


@dataclass(frozen=True)
class OwnerRule:
    """One CODEOWNERS line.

    Attributes:
        pattern: The pattern as written.
        owners: The owners named on the line (``@user``, ``@org/team`` or an e-mail address).
        regex: The pattern compiled to match a repository-relative path.
    """

    pattern: str
    owners: tuple[str, ...]
    regex: re.Pattern[str]


def _translate(body: str) -> str:
    regex = ""
    index = 0
    while index < len(body):
        if body.startswith("**/", index):
            regex += "(?:.*/)?"
            index += 3
        elif body.startswith("/**", index) and index + 3 == len(body):
            regex += "/.*"
            index += 3
        elif body.startswith("**", index):
            regex += ".*"
            index += 2
        elif body[index] == "*":
            regex += "[^/]*"
            index += 1
        elif body[index] == "?":
            regex += "[^/]"
            index += 1
        else:
            regex += re.escape(body[index])
            index += 1
    return regex


def pattern_regex(pattern: str) -> re.Pattern[str]:
    """Compile a CODEOWNERS pattern: anchored if it starts with ``/`` or has a ``/`` inside, else matched at any depth.

    A pattern matches a file or folder of that name and everything beneath it.
    """
    stripped = pattern.rstrip("/")
    anchored = stripped.startswith("/") or "/" in stripped
    body = _translate(stripped.lstrip("/"))
    prefix = "^" if anchored else "^(?:.*/)?"
    return re.compile(f"{prefix}{body}(?:/.*)?$")


@dataclass
class CodeOwners:
    """The rules of a CODEOWNERS file, in file order.

    Attributes:
        rules: The rules; the last one that matches a path decides its owners.
    """

    rules: list[OwnerRule] = field(default_factory=list)

    def owners_for(self, path: str) -> tuple[str, ...]:
        """Owners of a repository-relative path (forward slashes); empty if no rule matches or the last has none."""
        clean = path.replace("\\", "/").removeprefix("./")
        for rule in reversed(self.rules):
            if rule.regex.match(clean):
                return rule.owners
        return ()

    def is_owner(self, login: str, path: str) -> bool:
        """True if ``login`` (a user name, case-insensitive) is named as an owner of the path.

        Teams are not expanded: a team owner matches only if ``login`` is written ``org/team``.
        """
        wanted = login.lower().removeprefix("@")
        return any(owner.lower().removeprefix("@") == wanted for owner in self.owners_for(path))


def parse_codeowners(text: str) -> CodeOwners:
    """Parse CODEOWNERS text; comments and blank lines are skipped."""
    rules = []
    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        pattern, *owners = line.split()
        rules.append(OwnerRule(pattern, tuple(owners), pattern_regex(pattern)))
    return CodeOwners(rules)


def load_codeowners(root: Path) -> CodeOwners:
    """Load the first CODEOWNERS file found in the usual places; no file means no owners."""
    for location in LOCATIONS:
        file = root / location
        if file.is_file():
            return parse_codeowners(file.read_text(encoding="utf-8"))
    return CodeOwners()
