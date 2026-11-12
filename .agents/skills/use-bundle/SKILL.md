---
name: use-bundle
description: Answer questions from an OKF knowledge bundle (a release archive or a clone) by reading index files one level at a time and only the concept sections needed, then cite each concept used by its uid, status, trust tier and release tag. Use when asked to look something up in, or apply the knowledge of, an OKF library; do not use to write or change concepts.
license: Apache-2.0
compatibility: Reads files only; needs no script, network or package. Works on an unpacked release archive or a git checkout.
---

# Use a knowledge bundle

You are reading a library of Markdown concepts. Read as little as you need, and say how far each answer can be trusted.

## 1. Orient

1. Read `AGENTS.md` at the root of the archive or checkout.
2. Find the **release tag**. In an archive, read the `RELEASE` file at the root. In a checkout, use the tag the user names, or `git describe --tags`. If none can be found, ask the user; never invent one. An answer without a tag says so.
3. Read `profile/profile.yaml`. It declares the concept types, their body sections, the statuses in use, the vocabulary folder and the tag rules. Take every type name, `uid` prefix, section heading and tag namespace from it, not from memory.

## 2. Navigate one level at a time

1. Open `knowledge/index.md`. Each line is a folder or a concept with a one-line description; concept lines end with the status and trust tier.
2. Choose the folder that fits the question and open its `index.md`. Repeat until you reach concept lines that fit.
3. Do not open every file. Do not list a folder instead of reading its index.
4. Open a concept only when its description fits. Read its frontmatter, then only the sections the profile declares for its type that bear on the question, by heading.
5. A tag such as `namespace:value` is defined in the vocabulary concept for that namespace in the profile's vocabulary folder. Read the definition before relying on the tag.
6. Follow a link to another concept only when the answer needs it.

## 3. Judge what you read

Trust tier is on the index line. Keep it exactly as written, including a qualifier in brackets.

| Tier | Meaning | How to speak of it |
| --- | --- | --- |
| Unverified | No recorded review | "Unverified: no review is recorded." Never call it reviewed or approved |
| Machine-confirmed | Drafted or checked by an agent, or approved without an owner's review | "Machine-confirmed: not reviewed by a human owner" |
| Human-reviewed | A human directory owner approved | "Human-reviewed" |
| Human-reviewed (self) | Reviewed only by the author, who is also the owner | "Human-reviewed (self): one person wrote and approved it" |

Also say so when:

- the status is `draft` (not yet published as settled knowledge) or `deprecated` (superseded; look for what replaced it);
- the concept's last *Revision history* line is older than its `stale_after` date, or older than the profile's `stale_after_default`;
- two concepts disagree: report both, with their tiers, and do not choose silently;
- the bundle holds nothing on the question: say so rather than answer from general knowledge. If you add general knowledge, label it as not from the bundle.

Never edit a bundle file while using it.

## 4. Report

End every answer with the concepts you used, one line each:

```
- <uid> · <title> · <status> · <trust tier> · <release tag> · <path>
```

Quote or paraphrase only what the concept says. Cite the concept's own sources (its footnotes) when the user needs the original source. Where the tag is unknown, write `release tag unknown` in place of it.
