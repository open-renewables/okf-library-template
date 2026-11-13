"""The site build and its six compatibility checks (P3 plan steps 4 to 6; SDD C-07, W-08; FR8.1, FR8.2; ADR-001).

The builder tests need the site groups (``uv sync --group site-mkdocs --group site-zensical``) and skip with a reason
where they are not installed; CI installs them. Zensical skips settings it does not support without a warning, so its
results are compared with a recorded expectation per check, and a release that changes one fails the test and says so.
"""

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest
from okfprofile.site import (
    MANIFEST,
    PageComparison,
    SiteError,
    build,
    built_pages,
    compare_pages,
    docs_dir,
    expected_pages,
    installed,
    should_deploy,
    site_url,
    write_manifest,
)
from okfprofile.site_cli import build_site_main, check_site_main
from support import ROOT

FIXTURE = ROOT / "tests" / "template" / "fixtures" / "site"
HAVE = {name: installed(name) for name in ("mkdocs", "zensical")}
needs = {
    name: pytest.mark.skipif(not HAVE[name], reason=f"{name} is not installed (uv sync --group site-{name})")
    for name in HAVE
}
CHECKS = (
    "1 landing pages",
    "2 relative links",
    "3 unknown keys kept",
    "4 anchors",
    "5 reserved keys",
    "6 dialect",
)
# Recorded 2026-11-12 with MkDocs 1.6.1 + Material 9.7.7 and Zensical 0.1.1 (ADR-001: judge the output, not the exit code).
EXPECTED = {
    "mkdocs": dict.fromkeys(CHECKS, True),
    "zensical": dict.fromkeys(CHECKS, True),
}


def slug(text: str) -> str:
    """GitHub's automatic anchor for a heading: lower case, spaces to hyphens, punctuation dropped."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def read(site: Path, page: str) -> str:
    return (site / page).read_text(encoding="utf-8")


def tree_digest(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        digest.update(path.relative_to(folder).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def results_of(site: Path, folder: Path, before: str) -> dict[str, bool]:
    """The six FR8.2 checks, as pass or fail, for one built fixture site."""
    alpha = read(site, "group-a/alpha/index.html")
    glossary = read(site, "glossary/index.html")
    group = read(site, "group-a/index.html")
    return {
        CHECKS[0]: compare_pages(folder, site).ok and "<h1" in group and "Group A" in group,
        CHECKS[1]: all(
            f'href="{target}"' in alpha
            for target in (
                "../beta/",
                "../../group-b/gamma/",
                "../../glossary/#term-one",
                "../../group-b/with%20space/",
            )
        ),
        CHECKS[2]: tree_digest(folder) == before and "kept and ignored" not in alpha,
        CHECKS[3]: f'id="{slug("Term one")}"' in glossary
        and 'id="second-heading"' in alpha
        and 'href="#second-heading"' in alpha,
        CHECKS[4]: (site / "group-a/alpha/index.html").is_file()
        and not (site / "custom-slug").exists()
        and "<title>Alpha" in alpha
        and "md-status--stable" in alpha
        and "group:group-a" in alpha
        and not any(":" in p.relative_to(site).as_posix() for p in site.rglob("*")),
        CHECKS[5]: "&lt;1000 V" in alpha and "{braces}" in alpha and 'id="fn:1"' in alpha and 'id="fnref:1"' in alpha,
    }


@pytest.fixture(scope="module")
def fixture_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("site-fixture") / "lib"
    shutil.copytree(FIXTURE, root, ignore=shutil.ignore_patterns("site", "site-zensical"))
    return root


@pytest.fixture(scope="module")
def built(fixture_root: Path) -> dict[str, Path]:
    before = tree_digest(fixture_root / "knowledge")
    out = {}
    for name in ("mkdocs", "zensical"):
        if HAVE[name]:
            out[name] = build(fixture_root, name)
    assert tree_digest(fixture_root / "knowledge") == before
    return out


@pytest.mark.parametrize("name", ["mkdocs", "zensical"])
def test_each_builder_gives_the_recorded_result_for_each_of_the_six_checks(
    name: str, built: dict[str, Path], fixture_root: Path
) -> None:
    if not HAVE[name]:
        pytest.skip(needs[name].kwargs["reason"])
    got = results_of(built[name], docs_dir(fixture_root), tree_digest(fixture_root / "knowledge"))
    assert got == EXPECTED[name], {k: v for k, v in got.items() if v != EXPECTED[name][k]}


def test_both_builders_give_the_same_pages(built: dict[str, Path]) -> None:
    if len(built) < 2:
        pytest.skip("both site groups are needed")
    assert built_pages(built["mkdocs"]) == built_pages(built["zensical"])


def test_a_broken_link_fails_the_strict_mkdocs_build(fixture_root: Path, tmp_path: Path) -> None:
    if not HAVE["mkdocs"]:
        pytest.skip(needs["mkdocs"].kwargs["reason"])
    broken = tmp_path / "lib"
    shutil.copytree(fixture_root, broken, ignore=shutil.ignore_patterns("site", "site-zensical"))
    page = broken / "knowledge" / "group-a" / "beta.md"
    page.write_text(page.read_text(encoding="utf-8") + "\n[nowhere](missing.md)\n", encoding="utf-8")
    with pytest.raises(SiteError, match="exited with"):
        build(broken, "mkdocs", tmp_path / "out")


def test_the_shared_configuration_needs_no_zensical_only_keys(fixture_root: Path, tmp_path: Path) -> None:
    """ADR-001's carried issue, answered: Zensical 0.1.1 reads MkDocs' ``validation`` keys, and strict MkDocs rejects
    Zensical's own top-level link keys, so one ``mkdocs.yml`` works only without them. ``theme.variant`` is tolerated."""
    if not HAVE["mkdocs"]:
        pytest.skip(needs["mkdocs"].kwargs["reason"])
    both = tmp_path / "lib"
    shutil.copytree(fixture_root, both, ignore=shutil.ignore_patterns("site", "site-zensical"))
    config = both / "mkdocs.yml"
    original = config.read_text(encoding="utf-8")
    variant = original.replace("theme:\n  name: material\n", "theme:\n  name: material\n  variant: classic\n")
    assert variant != original
    config.write_text(variant, encoding="utf-8")
    assert build(both, "mkdocs", tmp_path / "out").is_dir()
    config.write_text(original + "invalid_links: true\n", encoding="utf-8")
    with pytest.raises(SiteError, match="exited with"):
        build(both, "mkdocs", tmp_path / "out2")


