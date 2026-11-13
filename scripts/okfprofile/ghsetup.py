"""Configure a GitHub repository for a library (SDD W-01 step 4, W-11, C-04 ``setup_repo.py``, NFR7).

Every setting is compared with the repository's current state first, so a run lists exactly what it would change
(``--dry-run``), changes only that, and a second run changes nothing: rerunning restores settings that someone
deleted. Every request names its repository; nothing here reaches another one.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

from okfprofile.document import parse_yaml

LABELS_FILE = ".github/labels.yml"
VALIDATE_WORKFLOW = ".github/workflows/validate.yml"
PROFILE = "profile/profile.yaml"
RULESET_NAME = "main-protect"
PAGES_ENVIRONMENT = "github-pages"
PAGES_REFS = (("main", "branch"), ("v*", "tag"))
ADMIN_ROLE_ID = 5
APP_CLIENT_VARIABLE = "APP_CLIENT_ID"
APP_KEY_SECRET = "APP_PRIVATE_KEY"  # noqa: S105 - the name of a secret, not its value
REPO_SETTINGS: dict[str, Any] = {
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    "squash_merge_commit_title": "PR_TITLE",
    "squash_merge_commit_message": "PR_BODY",
    "delete_branch_on_merge": True,
}
WORKFLOW_PERMISSIONS = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
HTTP_NOT_FOUND = "HTTP 404"


class GhError(Exception):
    """A request to GitHub failed."""


class NotFoundError(GhError):
    """GitHub answered 404."""


class GitHubApi(Protocol):
    """The calls ``setup_repo`` makes."""

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        """Send a request and return the parsed JSON, or None for an empty answer."""
        ...

    def paginate(self, path: str) -> list[Any]:
        """Every item of a list endpoint."""
        ...


class GhCli:
    """``GitHubApi`` over the ``gh`` command line, using the user's own authentication."""

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        """Send one request with ``gh api``; a 404 raises ``NotFoundError``."""
        command = ["gh", "api", "-X", method, path] + (["--input", "-"] if body is not None else [])
        done = subprocess.run(  # noqa: S603 - fixed program; the path is built from validated parts
            command,
            capture_output=True,
            check=False,
            input=json.dumps(body).encode("utf-8") if body is not None else None,
        )
        if done.returncode != 0:
            detail = done.stderr.decode("utf-8", errors="replace").strip() or done.stdout.decode(
                "utf-8", errors="replace"
            )
            error = NotFoundError if HTTP_NOT_FOUND in detail else GhError
            msg = f"gh api {method} {path}: {detail}"
            raise error(msg)
        out = done.stdout.decode("utf-8", errors="replace").strip()
        return json.loads(out) if out else None

    def paginate(self, path: str) -> list[Any]:
        """Every item of a list endpoint, with ``gh api --paginate --slurp``."""
        done = subprocess.run(  # noqa: S603 - fixed program and arguments
            ["gh", "api", "--paginate", "--slurp", path],  # noqa: S607 - gh is found on PATH by design
            capture_output=True,
            check=False,
        )
        if done.returncode != 0:
            msg = f"gh api {path}: {done.stderr.decode('utf-8', errors='replace').strip()}"
            raise GhError(msg)
        pages = json.loads(done.stdout.decode("utf-8") or "[]")
        return [item for page in pages for item in (page if isinstance(page, list) else [page])]


@dataclass(frozen=True)
class Operation:
    """One change to make: what it is, and the request that makes it."""

    area: str
    detail: str
    method: str
    path: str
    body: dict[str, Any] | None = None


