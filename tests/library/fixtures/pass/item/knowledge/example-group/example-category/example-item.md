---
type: Item
uid: ITM-0001
title: Example item
description: One sentence.
tags: [group:example-group, category:example-category]
status: draft
stale_after: 2027-01-01T00:00:00Z
generated: { by: agent/1, at: 2026-10-20T09:00:00Z }
verified: { by: human:alice, at: 2026-10-21T09:00:00+01:00 }
sources:
  - id: s1
    resource: https://example.org
---

# Example item

## Description

Some text with a footnote.[^s1] See <a id="anchor"></a>the anchor, [a section](#checks), [the vocabulary](../../vocab/group.md#group-vocabulary) and `<code>`.

## Checks

- **Name**: does a thing
    - Pass: yes
    - Flag: no


## Revision history

<!-- Maintained by CI. Do not edit. -->
- 2026-10-20 · author @alice · self-approved (owner) · PR #1 · full-review

[^s1]: A source.