def test_zensical_fails_a_strict_build_on_a_broken_link(
    fixture_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Zensical 0.1.1 reads ``strict`` and the link settings from ``mkdocs.yml``; its output still says what failed."""
    if not HAVE["zensical"]:
        pytest.skip(needs["zensical"].kwargs["reason"])
    broken = tmp_path / "lib"
    shutil.copytree(fixture_root, broken, ignore=shutil.ignore_patterns("site", "site-zensical"))
    page = broken / "knowledge" / "group-a" / "beta.md"
    page.write_text(page.read_text(encoding="utf-8") + "\n[nowhere](missing.md)\n", encoding="utf-8")
    with pytest.raises(SiteError, match="exited with"):
        build(broken, "zensical", tmp_path / "out")
    assert "page does not exist" in capsys.readouterr().err


def test_the_repository_site_builds_in_place_and_leaves_the_bundle_untouched(tmp_path: Path) -> None:
    if not HAVE["mkdocs"]:
        pytest.skip(needs["mkdocs"].kwargs["reason"])
    before = tree_digest(ROOT / "knowledge")
    out = build(ROOT, "mkdocs", tmp_path / "site")
    assert compare_pages(docs_dir(ROOT), out).ok
    assert tree_digest(ROOT / "knowledge") == before


def test_the_markdown_divergences_between_the_validator_and_the_site_are_the_recorded_ones(
    built: dict[str, Path],
) -> None:
    """G2: markdown-it-py (the validator) against Python-Markdown (the site) on constructs the profile does not use."""
    if not HAVE["mkdocs"]:
        pytest.skip(needs["mkdocs"].kwargs["reason"])
    from markdown_it import MarkdownIt
    from mdit_py_plugins.footnote import footnote_plugin

    source = (FIXTURE / "knowledge" / "group-b" / "constructs.md").read_text(encoding="utf-8").split("---\n", 2)[2]
    reference = MarkdownIt("commonmark").enable("table").use(footnote_plugin).render(source)
    site = read(built["mkdocs"], "group-b/constructs/index.html")
    divergences = {
        "list directly after a paragraph": "<li>first item</li>" in reference and "<li>first item</li>" not in site,
        "list inside a footnote definition": "<li>inner point</li>" in reference and "<li>inner point</li>" not in site,
    }
    agreements = {
        "table": "<table>" in reference and "<table>" in site,
        "inline html next to markdown": '<span class="x">HTML span</span>' in reference
        and '<span class="x">HTML span</span>' in site,
        "ordered list with nested bullet": "<li>nested bullet</li>" in reference and "<li>nested bullet</li>" in site,
        "footnote reference": "footnote" in reference and 'class="footnote-ref"' in site,
    }
    assert divergences == {"list directly after a paragraph": True, "list inside a footnote definition": True}
    assert all(agreements.values()), agreements


# Pure functions: these need no builder.


def test_expected_pages_follow_the_directory_url_rule(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    for name in ("index.md", "a/index.md", "a/b/c.md", "a/d.md", "e.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert expected_pages(tmp_path) == {"index.html", "a/index.html", "a/b/c/index.html", "a/d/index.html"}


def test_built_pages_leave_out_the_404_page_and_the_asset_folders(tmp_path: Path) -> None:
    for name in ("index.html", "404.html", "a/index.html", "assets/x.html", "search/y.html", "tags/z.html"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert built_pages(tmp_path) == {"index.html", "a/index.html"}


def test_compare_pages_names_missing_and_extra_pages(tmp_path: Path) -> None:
    folder, site = tmp_path / "k", tmp_path / "s"
    folder.mkdir()
    (folder / "a.md").write_text("x", encoding="utf-8")
    (site / "b").mkdir(parents=True)
    (site / "b" / "index.html").write_text("x", encoding="utf-8")
    result = compare_pages(folder, site)
    assert result == PageComparison(("a/index.html",), ("b/index.html",))
    assert not result.ok


def test_docs_dir_is_read_from_the_configuration(tmp_path: Path) -> None:
    with pytest.raises(SiteError, match=r"no mkdocs\.yml"):
        docs_dir(tmp_path)
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    assert docs_dir(tmp_path) == (tmp_path / "knowledge").resolve()
    (tmp_path / "mkdocs.yml").write_text("site_name: x\n", encoding="utf-8")
    assert docs_dir(tmp_path) == (tmp_path / "docs").resolve()
    (tmp_path / "mkdocs.yml").write_text("a: [unclosed\n", encoding="utf-8")
    with pytest.raises(SiteError, match="not readable"):
        docs_dir(tmp_path)


def test_the_manifest_names_the_tag_and_commit(tmp_path: Path) -> None:
    with pytest.raises(SiteError, match="not a version tag"):
        write_manifest(tmp_path, "latest", "abc")
    with pytest.raises(SiteError, match="not a built site"):
        write_manifest(tmp_path / "none", "v1.0.0", "abc")
    path = write_manifest(tmp_path, "v0.5.0", "abc123")
    assert path.name == MANIFEST
    assert json.loads(path.read_text(encoding="utf-8")) == {"tag": "v0.5.0", "commit": "abc123"}


@pytest.mark.parametrize(
    ("ref", "url", "expected"),
    [
        ("v1.0.0", "https://example.org", True),
        ("refs/tags/v2.3.4", "https://example.org", True),
        ("v1.0.0", "", False),
        ("v0.5.0", "https://example.org", False),
        ("v1.0.0-rc.1", "https://example.org", False),
        ("main", "https://example.org", False),
    ],
)
def test_only_a_stable_tag_of_a_library_with_a_site_url_deploys(
    tmp_path: Path, ref: str, url: str, expected: bool
) -> None:
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "profile.yaml").write_text(f'library:\n  site_url: "{url}"\n', encoding="utf-8")
    assert should_deploy(tmp_path, ref) is expected


def test_no_profile_means_no_site_url(tmp_path: Path) -> None:
    assert site_url(tmp_path) == ""
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / "profile.yaml").write_text("library: [unclosed\n", encoding="utf-8")
    assert site_url(tmp_path) == ""
    (tmp_path / "profile" / "profile.yaml").write_text("library: x\n", encoding="utf-8")
    assert site_url(tmp_path) == ""


def test_the_template_has_no_site_url_so_it_never_deploys() -> None:
    assert site_url(ROOT) == ""
    assert not should_deploy(ROOT, "v1.0.0")


def test_unknown_builders_and_missing_installs_are_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SiteError, match="unknown builder"):
        build(tmp_path, "hugo")
    monkeypatch.setattr("okfprofile.site.installed", lambda _name: False)
    with pytest.raises(SiteError, match="uv sync --group site-mkdocs"):
        build(tmp_path, "mkdocs")


def test_a_build_without_a_configuration_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("okfprofile.site.installed", lambda _name: True)
    with pytest.raises(SiteError, match=r"no mkdocs\.yml"):
        build(tmp_path, "mkdocs")


# The command line.


def test_build_site_cli_reports_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert build_site_main(["mkdocs", "--root", str(tmp_path)]) in (2,)
    assert "error:" in capsys.readouterr().err


def test_check_site_cli_compares_and_writes_the_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "knowledge" / "a.md").write_text("x", encoding="utf-8")
    site = tmp_path / "site"
    (site / "a").mkdir(parents=True)
    (site / "a" / "index.html").write_text("x", encoding="utf-8")
    assert check_site_main(["--root", str(tmp_path), "--manifest", "v0.5.0", "--commit", "abc", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert json.loads((site / MANIFEST).read_text(encoding="utf-8"))["tag"] == "v0.5.0"
    (site / "a" / "index.html").unlink()
    assert check_site_main(["--root", str(tmp_path)]) == 1
    assert "missing page a/index.html" in capsys.readouterr().err


def test_check_site_cli_compares_two_builds(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "knowledge" / "a.md").write_text("x", encoding="utf-8")
    for name in ("site", "other"):
        (tmp_path / name / "a").mkdir(parents=True)
        (tmp_path / name / "a" / "index.html").write_text("x", encoding="utf-8")
    assert check_site_main(["--root", str(tmp_path), "--against", str(tmp_path / "other")]) == 0
    (tmp_path / "other" / "a" / "index.html").unlink()
    assert check_site_main(["--root", str(tmp_path), "--against", str(tmp_path / "other")]) == 1
    assert "that site has" in capsys.readouterr().err


def test_check_site_cli_needs_a_built_site_and_a_configuration(tmp_path: Path) -> None:
    assert check_site_main(["--root", str(tmp_path)]) == 2
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    assert check_site_main(["--root", str(tmp_path)]) == 2


def test_check_site_cli_answers_the_deploy_question(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert check_site_main(["--root", str(tmp_path), "--deploy-ref", "v1.0.0"]) == 0
    assert capsys.readouterr().out.strip() == "false"


def test_the_link_check_is_skipped_with_a_notice_without_lychee(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("okfprofile.site_cli.shutil.which", lambda _name: None)
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "site").mkdir()
    assert check_site_main(["--root", str(tmp_path), "--linkcheck"]) == 0
    assert "lychee is not installed" in capsys.readouterr().err


def test_the_link_check_fails_the_run_when_lychee_does(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Done:
        returncode = 2

    monkeypatch.setattr("okfprofile.site_cli.shutil.which", lambda _name: "lychee")
    monkeypatch.setattr("okfprofile.site_cli.subprocess.run", lambda *_a, **_k: Done())
    (tmp_path / "mkdocs.yml").write_text("docs_dir: knowledge\n", encoding="utf-8")
    (tmp_path / "knowledge").mkdir()
    (tmp_path / "site").mkdir()
    assert check_site_main(["--root", str(tmp_path), "--linkcheck"]) == 1
