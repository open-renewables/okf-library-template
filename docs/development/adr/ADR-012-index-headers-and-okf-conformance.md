# ADR-012: Index scope headers and OKF conformance

**Status:** Accepted (owner, 2026-11-19; drafted in P4 PR 1 after the owner chose to keep the YAML header). **Supersedes:** none; amends ADR-010 by recording the conformance consequence and how check 1 reports it. **RFC:** [RFC-001](../rfcs/RFC-001-scope-notes.md). **Plan:** P4 step 2, proposed entry PP-1.

## Context

ADR-010 puts a folder's scope in a YAML header on its `index.md`. Building it showed that OKF does not allow this:

- **OKF v0.2** (the pinned specification, commit `ad30107`), §8: "Index files contain no frontmatter, with one exception: a bundle-root `index.md` MAY carry an `okf_version` key". §12 repeats that the root block is "the only place frontmatter is permitted in an `index.md`". §11 makes following §8 part of conformance, and also says consumers "MUST NOT reject a bundle" for unknown frontmatter keys. The pinned okf-skills checker warns `OKF117` on each index with a header.
- **OKF v0.3** (2026-11-18, in the new home `open-knowledge-format/open-knowledge-format`; the pinned repository is now marked deprecated), §8 and §8.1: the bundle-root index MAY carry `okf_version`, `title`, `description`, `license` and extension keys, and a regenerating producer MUST keep them; "An index file in a subdirectory has no frontmatter." So a root `description` is allowed from v0.3, and a folder header is still not.

The owner chose to keep the YAML header (2026-11-19) because Obsidian and other tools read YAML properties: Obsidian lists `description` among its default properties, and MkDocs Material uses a page's `description` front matter for its meta description and social cards. A search found no contradiction to that. No agent tooling was found that relies on index frontmatter; agents read the index body.

## Decision

1. ADR-010 stands: a folder index, and the root index, may carry a one-sentence `description` header, kept by the generator and shown on the parent's folder line.
2. Check 1 replaces okf-skills' per-index `OKF117` warnings about such headers with **one bundle-level warning, `OKF121`**, on the root index, naming every index that carries a scope header. The departure from OKF stays visible on every run without repeating on each index. `OKF117` is unchanged for every other reserved-file problem.
3. A header that is not usable is not counted in `OKF121`: check 5 reports it (`OKF505` not closed, not YAML or not a mapping; `OKF506` a key other than `description`, plus `okf_version` on the root, or a description that is not one line of text).
4. Headers are optional. The template ships without them, and a library that wants a strictly conformant v0.2 bundle leaves them out; nothing else depends on them.
5. When the template moves to OKF v0.3 (a separate decision), the root `description` is no longer a departure and drops out of `OKF121`; folder headers remain one unless OKF changes. Proposing folder-index metadata upstream is a post-`v1.0.0` item.

## Consequences

- A bundle with folder headers is not strictly conformant with OKF v0.2 §8 and §11 item 3, and says so in `OKF121`. Conforming consumers still read it (§11). The template's own example folders carry no header, so a new library validates without warnings and adds headers by choice; the guide and the `author-concept` skill say how.
- Check 1 gains one mapping rule; the vendored okf-skills validator is not modified (AD-08).
- New codes `OKF121`, `OKF505` and `OKF506`, each with a failing fixture.
- Known gap G42 records the non-conformance; the OKF v0.3 move is a follow-up outside P4.
