# Governance

How this library is run: who decides, what review a concept needs, how changes arrive and how releases are made. The tools enforce what they can (`uv run poe check`); this file states the rest.

## Roles

- **Maintainers** own the profile (`profile/`), the tooling (`scripts/`), CI (`.github/`) and releases. The maintainer is {maintainer}.
- **Directory owners** are named for a folder of `knowledge/` in `.github/CODEOWNERS`. They review and approve concepts in their folders. Ownership is assessed per concept file.
- **Contributors** propose changes through an issue form or a pull request. They need no write access.

While there is one maintainer, that person is also the owner of every folder.

## Review and what `stable` means

A new concept is `draft`. A human directory owner makes it `stable`. A concept is `stable` only when all of these hold:

- it is written in the contributor's own words, with at least one source cited in its body (a footnote or an external link);
- one human directory owner of that concept has approved the change;
- every internal link and anchor resolves, and every declared section is present.

An approval counts when it was given on the commit that merged. An approval given on an earlier commit is recorded as stale and does not count.

**Self-approval.** GitHub does not let an author approve their own pull request, so a single maintainer's merge of their own change is recorded as `self-approved`. It counts as the one approval, and the concept's trust tier is shown as `human-reviewed (self)`. When a second directory owner joins, set `rules.require_non_author_approver: true` in `profile/profile.yaml` (a profile change, recorded in `DECISIONS.md`); from then on a self-approved revision is Machine-confirmed.

**Agent-drafted work.** Content drafted by an agent is labelled `agent-drafted` (or carries the commit trailer `Agent-Drafted: yes` with `platform: git-local`) and never becomes Human-reviewed on a one-line fix. A concept regains the Human-reviewed tier only through a revision labelled `full-review` that an owner approves: that label states that the whole concept was reviewed, not only the change.

## Contributing

| Route | Use it for |
| --- | --- |
| Issue forms (new concept, correction, feedback) | People who do not use git. A maintainer or an agent turns an accepted issue into a pull request |
| Pull request | Everyone else. Create a concept with `uv run python scripts/new_concept.py <Type> <path>`; never copy a file and edit its `uid` |

Labels the pull request template asks for: `agent-drafted`, `full-review`, `approved-move` (a concept moves path; the registry records the old one) and `profile-migration` (a profile change that must update concepts in the same pull request). A change to `scripts/`, `profile/`, `.github/` or `docs/` is a separate pull request from a change to `knowledge/`, unless it carries `profile-migration`.

Tag values come from the vocabulary concepts in `knowledge/vocab/`. Adding a value is a reviewed change.

## Decisions

Changes to the profile or the structure are recorded in `DECISIONS.md` before or with the change: the date, the decision and the reason. A decision is never deleted; a later row supersedes it.

## Releases

Releases are semantic-version tags (`vX.Y.Z`) on `main`. A release fails while any merged change lacks its revision-history line. Each release carries an archive, its SHA-256 and a manifest; cite a concept as `<uid>@<tag>`.

- **Minor** (`X.Y.0`): concepts added or revised.
- **Patch**: corrections that change no meaning.
- **Major** (`X.0.0`): a breaking profile change: a renamed declared heading, a removed field, value or type, any `profile-migration` change since the previous release, or a wider `uid` sequence.

Release notes are published with each release.

## Staleness, deprecation and deletion

A concept is stale at the earlier of its `stale_after` instant and the profile's default interval (two years) after its last revision. The weekly stale report lists them; an owner re-reviews or deprecates.

Concepts are never deleted. A concept leaves use by `status: deprecated`, keeps its `uid` and its path, and says what replaces it. `uid` numbers are never reused.

## Reporting a security problem

Do not open a public issue for a secret, a leaked file or a vulnerability. Write to {contact}, or use the repository's private vulnerability reporting where the platform offers it. Say what you found and where; you will get an answer from the maintainer.
