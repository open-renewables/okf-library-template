"""The marker and secret scanner and its command line (plan step 3, NFR6)."""

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from okfprofile import supply_cli
from okfprofile.scanner import ScanConfigError, load_scan_config, scan_files, scan_text
from okfprofile.supply_cli import scan_main
from support import ROOT

# Secret-shaped strings are built at run time so that no literal in this file looks like a secret to a scanner.
GITHUB_TOKEN = "ghp_" + "A1" * 18
AWS_KEY = "AKIA" + "B2" * 8
PEM = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"
SLACK = "xoxb-" + "1234567890" + "abcdef"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A scratch tree holding this repository's scan rules and their schema."""
    for name in ("profile/scan.yaml", "profile/schemas/scan.schema.json"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, tmp_path / name)
    return tmp_path


def write(root: Path, name: str, text: str) -> None:
    file = root / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding="utf-8", newline="\n")


def test_the_shipped_rules_load() -> None:
    config = load_scan_config(ROOT)
    assert {r.id for r in config.rules} >= {"confidentiality-marker", "private-key-block", "github-token"}
    assert "profile/scan.yaml" in config.exclude


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("This is CONFIDENTIAL material", "confidentiality-marker"),
        ("INTERNAL USE ONLY", "confidentiality-marker"),
        (f"token = {GITHUB_TOKEN}", "github-token"),
        (f"key: {AWS_KEY}", "aws-access-key-id"),
        (PEM, "private-key-block"),
        (f"hook {SLACK}", "slack-token"),
    ],
)
def test_each_rule_finds_its_planted_string(text: str, rule: str) -> None:
    findings = scan_text(load_scan_config(ROOT), "first line\n" + text + "\n", "a.txt")
    assert [(f.rule, f.line) for f in findings] == [(rule, 2)]


def test_secrets_are_redacted_and_markers_are_not() -> None:
    config = load_scan_config(ROOT)
    secret = scan_text(config, GITHUB_TOKEN, "a.txt")[0]
    marker = scan_text(config, "CONFIDENTIAL", "a.txt")[0]
    assert secret.excerpt == "ghp_***"
    assert GITHUB_TOKEN not in secret.human()
    assert marker.excerpt == "CONFIDENTIAL"


@pytest.mark.parametrize("text", ["confidential in lower case", "ghp_short", "AKIA too short", "plain text"])
def test_clean_text_has_no_finding(text: str) -> None:
    assert scan_text(load_scan_config(ROOT), text, "a.txt") == []


def test_scan_files_counts_what_it_skips(root: Path) -> None:
    config = load_scan_config(root)
    write(root, "bad.md", "CONFIDENTIAL\n")
    write(root, "ok.md", "fine\n")
    (root / "blob.bin").write_bytes(b"CONFIDENTIAL\0")
    (root / "big.txt").write_text("CONFIDENTIAL" * 200_000, encoding="utf-8")
    result = scan_files(config, root, ["bad.md", "ok.md", "blob.bin", "big.txt", "profile/scan.yaml", "missing.md"])
    assert [(f.file, f.line) for f in result.findings] == [("bad.md", 1)]
    assert (result.scanned, result.excluded, result.skipped_binary, result.skipped_large) == (2, 1, 1, 1)
    assert not result.ok
    assert json.loads(result.to_json())["findings"][0]["rule"] == "confidentiality-marker"


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda t: t.replace("kind: marker", "kind: other"), "kind"),
        (lambda t: t.replace("version: 1", "version: 2"), "version"),
        (lambda t: t.replace(r"'\b(CONFIDENTIAL", "'(CONFIDENTIAL"), None),
        (lambda t: t.replace("id: private-key-block", "id: confidentiality-marker"), "unique"),
        (lambda t: t.replace("'-----BEGIN [A-Z ]*PRIVATE KEY-----'", "'[unclosed'"), "does not compile"),
        (lambda t: t + "extra: true\n", "extra"),
    ],
)
def test_invalid_rules_are_refused(root: Path, edit: Callable[[str], str], message: str | None) -> None:
    path = root / "profile" / "scan.yaml"
    path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")  # type: ignore[operator]
    if message is None:
        load_scan_config(root)
    else:
        with pytest.raises(ScanConfigError, match=message):
            load_scan_config(root)


def test_missing_and_malformed_files_are_refused(root: Path) -> None:
    (root / "profile" / "scan.yaml").write_text("rules: [unclosed\n", encoding="utf-8")
    with pytest.raises(ScanConfigError, match="invalid scan rules"):
        load_scan_config(root)
    (root / "profile" / "scan.yaml").unlink()
    with pytest.raises(ScanConfigError, match="cannot read"):
        load_scan_config(root)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)  # noqa: S603, S607


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_command_line_modes(root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.org")
    git(root, "config", "user.name", "Tester")
    write(root, "clean.md", "fine\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    assert scan_main(["--root", str(root)]) == 0
    write(root, "new.md", f"line\n{GITHUB_TOKEN}\n")
    assert scan_main(["--root", str(root), "--json"]) == 1
    out = capsys.readouterr()
    assert json.loads(out.out)["findings"][0]["file"] == "new.md"
    assert GITHUB_TOKEN not in out.err
    assert scan_main(["--root", str(root), "clean.md"]) == 0
    assert scan_main(["--root", str(root), "--all"]) == 0
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "second")
    assert scan_main(["--root", str(root)]) == 0
    assert scan_main(["--root", str(root), "--all"]) == 1


def test_a_broken_configuration_is_a_usage_error(tmp_path: Path) -> None:
    assert scan_main(["--root", str(tmp_path), "x"]) == 2


def test_gitleaks_runs_only_when_installed(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write(root, "a.md", "fine\n")
    monkeypatch.setattr(supply_cli.shutil, "which", lambda _name: None)
    assert scan_main(["--root", str(root), "--gitleaks", "a.md"]) == 0
    assert "gitleaks is not installed" in capsys.readouterr().err
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(supply_cli.shutil, "which", lambda _name: "/bin/gitleaks")
    monkeypatch.setattr(supply_cli.subprocess, "run", fake_run)
    assert scan_main(["--root", str(root), "--gitleaks", "a.md"]) == 1
    assert calls == [["/bin/gitleaks", "git", "--pre-commit", "--redact", "--staged", "--verbose"]]
