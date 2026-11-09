"""The revision writer: record every merged change in the *Revision history* of the concepts it touched.

SDD W-05, I-08, AD-11, AD-12. The writer works from the commits on the main branch after the last revision-writer
commit (catch-up), so a dropped or failed run loses nothing. Approval is inferred, never waited for: a single
maintainer cannot approve their own pull request, so a merge by the author is recorded as ``self-approved``.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass, field
from pathlib import Path

from okfprofile.bundle import RESERVED_NAMES, load_bundle
from okfprofile.codeowners import CodeOwners
from okfprofile.config import Profile
from okfprofile.document import parse_concept
from okfprofile.gitutil import git
from okfprofile.history import history_heading, history_lines
from okfprofile.indexes import write_indexes
from okfprofile.platforms import MergedChange, MergeReview, PlatformAdapter, normalise_login
from okfprofile.platforms.commits import BOT_TRAILER, commits_after, last_revision_bot_commit
from okfprofile.report import Finding
from okfprofile.revision import (
    SEPARATOR,
    RevisionLine,
    Tier,
    concept_tier,
    owner_approved,
    parse_revision_line,
    window_start,
)

CI_MARKER = "<!--"
BOT_ACTOR = "process:revision-bot"
APPROVED, CHANGES_REQUESTED, DISMISSED = "APPROVED", "CHANGES_REQUESTED", "DISMISSED"
DECISIONS = frozenset({APPROVED, CHANGES_REQUESTED, DISMISSED})
COMMIT_MESSAGE = f"Record revision history\n\n{BOT_TRAILER}\n"


class RevisionError(Exception):
    """A revision line could not be built or placed."""


@dataclass(frozen=True)
class Outcome:
    """The approval recorded for one concept, and whether it counts for ``full-review``.

    Attributes:
        text: The approval part of the line, for example ``approved @alice (owner)``.
        counts_for_full_review: True for a current owner approval or an owner's self-approval.
    """

    text: str
    counts_for_full_review: bool


def infer_approval(change: MergedChange, concept_path: str, owners: CodeOwners) -> Outcome:
    """Infer the approval outcome of a change for one concept (W-05, steps 1 to 6).

    Args:
        change: The merged change.
        concept_path: Repository-relative path of the concept; ownership is assessed per file (FR5.4).
        owners: The CODEOWNERS rules.

    Returns:
        The outcome. The latest decision of each reviewer counts; the author's own review does not.
    """
    latest = {}
    for review in change.reviews:
        if review.state in DECISIONS:
            latest[review.login] = review
    approvers = sorted(
        (r for r in latest.values() if r.state == APPROVED and r.login != change.author),
        key=lambda r: r.submitted_at,
        reverse=True,
    )
    current = [r for r in approvers if r.commit_id == change.head_sha]
    stale = [r for r in approvers if r.commit_id != change.head_sha]

    def owned(group: list[MergeReview]) -> list[MergeReview]:
        return [r for r in group if owners.is_owner(r.login, concept_path)]

    if owned(current):
        return Outcome(f"approved @{owned(current)[0].login} (owner)", True)
    if owned(stale):
        return Outcome(f"approved (stale) @{owned(stale)[0].login} (owner)", False)
    if current:
        return Outcome(f"approved @{current[0].login} (non-owner)", False)
    if stale:
        return Outcome(f"approved (stale) @{stale[0].login} (non-owner)", False)
    if change.merged_by == change.author:
        is_owner = owners.is_owner(change.author, concept_path)
        return Outcome(f"self-approved ({'owner' if is_owner else 'non-owner'})", is_owner)
    return Outcome(f"merged without approval @{change.merged_by}", False)


def build_line(profile: Profile, change: MergedChange, concept_path: str, owners: CodeOwners) -> str:
    """The revision line (without the list marker) for one concept.

    Args:
        profile: The loaded profile (label names).
        change: The merged change.
        concept_path: Repository-relative path of the concept.
        owners: The CODEOWNERS rules.

    Returns:
        A line that parses with ``parse_revision_line``.

    Raises:
        RevisionError: If the line does not follow the I-08 grammar (for example an unusable login).
    """
    outcome = infer_approval(change, concept_path, owners)
    parts = [
        change.commit.day.isoformat(),
        f"author @{normalise_login(change.author)}",
        outcome.text,
        change.reference,
    ]
    if profile.rules.full_review_label in change.labels and outcome.counts_for_full_review:
        parts.append("full-review")
    if profile.rules.agent_label in change.labels:
        parts.append("agent-drafted")
    line = SEPARATOR.join(parts)
    if parse_revision_line(line) is None:
        msg = f"revision line does not follow the grammar: {line}"
        raise RevisionError(msg)
    return line


def insert_line(text: str, heading: str, line: str) -> str:
    """Insert a revision line at the end of the CI-managed section, before footnote definitions.

    The new item goes after the last existing item; in an empty section it goes after the CI comment (or the
    heading), separated by a blank line. Line endings of the file are kept.

    Args:
        text: The concept file.
        heading: Heading of the managed section.
        line: Revision line without the list marker.

    Returns:
        The new text.

    Raises:
        RevisionError: If the section is missing.
    """
    concept = parse_concept(text)
    section = concept.section(heading)
    if section is None:
        msg = f"no '{heading}' section"
        raise RevisionError(msg)
    cr = "\r" if "\r\n" in text else ""
    rows = text.split("\n")
    if section.items:
        at = section.items[-1].line
        new = [f"- {line}{cr}"]
    else:
        inside = range(section.heading.line, section.end_line + 1)
        comment = next((n for n in inside if CI_MARKER in rows[n - 1]), None)
        at = comment if comment is not None else section.heading.line
        new = [cr, f"- {line}{cr}"]
    return "\n".join([*rows[:at], *new, *rows[at:]])


def verified_entries(profile: Profile, lines: list[RevisionLine]) -> list[tuple[str, str]]:
    """The OKF ``verified`` entries that make a generic tool derive the same tier as the library (I-08).

    Human-reviewed: one ``human:<login>`` entry per owner approval or owner self-approval since the latest
    owner-approved full review. Machine-confirmed: one ``process:revision-bot`` entry at the latest revision.
    Unverified: none. The time of an entry is its revision date at 00:00 UTC, because a line records the date only.
    """
    tier = concept_tier(lines, profile.rules.require_non_author_approver).tier
    if tier is Tier.UNVERIFIED:
        return []
    if tier is Tier.MACHINE_CONFIRMED:
        return [(BOT_ACTOR, f"{lines[-1].date.isoformat()}T00:00:00Z")]
    entries = []
    for line in lines[window_start(lines) :]:
        if owner_approved(line):
            actor = f"human:{line.approver or line.author}"
            entries.append((actor, f"{line.date.isoformat()}T00:00:00Z"))
    return list(dict.fromkeys(entries))


def set_verified(text: str, entries: list[tuple[str, str]]) -> str:
    """Replace the ``verified`` key of the frontmatter with ``entries`` (removed if empty).

    Args:
        text: The concept file.
        entries: ``(by, at)`` pairs.

    Returns:
        The new text; unchanged if the key already holds exactly these entries.
    """
    cr = "\r" if "\r\n" in text else ""
    rows = text.split("\n")
    if not rows or rows[0].rstrip("\r") != "---":
        return text
    end = next((i for i in range(1, len(rows)) if rows[i].rstrip("\r") == "---"), None)
    if end is None:
        return text
    start = next((i for i in range(1, end) if rows[i].startswith("verified:")), None)
    stop = start
    if start is not None:
        stop = start + 1
        while stop < end and rows[stop].startswith((" ", "\t", "-")):
            stop += 1
    block = [f"verified:{cr}"] if entries else []
    for by, at in entries:
        block += [f"  - by: {by}{cr}", f"    at: {at}{cr}"]
    if start is None:
        return "\n".join([*rows[:end], *block, *rows[end:]])
    return "\n".join([*rows[:start], *block, *rows[stop:]])


@dataclass
class WriteResult:
    """What a run changed.

    Attributes:
        lines: ``(concept path, line)`` for each line added, in order.
        files: Repository-relative paths written, including indexes.
        already_present: Changes skipped because the concept already records them.
        changes: Merged changes processed.
    """

    lines: list[tuple[str, str]] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    already_present: int = 0
    changes: int = 0


def _eligible(profile: Profile, root: Path, relative: str) -> tuple[str, str] | None:
    """(file text, managed heading) if ``relative`` is a concept of the bundle with a managed section."""
    bundle = profile.bundle_root.relative_to(root).as_posix().rstrip("/") + "/"
    if (
        not relative.startswith(bundle)
        or not relative.endswith(".md")
        or posixpath.basename(relative) in RESERVED_NAMES
    ):
        return None
    file = root / relative
    if not file.is_file():
        return None
    text = file.read_bytes().decode("utf-8")
    concept = parse_concept(text, relative)
    heading = history_heading(profile, str((concept.frontmatter or {}).get("type")))
    if heading is None or concept.section(heading) is None:
        return None
    return text, heading


def _records(lines: list[RevisionLine], change: MergedChange) -> bool:
    for line in lines:
        if change.kind == "pr" and line.change == "pr" and line.reference == str(change.number):
            return True
        if change.kind == "commit" and line.change == "commit" and line.reference == change.commit.short:
            return True
        if change.kind == "pr-none" and line.change == "pr-none" and line.date == change.commit.day:
            return True
    return False


def _flush(profile: Profile, texts: dict[str, str], result: WriteResult, dry_run: bool) -> None:
    """Write the changed concept files, refresh ``verified`` where enabled, then the indexes of their folders."""
    root = profile.root
    written = []
    for relative, text in texts.items():
        if profile.rules.write_okf_verified:
            concept = parse_concept(text, relative)
            text = set_verified(text, verified_entries(profile, history_lines(profile, concept)))
        if text != (root / relative).read_bytes().decode("utf-8"):
            written.append(relative)
            if not dry_run:
                (root / relative).write_bytes(text.encode("utf-8"))
    result.files.extend(written)
    if written and not dry_run:
        bundle = profile.bundle_root.relative_to(root).as_posix()
        folders = {posixpath.dirname(posixpath.relpath(p, bundle)) for p in written}
        for index in write_indexes(profile, load_bundle(profile.bundle_root, root), only_folders=folders):
            result.files.append(index.relative_to(root).as_posix())


def record_changes(
    profile: Profile, changes: list[MergedChange], owners: CodeOwners, dry_run: bool = False
) -> WriteResult:
    """Append a revision line to each concept each change touched, then refresh ``verified`` and the indexes.

    Args:
        profile: The loaded profile.
        changes: Merged changes, oldest first.
        owners: The CODEOWNERS rules.
        dry_run: Compute the result without writing any file.

    Returns:
        What was (or would be) written. A concept that already records a change is left alone, so running twice
        is a no-op.

    Raises:
        RevisionError: If a line cannot be built or placed.
    """
    texts: dict[str, str] = {}
    result = WriteResult(changes=len(changes))
    for change in changes:
        for relative in change.commit.files:
            if relative not in texts:
                found = _eligible(profile, profile.root, relative)
                if found is None:
                    continue
                texts[relative] = found[0]
            concept = parse_concept(texts[relative], relative)
            if _records(history_lines(profile, concept), change):
                result.already_present += 1
                continue
            heading = history_heading(profile, str((concept.frontmatter or {}).get("type"))) or ""
            line = build_line(profile, change, relative, owners)
            texts[relative] = insert_line(texts[relative], heading, line)
            result.lines.append((relative, line))
    _flush(profile, texts, result, dry_run)
    return result


def catch_up(
    profile: Profile,
    adapter: PlatformAdapter,
    owners: CodeOwners,
    ref: str = "HEAD",
    since: str | None = None,
    dry_run: bool = False,
) -> WriteResult:
    """Record every change on ``ref`` since the last revision-writer commit (or ``since``).

    Args:
        profile: The loaded profile.
        adapter: A ``PlatformAdapter``.
        owners: The CODEOWNERS rules.
        ref: Tip of the history to read.
        since: Start after this commit instead of the last revision-writer commit.
        dry_run: Do not write.

    Returns:
        The result.
    """
    root = profile.root
    base = since if since is not None else last_revision_bot_commit(root, ref)
    changes = []
    for commit in commits_after(root, base, ref):
        if commit.is_revision_bot or not any(_eligible(profile, root, f) for f in commit.files):
            continue
        changes.append(adapter.resolve(commit))
    return record_changes(profile, changes, owners, dry_run)


def check_since(profile: Profile, adapter: PlatformAdapter, base: str | None, ref: str = "HEAD") -> list[Finding]:
    """Report merged changes after ``base`` whose concepts lack a revision line (SRS FR7.4, ``OKF901``).

    Args:
        profile: The loaded profile.
        adapter: A ``PlatformAdapter``.
        base: A tag or commit; changes after it are checked. None checks the whole history (a first release).
        ref: Tip of the history.

    Returns:
        One ``OKF901`` per concept and change without a line.
    """
    root = profile.root
    findings = []
    for commit in commits_after(root, base, ref):
        if commit.is_revision_bot:
            continue
        eligible = [(f, found) for f in commit.files if (found := _eligible(profile, root, f)) is not None]
        if not eligible:
            continue
        change = adapter.resolve(commit)
        for relative, (text, heading) in eligible:
            concept = parse_concept(text, relative)
            if _records(history_lines(profile, concept), change):
                continue
            section = concept.section(heading)
            where = section.heading.line if section else 0
            message = f"merged change {change.reference} ({commit.short}) has no revision line"
            findings.append(Finding.make("OKF901", relative, where, message))
    return findings


def commit_revision(root: Path, paths: list[str]) -> bool:
    """Commit the given files with the ``Revision-Bot: true`` trailer.

    Args:
        root: Repository root.
        paths: Repository-relative files to add.

    Returns:
        True if a commit was made; False if there was nothing to commit.

    Raises:
        GitError: If git fails (for example no identity is configured).
    """
    if not paths:
        return False
    git(root, "add", "--", *paths)
    if not git(root, "diff", "--cached", "--name-only").strip():
        return False
    git(root, "commit", "-q", "-m", COMMIT_MESSAGE)
    return True


def clear_history(text: str, heading: str) -> str:
    """Remove every revision line of the managed section, keeping the heading and the CI comment.

    Args:
        text: The concept file.
        heading: Heading of the managed section.

    Returns:
        The new text; unchanged if the section holds no lines.
    """
    section = parse_concept(text).section(heading)
    if section is None or not section.items:
        return text
    drop = {item.line for item in section.items}
    rows = text.split("\n")
    return "\n".join(row for number, row in enumerate(rows, start=1) if number not in drop)


def reset_history(profile: Profile, root: Path) -> list[str]:
    """Clear the revision history of every concept in the bundle.

    A library created from the template starts its own history: the example concepts must not carry the template's
    lines, which name the template's authors and pull requests.

    Args:
        profile: The loaded profile.
        root: Repository root.

    Returns:
        The repository-relative files that changed.
    """
    changed: list[str] = []
    for path in sorted(profile.bundle_root.rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        found = _eligible(profile, root, relative)
        if found is None:
            continue
        text, heading = found
        new = clear_history(text, heading)
        if new != text:
            path.write_bytes(new.encode("utf-8"))
            changed.append(relative)
    return changed
