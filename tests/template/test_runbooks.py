"""The runbooks name only commands, tasks, flags and files that exist (P2 plan step 15)."""

import re
import subprocess
import sys
import tomllib
from functools import cache
from pathlib import Path

import pytest
from support import ROOT

RUNBOOKS = sorted((ROOT / "docs" / "development" / "operations").glob("runbook-*.md"))
CODE = re.compile(r"```[a-z]*\n(.*?)```|`([^`\n]+)`", re.DOTALL)
SCRIPT = re.compile(r"scripts/([a-z_]+)\.py")
TASK = re.compile(r"uv run poe ([a-z][a-z-]*)")
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z-]*)")


def code_of(path: Path) -> list[str]:
    """Every code span and block of a runbook, with shell line continuations joined."""
    text = path.read_text(encoding="utf-8")
    return [(m[1] or m[2]).replace("\\\n", " ") for m in CODE.finditer(text)]


@cache
def tasks() -> set[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return set(data["tool"]["poe"]["tasks"])


@cache
def help_of(script: str) -> str:
    done = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts" / f"{script}.py"), "--help"],
        capture_output=True,
        check=False,
        cwd=ROOT,
        text=True,
    )
    return done.stdout


def test_there_are_runbooks_for_every_procedure() -> None:
    names = {path.name for path in RUNBOOKS}
    assert {
        "runbook-create-template-repository.md",
        "runbook-promote-to-public.md",
        "runbook-move-git-local-to-platform.md",
        "runbook-revision-writer-recovery.md",
        "runbook-remove-leaked-content.md",
        "runbook-instantiate-library.md",
    } <= names


@pytest.mark.parametrize("path", RUNBOOKS, ids=lambda p: p.name)
def test_every_poe_task_a_runbook_names_exists(path: Path) -> None:
    named = {m[1] for snippet in code_of(path) for m in TASK.finditer(snippet)}
    assert named <= tasks(), sorted(named - tasks())


@pytest.mark.parametrize("path", RUNBOOKS, ids=lambda p: p.name)
def test_every_script_and_flag_a_runbook_names_exists(path: Path) -> None:
    problems = []
    for snippet in code_of(path):
        for line in snippet.splitlines():
            for script in {m[1] for m in SCRIPT.finditer(line)}:
                if not (ROOT / "scripts" / f"{script}.py").is_file():
                    problems.append(f"no scripts/{script}.py")
                    continue
                for flag in set(FLAG.findall(line)):
                    if flag not in help_of(script) and flag != "--help":
                        problems.append(f"scripts/{script}.py has no {flag}")
    assert not problems, problems


@pytest.mark.parametrize("path", RUNBOOKS, ids=lambda p: p.name)
def test_every_runbook_a_runbook_names_exists(path: Path) -> None:
    named = set(re.findall(r"runbook-[a-z0-9-]+\.md", path.read_text(encoding="utf-8")))
    assert {name for name in named if not (path.parent / name).is_file()} == set()
