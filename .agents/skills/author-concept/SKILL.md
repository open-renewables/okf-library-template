---
name: author-concept
description: Draft a new concept for an OKF knowledge library from a clone of its repository, following the library's profile (declared type, body sections, formats, vocabularies), and leave it as a validated, agent-drafted draft for a human to review. Use when asked to add or write a concept; do not use to answer questions from the library.
license: Apache-2.0
compatibility: Needs a clone of the library repository with Python 3.11 or later and uv, because it runs scripts in scripts/. Not usable from a release archive.
---

# Author a concept

You write drafts. A person reviews and publishes them. Everything the library requires is declared in `profile/profile.yaml`, the schemas in `profile/types/`, the section formats in `profile/formats/` and the vocabulary concepts; read those, do not rely on memory of another library.

## Before you start

1. Read `AGENTS.md` and `profile/profile.yaml`: which types exist, where each may live (`paths`), its body sections in order, which are required, the empty placeholder, any section format, and which sections are CI-managed.
2. Read the type's schema in `profile/types/` for the frontmatter it requires.
3. Read the vocabulary concepts for the tag namespaces the type needs. Use only values defined there. If a value you need is missing, stop and tell the user; adding a value is a change to the vocabulary that an owner approves.
4. Read one existing concept of the same type as a worked example, and a section format in `profile/formats/` for any section that has one.
5. Check `platform` in the profile: it decides how the draft is labelled (step 6).

## Steps

1. Create the file. The folder path gives some tags, and the next `uid` is assigned for you:

   ```bash
   uv run scripts/new_concept.py <type> <folder>/<name> --title "<title>" --description "<one sentence>"
   ```

2. Fill each declared section in the declared order and format, in your own words. Where a section has nothing yet, leave the profile's placeholder rather than inventing content.
3. Cite sources as footnotes (or external links) for every claim of substance. Never cite a source you have not read. A concept without a source cannot become `stable`.
4. Leave `status: draft`. Only a human owner makes a concept `stable`. Do not add `verified`, `generated` or other fields the schema does not ask for.
5. Do not edit by hand: the *Revision history* section, any `index.md`, `profile/uid-registry.yaml`. Then rebuild the indexes and validate:

   ```bash
   uv run scripts/build_indexes.py
   uv run scripts/validate_profile.py
   ```

   Fix every error. A warning needs a reason or a fix. Run `uv run poe check` before you hand over.
6. Mark the change as agent-drafted so the review records it:
   - `platform: github`: apply the label named by `rules.agent_label` in the profile to the pull request.
   - `platform: git-local`: add the trailer `Agent-Drafted: yes` to the commit message.
7. Keep tooling and content apart. A change to `scripts/`, `profile/` or `.github/` goes in a separate pull request from a concept, unless it carries the migration label the profile names.
8. Open the pull request (or commit) with a short description: what the concept is, its sources, and anything you were unsure of.

## Special cases

- A vocabulary concept needs its `namespace` key set by hand after the file is created, and a library has at most one common-terms (glossary) concept. If the type you need is one of these, read the existing one first.
- Moving or renaming a concept needs the approved-move label the profile names; a concept is never deleted, only deprecated.
- If a rule in the profile seems wrong, say so; do not work around it.

## What you must not do

- Mark anything `stable`, reviewed or approved.
- Edit CI-managed sections, indexes or the registry by hand.
- Weaken the profile, a schema or a check to make a draft pass.
- Copy text from a source; summarise and cite it.