@dataclass
class Plan:
    """The changes a run needs, the things it skipped and the manual steps left."""

    operations: list[Operation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def covers(current: Any, desired: Any) -> bool:
    """True if ``current`` holds everything ``desired`` asks for (GitHub adds defaults to what it returns)."""
    if isinstance(desired, dict):
        return isinstance(current, dict) and all(k in current and covers(current[k], v) for k, v in desired.items())
    if isinstance(desired, list):
        return (
            isinstance(current, list)
            and len(current) == len(desired)
            and all(any(covers(c, d) for c in current) for d in desired)
        )
    return bool(current == desired)


def read_labels(root: Path) -> list[dict[str, str]]:
    """The labels in ``.github/labels.yml``.

    Raises:
        GhError: If the file is missing or malformed.
    """
    try:
        data, _ = parse_yaml((root / LABELS_FILE).read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"cannot read {LABELS_FILE}: {exc.strerror}"
        raise GhError(msg) from exc
    if not isinstance(data, list) or not all(isinstance(i, dict) and {"name", "color"} <= set(i) for i in data):
        msg = f"{LABELS_FILE} must be a list of labels with a name and a colour"
        raise GhError(msg)
    return [
        {"name": str(i["name"]), "color": str(i["color"]), "description": str(i.get("description", ""))} for i in data
    ]


def plan_settings(api: GitHubApi, repo: str, plan: Plan) -> dict[str, Any]:
    """Squash-only merges, read-only workflow permissions and dependency alerts."""
    info: dict[str, Any] = api.request("GET", f"repos/{repo}")
    differing = {k: v for k, v in REPO_SETTINGS.items() if info.get(k) != v}
    if differing:
        plan.operations.append(
            Operation("merge methods", ", ".join(sorted(differing)), "PATCH", f"repos/{repo}", differing)
        )
    current = api.request("GET", f"repos/{repo}/actions/permissions/workflow") or {}
    if not covers(current, WORKFLOW_PERMISSIONS):
        plan.operations.append(
            Operation(
                "workflow permissions",
                "read-only default token",
                "PUT",
                f"repos/{repo}/actions/permissions/workflow",
                WORKFLOW_PERMISSIONS,
            )
        )
    try:
        api.request("GET", f"repos/{repo}/vulnerability-alerts")
    except NotFoundError:
        plan.operations.append(Operation("dependency alerts", "enable", "PUT", f"repos/{repo}/vulnerability-alerts"))
    return info


def plan_labels(api: GitHubApi, repo: str, root: Path, plan: Plan) -> None:
    """Create each label in ``labels.yml`` that is missing and fix one whose colour or description differs."""
    existing = {str(item["name"]): item for item in api.paginate(f"repos/{repo}/labels?per_page=100")}
    for label in read_labels(root):
        current = existing.get(label["name"])
        body = {"color": label["color"], "description": label["description"]}
        if current is None:
            plan.operations.append(
                Operation(
                    "label", f"create {label['name']}", "POST", f"repos/{repo}/labels", {"name": label["name"], **body}
                )
            )
        elif (str(current.get("color", "")).lower(), current.get("description") or "") != (
            label["color"].lower(),
            label["description"],
        ):
            path = f"repos/{repo}/labels/{quote(label['name'], safe='')}"
            plan.operations.append(Operation("label", f"update {label['name']}", "PATCH", path, body))


def find_app(api: GitHubApi, org: str, slug: str) -> int | None:
    """The App ID of the installation named ``slug`` in an organisation, or None."""
    for installation in api.request("GET", f"orgs/{org}/installations?per_page=100").get("installations", []):
        if installation.get("app_slug") == slug:
            return int(installation["app_id"])
    return None


def desired_ruleset(app_id: int | None, require_validate: bool, name: str = RULESET_NAME) -> dict[str, Any]:
    """The ``main`` ruleset of SDD section 11, under the name ``name``."""
    bypass = [{"actor_id": ADMIN_ROLE_ID, "actor_type": "RepositoryRole", "bypass_mode": "pull_request"}]
    if app_id is not None:
        bypass.append({"actor_id": app_id, "actor_type": "Integration", "bypass_mode": "always"})
    rules: list[dict[str, Any]] = [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": True,
                "require_last_push_approval": False,
                "required_review_thread_resolution": False,
                "allowed_merge_methods": ["squash"],
            },
        },
    ]
    if require_validate:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [{"context": "validate"}],
                    "strict_required_status_checks_policy": False,
                },
            }
        )
    return {
        "name": name,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": bypass,
        "rules": rules,
    }


