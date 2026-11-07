"""The ``git-local`` adapter: commit trailers instead of a platform (SDD AD-19, I-08, QA-59).

Each change is one squash commit on ``main``. Authors and approvers are resolved to logins through the profile's
``maintainers`` map (login to emails); an address not in the map is recorded by its local part. Trailers are not
authenticated, which is accepted for single-user libraries. There is no separate merger: the commit author is
the one who merged, so a change nobody else approved is recorded as ``self-approved``.
"""

from __future__ import annotations

import re

from okfprofile.config import Profile
from okfprofile.platforms import CommitInfo, MergedChange, MergeReview, normalise_login

ADDRESS = re.compile(r"<(?P<email>[^>]+)>")


class GitLocalAdapter:
    """Resolve a commit from its message trailers.

    Args:
        profile: The loaded profile (maintainers and label names).
    """

    def __init__(self, profile: Profile) -> None:
        self.by_email = {email.lower(): login for login, emails in profile.maintainers.items() for email in emails}
        self.full_review_label = profile.rules.full_review_label
        self.agent_label = profile.rules.agent_label

    def login_for(self, email: str, fallback: str = "") -> str:
        """The login an email address stands for: the maintainer who lists it, else its local part."""
        known = self.by_email.get(email.strip().lower())
        return normalise_login(known or email.split("@", 1)[0] or fallback)

    def resolve(self, commit: CommitInfo) -> MergedChange:
        """The merged change for ``commit``; approvals come from ``Approved-by`` trailers."""
        author = self.login_for(commit.author_email, commit.author_name)
        reviews = []
        approved = commit.trailers.get("approved-by", "")
        for part in filter(None, (p.strip() for p in approved.split(";"))):
            match = ADDRESS.search(part)
            who = self.login_for(match["email"]) if match else normalise_login(part)
            if who != author:
                reviews.append(MergeReview(who, "APPROVED", commit.sha, commit.when.isoformat()))
        labels = set()
        if commit.trailers.get("full-review", "").lower() == "yes":
            labels.add(self.full_review_label)
        if commit.trailers.get("agent-drafted", "").lower() == "yes":
            labels.add(self.agent_label)
        return MergedChange(commit, "commit", None, author, author, commit.sha, tuple(reviews), frozenset(labels))
