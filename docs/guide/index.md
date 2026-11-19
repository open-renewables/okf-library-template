# User guide

How to work on this library: an Open Knowledge Format (OKF) v0.3 bundle in `knowledge/`, the profile that governs it in `profile/`, and the tooling in `scripts/`. Agents start at [`AGENTS.md`](../../AGENTS.md); this guide is for the people who maintain, author and customise the library.

| Page | For |
| --- | --- |
| [Getting started](getting-started.md) | Creating a library, or how this one was created, and the first steps on a clone |
| [Maintaining a library](maintaining.md) | Reviews, approval and trust tiers, revision history, releases, the site, staleness, dependencies |
| [Customising the profile](customising.md) | Concept types, sections, formats, vocabularies, path rules, warnings, statuses, folder scope, renaming the primary type |
| [Reference](reference.md) | Commands, revision-line grammar, commit trailers, finding codes |
| [Finding codes](finding-codes.md) | Every `OKF` code the validator reports, with its level and check |

Procedures, step by step:

| Runbook | When |
| --- | --- |
| [Promote a library to public](runbook-promote-to-public.md) | A private GitHub library goes public, normally at its `v1.0.0` |
| [Move a git-local library to a platform](runbook-move-git-local-to-platform.md) | A library run with git and Python alone moves to GitHub |
| [Recover the revision writer](runbook-revision-writer-recovery.md) | A revision run failed, a line is missing, or the bot cannot push |
| [Remove leaked content](runbook-remove-leaked-content.md) | A secret or confidential text reached the repository |

The rules for who approves what, what makes a concept `stable`, and how releases are numbered are in [`GOVERNANCE.md`](../../GOVERNANCE.md).