def _bypass_key(actor: dict[str, Any]) -> tuple[Any, Any, Any]:
    return actor.get("actor_id"), actor.get("actor_type"), actor.get("bypass_mode")


def plan_ruleset(
    api: GitHubApi, repo: str, app_id: int | None, require_validate: bool, plan: Plan, name: str = RULESET_NAME
) -> None:
    """Create or update the ruleset called ``name`` so it matches the design."""
    desired = desired_ruleset(app_id, require_validate, name)
    found = next((r for r in api.paginate(f"repos/{repo}/rulesets") if r.get("name") == name), None)
    if found is None:
        plan.operations.append(Operation("ruleset", f"create {name}", "POST", f"repos/{repo}/rulesets", desired))
        return
    current = api.request("GET", f"repos/{repo}/rulesets/{found['id']}")
    same = (
        current.get("enforcement") == desired["enforcement"]
        and covers(current.get("conditions"), desired["conditions"])
        and {_bypass_key(a) for a in current.get("bypass_actors", [])}
        == {_bypass_key(a) for a in desired["bypass_actors"]}
        and covers(current.get("rules"), desired["rules"])
        and len(current.get("rules", [])) == len(desired["rules"])
    )
    if not same:
        plan.operations.append(
            Operation("ruleset", f"update {name}", "PUT", f"repos/{repo}/rulesets/{found['id']}", desired)
        )


def plan_security(info: dict[str, Any], repo: str, plan: Plan) -> None:
    """Native secret scanning and push protection (public repositories)."""
    wanted = {"secret_scanning": {"status": "enabled"}, "secret_scanning_push_protection": {"status": "enabled"}}
    if not covers(info.get("security_and_analysis") or {}, wanted):
        plan.operations.append(
            Operation(
                "secret scanning",
                "enable with push protection",
                "PATCH",
                f"repos/{repo}",
                {"security_and_analysis": wanted},
            )
        )


def plan_public_extras(api: GitHubApi, repo: str, plan: Plan) -> None:
    """CodeQL default setup and GitHub Pages (W-11 step 3)."""
    setup = api.request("GET", f"repos/{repo}/code-scanning/default-setup") or {}
    if setup.get("state") != "configured":
        body = {"state": "configured", "languages": ["actions", "python"], "query_suite": "default"}
        plan.operations.append(
            Operation(
                "code scanning",
                "configure CodeQL default setup",
                "PATCH",
                f"repos/{repo}/code-scanning/default-setup",
                body,
            )
        )
    try:
        api.request("GET", f"repos/{repo}/pages")
    except NotFoundError:
        plan.operations.append(
            Operation("pages", "enable, built by workflow", "POST", f"repos/{repo}/pages", {"build_type": "workflow"})
        )
    _pages_environment(api, repo, plan)


def _pages_environment(api: GitHubApi, repo: str, plan: Plan) -> None:
    """Let the ``github-pages`` environment take a deployment from ``main`` and from a release tag (``site.yml``).

    Enabling Pages leaves the environment open to the ``main`` branch only, so the tag run that publishes the
    site would be refused before any step ran (seen in the P3 rehearsal).
    """
    base = f"repos/{repo}/environments/{PAGES_ENVIRONMENT}"
    try:
        found = api.request("GET", f"{base}/deployment-branch-policies") or {}
        have = {(p["name"], p["type"]) for p in found.get("branch_policies", [])}
    except NotFoundError:
        have = set()
    if not have:
        policy = {"protected_branches": False, "custom_branch_policies": True}
        plan.operations.append(
            Operation(
                "pages environment",
                "limit deployments to listed refs",
                "PUT",
                base,
                {"deployment_branch_policy": policy},
            )
        )
    for name, kind in PAGES_REFS:
        if (name, kind) not in have:
            plan.operations.append(
                Operation(
                    "pages environment",
                    f"allow {kind} {name}",
                    "POST",
                    f"{base}/deployment-branch-policies",
                    {"name": name, "type": kind},
                )
            )


