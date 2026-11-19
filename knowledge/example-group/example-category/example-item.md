---
type: Item
uid: ITM-0001
title: Example item
description: A worked example of an Item concept, showing every declared section.
tags: [group:example-group, category:example-category]
status: draft
sources:
  - id: okf-spec
    resource: https://github.com/open-knowledge-format/open-knowledge-format
---

# Example item

## Description

This item shows how a concept is written to the profile. The description is plain prose in the author's own words and cites its source with a footnote whose label is the id of a `sources` entry.[^okf-spec] Terms are linked to the [glossary](../../glossary.md#example-term) and tag values are defined in the [group vocabulary](../../vocab/group.md) and the [category vocabulary](../../vocab/category.md).

## Checks

- **Source cited**: the description cites at least one source.
    - Pass: a footnote or external link supports each claim.
    - Flag: a claim has no source; raise it with the owner.
- **Terms defined**: each term of art links to the glossary.
    - Pass: the first use of every glossary term is a link.
    - Flag: a term of art is used without a definition.

## Revision history

<!-- Maintained by CI. Do not edit. -->

- 2026-11-01 · author @richard-gledhill · self-approved (owner) · PR #16
- 2026-11-19 · author @richard-gledhill · self-approved (owner) · PR #54 · agent-drafted

[^okf-spec]: Open Knowledge Format specification v0.3, <https://github.com/open-knowledge-format/open-knowledge-format>.
