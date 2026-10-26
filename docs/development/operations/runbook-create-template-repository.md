# Runbook: create the template repository

Status: Done once, on 26 October 2026; kept as the record of how the repository was set up and for rebuilding it.

Creates the public template repository `open-renewables/okf-library-template` from the `docs/development/` scaffold, 
before build phase P0 (SDD §14, set-up row). `open-renewables` is the GitHub organisation; the repository name is a 
placeholder (DDR QA-11).

## 1. Prerequisites

| Tool | Install | Check |
| --- | --- | --- |
| git 2.27+ | OS package manager | `git --version` |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`) | `uv --version` |
| Python 3.12 | `uv python install 3.12` | `uv python list` |
| GitHub CLI | https://cli.github.com | `gh auth login`, then `gh auth status` |

## 2. Organisation

A **free organisation**, not a personal account (SDD AD-01).

1. github.com → avatar → **Your organizations → New organization → Free**; add yourself as owner.
2. Organisation **Settings → Actions → General**: workflow permissions "Read repository contents and packages permissions"; enable "Require actions to be pinned to a full-length commit SHA" where offered (SDD §10).

## 3. First commit

```bash
mkdir okf-library-template && cd okf-library-template
unzip ~/Downloads/okf-docs-development-scaffold.zip
mv okf-library-template/* okf-library-template/.[!.]* . 2>/dev/null; rmdir okf-library-template
git init -b main
curl -sSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

Create `NOTICE`:

```
OKF library template
Copyright 2026 Richard Gledhill

Licensed under the Apache License, Version 2.0 (see LICENSE).
Libraries created from this template keep this notice for the files they inherit.
```

Create `README.md`:

```markdown
# OKF library template

A template for building validated, agent-ready knowledge libraries on the Open Knowledge Format (OKF) v0.2.

Status: in development (build phase P0). Design documents are in `docs/development/`; start with `docs/development/README.md`.

Licence: Apache 2.0 (see `LICENSE` and `NOTICE`).
```

Create `.gitignore`:

```
.venv/
__pycache__/
*.pyc
.coverage
coverage.xml
.pytest_cache/
.mypy_cache/
.ruff_cache/
site/
dist/
.DS_Store
```

```bash
git add .
git commit -m "Add development documentation scaffold, licence and notice"
```

## 4. Create and push

```bash
gh repo create open-renewables/okf-library-template --public \
  --description "Template for agent-ready OKF knowledge libraries" \
  --source . --push
```

## 5. Repository settings

```bash
R=open-renewables/okf-library-template
gh repo edit $R --enable-squash-merge --enable-merge-commit=false \
  --enable-rebase-merge=false --delete-branch-on-merge --template
gh api -X PUT repos/$R/actions/permissions/workflow \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false
gh api -X PATCH repos/$R \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
gh api -X PUT repos/$R/vulnerability-alerts
```

If a flag is rejected, use **Settings → General** and **Settings → Code security**.

## 6. Ruleset for `main`

**Settings → Rules → Rulesets → New branch ruleset**: name `main`; enforcement Active; target the default branch; bypass list *Repository admin*, **For pull requests only**. Rules: restrict deletions; block force pushes; require a pull request before merging with 1 approval and code-owner review; allowed merge method squash. Leave off "Require approval of the most recent reviewable push" and "Do not allow bypassing" (SDD §11).

Added in P2: the required status check `validate` and the GitHub App on the bypass list ("always").

## 7. Check

```bash
git switch -c docs/setup-check
echo "" >> docs/development/plan/README.md
git commit -am "Check pull request and squash-merge settings"
git push -u origin docs/setup-check
gh pr create --fill
gh pr merge --squash --admin
```

Pass when only a squash merge is offered, a direct `git push` to `main` is refused, and the branch is deleted after merge. Record the date and any deviation at the top of this runbook.

## 8. Afterwards

- From now on the copies in `docs/development/` are authoritative; the Claude Project copies are refreshed from them (SDD §2.2).
- P0 spikes run in a separate scratch repository and organisation (SDD §14).
- First V-10 check: open Claude Code in this repository and ask for a summary of the SRS.