def promote_profile(root: Path) -> bool:
    """Set ``rules.revision_token: github-app`` in the working tree's profile (W-11 step 3); True if it changed."""
    path = root / PROFILE
    text = path.read_bytes().decode("utf-8")
    new = re.sub(r"^(  revision_token: )github-token\b", r"\1github-app", text, count=1, flags=re.MULTILINE)
    if new == text:
        return False
    path.write_bytes(new.encode("utf-8"))
    return True


def build_plan(
    api: GitHubApi,
    repo: str,
    root: Path,
    app_slug: str | None = None,
    require_check: bool | None = None,
    promote: bool = False,
    ruleset_name: str = RULESET_NAME,
) -> Plan:
    """Work out what has to change in ``repo``.

    Args:
        api: GitHub.
        repo: ``owner/name``.
        root: The library's working tree (labels, workflows).
        app_slug: The revision App's slug, for its ruleset bypass.
        require_check: Require the ``validate`` check; default is yes when ``validate.yml`` exists.
        promote: Also plan the public-repository extras of W-11.

    Returns:
        The plan. A private repository gets no ruleset or scanning (GitHub Free offers neither); ``promote`` on a
        private repository is a problem, because making it public is the owner's step.
    """
    plan = Plan()
    info = plan_settings(api, repo, plan)
    plan_labels(api, repo, root, plan)
    public = info.get("visibility") == "public"
    if promote and not public:
        plan.problems.append("the repository is not public: make it public first (W-11 step 1), then run --promote")
        return plan
    if not public:
        plan.notes.append("private repository: no ruleset or native secret scanning on GitHub Free; CI checks apply")
        return plan
    app_id = None
    if app_slug:
        app_id = find_app(api, repo.split("/")[0], app_slug)
        if app_id is None:
            plan.problems.append(f"the App '{app_slug}' is not installed in {repo.split('/')[0]}")
    elif promote:
        plan.problems.append("--promote needs --app-slug: the revision App must be on the bypass list")
    use_check = (root / VALIDATE_WORKFLOW).is_file() if require_check is None else require_check
    plan_ruleset(api, repo, app_id, use_check, plan, ruleset_name)
    plan_security(info, repo, plan)
    if promote:
        plan_public_extras(api, repo, plan)
        plan.notes.append("enable immutable releases in Settings > General (no API is used for it)")
    return plan


def apply_plan(api: GitHubApi, plan: Plan) -> None:
    """Make each planned change."""
    for op in plan.operations:
        api.request(op.method, op.path, op.body)


def check_app(api: GitHubApi, repo: str, slug: str, ruleset_name: str = RULESET_NAME) -> list[str]:
    """Check the revision App's set-up (C-06): installed, on the ruleset bypass list, variable and secret present.

    Args:
        api: GitHub.
        repo: ``owner/name``.
        slug: The App's slug.
        ruleset_name: The ruleset that must list the App.

    Returns:
        Problems found; empty if everything is in place.
    """
    problems: list[str] = []
    org = repo.split("/")[0]
    app_id = find_app(api, org, slug)
    if app_id is None:
        return [f"the App '{slug}' is not installed in {org}"]
    found = next((r for r in api.paginate(f"repos/{repo}/rulesets") if r.get("name") == ruleset_name), None)
    bypass = api.request("GET", f"repos/{repo}/rulesets/{found['id']}").get("bypass_actors", []) if found else []
    if (app_id, "Integration", "always") not in {_bypass_key(a)[:3] for a in bypass}:
        problems.append(f"the App is not on the {ruleset_name} ruleset bypass list with mode 'always'")
    expected = api.request("GET", f"apps/{slug}").get("client_id")
    try:
        value = (api.request("GET", f"repos/{repo}/actions/variables/{APP_CLIENT_VARIABLE}") or {}).get("value")
    except NotFoundError:
        value = None
        problems.append(f"the variable {APP_CLIENT_VARIABLE} is missing")
    if value is not None and value != expected:
        problems.append(f"{APP_CLIENT_VARIABLE} is not the App's client ID (check capital I and lower case l)")
    try:
        api.request("GET", f"repos/{repo}/actions/secrets/{APP_KEY_SECRET}")
    except NotFoundError:
        problems.append(f"the secret {APP_KEY_SECRET} is missing")
    return problems
