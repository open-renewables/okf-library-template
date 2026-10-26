# Claude Code instructions: OKF library template

Template only: `init_library.py` removes this file at instantiation, after which Claude Code reads the library's `AGENTS.md`.

@AGENTS.md
@docs/development/AGENTS.md

## Design documents

<!-- The file names contain spaces. V-10 (SDD §15) confirms whether these imports resolve as written; if not, use the form V-10 settles. -->

@docs/development/requirements/OKF Library Template - Software Requirements Spec.md
@docs/development/architecture/OKF Library Template - Software Design Document.md
@docs/development/adr/OKF Library Template - Design Decision Record.md
@docs/development/architecture/OKF library technology stack options.md

The quality bar is `docs/development/constraints.md` and the style guide is `docs/development/conventions.md`; they are referenced from `docs/development/AGENTS.md` rather than imported, to keep the context small.
