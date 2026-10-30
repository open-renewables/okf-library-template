# ADR-002: Provider-neutral skills

**Status:** Accepted (owner, 2026-10-30). **Supersedes:** AD-16. **RFC:** none.

## Context

AD-16 placed agent skills in `.agents/skills/` and added `.claude/skills/<name>` symlinks so that Claude Code discovers them. V-09 (2026-10-27): the symlinks survive git, GitHub source archives and Linux, macOS and hosted Windows checkouts, but a checkout with `core.symlinks=false` turns them into text files and Claude Code then does not list the skill; a plain copy and a directory junction work. The owner's starting principle (2026-10-30) is that the repository is AI-provider agnostic; SRS NFR2 and FR7.1 already point that way.

## Decision

The committed layout is provider-neutral. `AGENTS.md` is the single agent entry point and names the skills; skills live only in `.agents/skills/` in the Agent Skills format with the six specification frontmatter fields. No `.claude/` directory and no provider-specific file is part of the template or of a library, except the template-only `CLAUDE.md`, which `init_library.py` removes. Provider-specific discovery (for example Claude Code's `.claude/skills/`) is an optional adapter: documented in the README, created by one command or task in the user's own checkout, and not committed.

## Consequences

- AD-16 is superseded. SDD §6 drops `.claude/skills/`; C-08's symlink sentence is replaced; W-10 needs no symlink or copy case.
- `init_library.py` has no copy path for skills (P2 effort falls by about 0.5 to 1 day; 0.1 to 0.25 is added for the adapter documentation and command).
- Claude Code does not list the skills automatically until the adapter is run; an agent reaches them through `AGENTS.md`. Whether each runtime reads `AGENTS.md` on its own and follows a skill pointer reliably is **not verified**: Claude Code was not tested alone and no other runtime was tested.
- FR7.1's acceptance ("both skills work on the pilot library without edits") is shown in P4 through `AGENTS.md`, and separately with the adapter for Claude Code.
- V-09's carried items (real symlink, "Use this template" keeps the symlink) are dropped.

## Alternatives

- Keep the symlinks: breaks on Windows without symlink rights.
- Symlinks with a copy fallback in `init_library.py`: two behaviours and a drift risk in the copies.
- Always copy with a sync check: duplicate files.
- A product plugin manifest: needs an install step; remains available later.
