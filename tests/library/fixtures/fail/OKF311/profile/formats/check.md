---
format: check
item:
  pattern: '^\*\*(?P<name>[^*]+)\*\*: (?P<text>.+)$'
  enums: {}
  vocab: {}
children:
  - label: Pass
    required: true
    enum: [yes, no]
  - label: Flag
    required: true
---

# Format: check

Applies to the top-level list items of a *Checks* section. Each item names a check and states it in one sentence; two sub-items follow, indented four spaces (two-space nesting renders differently on GitHub and on the site).

```markdown
- **Name of the check**: what is checked, in one sentence.
    - Pass: what a satisfactory result looks like.
    - Flag: what should be raised with the owner.
```
