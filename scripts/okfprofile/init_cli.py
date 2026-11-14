"""Command-line entry point for ``init_library.py`` (SDD C-04, W-01 step 3).

Exit codes follow ``okfprofile.cli``: 0 success, 2 when the answers are invalid or the folder is not a template copy.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from okfprofile.config import ProfileError
from okfprofile.instantiate import (
    CODE_LICENCES,
    CONTENT_LICENCES,
    PLATFORMS,
    Answers,
    InitError,
    instantiate,
    leftover_markers,
    load_answers,
    parse_answers,
)
from okfprofile.registry import RegistryError

EXIT_OK = 0
EXIT_USAGE = 2
Ask = Callable[[str], str]


def questionnaire(ask: Ask) -> Answers:
    """Ask the questions of W-01 step 3 on the terminal.

    Args:
        ask: Called with a prompt, returns the reply (``input`` by default).

    Returns:
        The validated answers.

    Raises:
        InitError: If the replies are invalid.
    """

    def put(prompt: str, default: str = "") -> str:
        reply = ask(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
        return reply or default

    def yes(prompt: str, default: bool) -> bool:
        return put(f"{prompt} (yes/no)", "yes" if default else "no").lower() in {"y", "yes", "true"}

    data: dict[str, Any] = {
        "platform": put(f"Platform ({' or '.join(PLATFORMS)})", "github"),
        "name": put("Library name (lower case, hyphens)"),
    }
    data["title"] = put("Title", str(data["name"]).replace("-", " ").title())
    data["description"] = put("One-sentence description")
    data["maintainer"] = {
        "login": put("Maintainer's platform login"),
        "name": put("Maintainer's name"),
        "email": put("Maintainer's email address"),
    }
    data["licence_holder"] = put("Copyright holder (default: the maintainer)")
    data["content_licence"] = put(f"Content licence ({', '.join(CONTENT_LICENCES)})", "CC-BY-4.0")
    data["code_licence"] = put(f"Licence for your own code and changes ({', '.join(CODE_LICENCES)})", "Apache-2.0")
    if data["platform"] == "github":
        data["repository"] = put("Repository URL (for example https://github.com/org/name)")
    data["site_generator"] = put("Site generator (mkdocs or zensical)", "mkdocs")
    data["keep_examples"] = yes("Keep the example concept?", True)
    data["keep_tests"] = yes("Keep the template's own tests?", False)
    return parse_answers(data)


def init_library_main(argv: Sequence[str] | None = None, ask: Ask = input) -> int:
    """``init_library.py``: personalise a copy of the template."""
    parser = argparse.ArgumentParser(prog="init_library.py", description="Turn a copy of the template into a library.")
    parser.add_argument("--root", default=".", help="the copy's root folder (default: the current folder)")
    parser.add_argument("--answers", metavar="FILE", help="read the answers from a YAML file instead of asking")
    parser.add_argument("--json", action="store_true", help="write the result as JSON to standard output")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        answers = load_answers(Path(args.answers)) if args.answers else questionnaire(ask)
        result = instantiate(root, answers)
        leftovers = leftover_markers(root)
    except InitError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        return EXIT_USAGE
    except (ProfileError, RegistryError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    for relative in result.changed:
        print(f"wrote {relative}", file=sys.stderr)
    for relative in result.removed:
        print(f"removed {relative}", file=sys.stderr)
    for leftover in leftovers:
        print(f"warning: template name left in {leftover}", file=sys.stderr)
    if args.json:
        print(json.dumps({"changed": result.changed, "removed": result.removed, "leftovers": leftovers}, indent=2))
    return EXIT_OK
