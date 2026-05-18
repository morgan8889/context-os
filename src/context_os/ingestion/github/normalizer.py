"""GitHub API response normalizer — maps GitHub objects to core ontology types.

Maps raw GitHub API responses to Context-OS node property dicts.
The output dicts are used by graph/mutations.py upsert_node().
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _make_id(source_id: str, tenant_id: str, prefix: str = "gh") -> str:
    """Generate a deterministic UUID from source_id + tenant_id + prefix.

    This ensures the same GitHub object always maps to the same graph node UUID,
    preventing duplicates across incremental syncs.

    Args:
        source_id: Vendor-assigned ID (repo name, PR number, etc.).
        tenant_id: Clerk org ID.
        prefix: Integration prefix for namespace separation.

    Returns:
        UUID string.
    """
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000001")
    return str(uuid.uuid5(namespace, f"{prefix}:{tenant_id}:{source_id}"))


class GitHubNormalizer:
    """Normalize GitHub API responses to Context-OS ontology node dicts.

    Each method returns a node property dict with 'node_type' plus all
    required BaseNodeSchema fields (id, tenant_id, source, source_id,
    fetch_ts, created_at, updated_at).
    """

    def __init__(self, tenant_id: str) -> None:
        """Initialize normalizer for a specific tenant.

        Args:
            tenant_id: Clerk org ID for all produced nodes.
        """
        self.tenant_id = tenant_id

    def repo_to_initiative(self, repo: dict[str, Any]) -> dict[str, Any]:
        """Map a GitHub repository to an Initiative node.

        Args:
            repo: Raw GitHub repository API response.

        Returns:
            Initiative node property dict.
        """
        source_id = str(repo["id"])
        now = _now_iso()
        status = "archived" if repo.get("archived") else "active"

        return {
            "node_type": "Initiative",
            "id": _make_id(source_id, self.tenant_id, "gh_repo"),
            "tenant_id": self.tenant_id,
            "source": "github",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": repo.get("created_at", now),
            "updated_at": repo.get("updated_at", now),
            # Initiative-specific
            "title": repo.get("name", ""),
            "description": repo.get("description") or "",
            "status": status,
            "url": repo.get("html_url", ""),
        }

    def milestone_to_goal(
        self, milestone: dict[str, Any], repo_full_name: str
    ) -> dict[str, Any]:
        """Map a GitHub milestone to a Goal node.

        Args:
            milestone: Raw GitHub milestone API response.
            repo_full_name: Repository "owner/repo" for source_id namespacing.

        Returns:
            Goal node property dict.
        """
        source_id = f"{repo_full_name}/milestone/{milestone['number']}"
        now = _now_iso()

        state = milestone.get("state", "open")
        status_map = {"open": "open", "closed": "done"}
        status = status_map.get(state, "open")

        return {
            "node_type": "Goal",
            "id": _make_id(source_id, self.tenant_id, "gh_milestone"),
            "tenant_id": self.tenant_id,
            "source": "github",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": milestone.get("created_at", now),
            "updated_at": milestone.get("updated_at", now),
            # Goal-specific
            "title": milestone.get("title", ""),
            "description": milestone.get("description") or "",
            "status": status,
            "due_date": milestone.get("due_on") or "",
            "url": milestone.get("html_url", ""),
        }

    def pr_to_artifact(self, pr: dict[str, Any], repo_full_name: str) -> dict[str, Any]:
        """Map a GitHub pull request to an Artifact node.

        Args:
            pr: Raw GitHub pull request API response.
            repo_full_name: Repository "owner/repo" for source_id namespacing.

        Returns:
            Artifact node property dict.
        """
        source_id = f"{repo_full_name}/pull/{pr['number']}"
        now = _now_iso()

        state = pr.get("state", "open")
        if pr.get("merged_at"):
            status = "merged"
        elif state == "closed":
            status = "closed"
        elif pr.get("draft"):
            status = "draft"
        else:
            status = "open"

        return {
            "node_type": "Artifact",
            "id": _make_id(source_id, self.tenant_id, "gh_pr"),
            "tenant_id": self.tenant_id,
            "source": "github",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": pr.get("created_at", now),
            "updated_at": pr.get("updated_at", now),
            # Artifact-specific
            "title": pr.get("title", ""),
            "content": pr.get("body") or "",
            "artifact_type": "pull_request",
            "status": status,
            "url": pr.get("html_url", ""),
        }

    def issue_to_signal_or_artifact(
        self,
        issue: dict[str, Any],
        repo_full_name: str,
    ) -> dict[str, Any]:
        """Map a GitHub issue to Signal (open) or Artifact (closed).

        Args:
            issue: Raw GitHub issue API response.
            repo_full_name: Repository "owner/repo" for source_id namespacing.

        Returns:
            Signal or Artifact node property dict.
        """
        source_id = f"{repo_full_name}/issue/{issue['number']}"
        now = _now_iso()
        state = issue.get("state", "open")

        if state == "closed":
            return {
                "node_type": "Artifact",
                "id": _make_id(source_id, self.tenant_id, "gh_issue"),
                "tenant_id": self.tenant_id,
                "source": "github",
                "source_id": source_id,
                "fetch_ts": now,
                "created_at": issue.get("created_at", now),
                "updated_at": issue.get("updated_at", now),
                "title": issue.get("title", ""),
                "content": issue.get("body") or "",
                "artifact_type": "issue",
                "status": "closed",
                "url": issue.get("html_url", ""),
            }
        else:
            return {
                "node_type": "Signal",
                "id": _make_id(source_id, self.tenant_id, "gh_issue"),
                "tenant_id": self.tenant_id,
                "source": "github",
                "source_id": source_id,
                "fetch_ts": now,
                "created_at": issue.get("created_at", now),
                "updated_at": issue.get("updated_at", now),
                "content": (
                    f"{issue.get('title', '')} — {issue.get('body', '') or ''}".strip(
                        " —"
                    )
                ),
                "signal_type": "comment",
                "url": issue.get("html_url", ""),
                "occurred_at": issue.get("created_at", now),
            }

    def user_to_actor(self, user: dict[str, Any]) -> dict[str, Any]:
        """Map a GitHub user to an Actor node.

        Args:
            user: Raw GitHub user API response (requires full user object, not summary).

        Returns:
            Actor node property dict.
        """
        source_id = str(user.get("id", user.get("login", "")))
        now = _now_iso()

        identities = [
            {
                "source": "github",
                "id": str(user.get("id", "")),
                "login": user.get("login", ""),
            }
        ]

        return {
            "node_type": "Actor",
            "id": _make_id(source_id, self.tenant_id, "gh_user"),
            "tenant_id": self.tenant_id,
            "source": "github",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": user.get("created_at", now),
            "updated_at": user.get("updated_at", now),
            # Actor-specific
            "name": user.get("name") or user.get("login", ""),
            "email": user.get("email") or "",
            "identities": str(identities),  # JSON string for AGE storage
        }

    def review_to_signal(
        self,
        review: dict[str, Any],
        repo_full_name: str,
        pull_number: int,
    ) -> dict[str, Any]:
        """Map a GitHub PR review to a Signal node.

        Args:
            review: Raw GitHub review API response.
            repo_full_name: Repository "owner/repo".
            pull_number: PR number this review belongs to.

        Returns:
            Signal node property dict.
        """
        source_id = f"{repo_full_name}/pull/{pull_number}/review/{review['id']}"
        now = _now_iso()

        state = review.get("state", "COMMENTED")
        content_parts = []
        if state:
            content_parts.append(f"[{state}]")
        if review.get("body"):
            content_parts.append(review["body"])
        content = " ".join(content_parts)

        return {
            "node_type": "Signal",
            "id": _make_id(source_id, self.tenant_id, "gh_review"),
            "tenant_id": self.tenant_id,
            "source": "github",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": review.get("submitted_at", now),
            "updated_at": review.get("submitted_at", now),
            # Signal-specific
            "content": content,
            "signal_type": "review",
            "url": review.get("html_url", ""),
            "occurred_at": review.get("submitted_at", now),
        }
