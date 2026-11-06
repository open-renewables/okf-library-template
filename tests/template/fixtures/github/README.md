# Recorded GitHub responses

`sandbox-2026-11-03.json` holds real API responses recorded on 2026-11-03 from the synthetic pull requests #2 to #5 and two direct pushes in `open-renewables-sandbox/p0-spikes` (plan step 1, V-05). The adapter tests replay them; no test reaches the network (`../../../../docs/development/constraints.md`).

| Part | Contents |
| --- | --- |
| `merge_shas` | The squash commit of each pull request: `stale` (#2: the App approved head A, the owner pushed head B and merged), `noreview` (#3: merged by the owner past the Admin bypass), `lk1` (#4) and `lk2` (#5) |
| `direct_shas` | Two pushes to `main` by the App through the "always" bypass, with no pull request (the author and committer have no GitHub user) |
| `routes` | Response by request path, as `GitHubAdapter` asks for it: the closed-pull-request list (cut to #2 to #5), `pulls/{n}`, `pulls/{n}/reviews?per_page=100`, `commits/{sha}` and `commits/{sha}/pulls` |

Responses are real. Only noise was removed: `*_url` fields other than `html_url`, `_links`, node and gravatar IDs, avatar URLs, PR bodies and the large `repo` objects. Nothing the adapter reads was changed.

Not recorded, and so built by hand in the tests: a review by a code owner other than the author, and a merge by someone other than the author (the sandbox has one human account, plan OD-2). See `known-gaps.md`, G9.
