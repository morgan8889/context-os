"""Jira Cloud API response normalizer — maps Jira objects to core ontology types.

Maps raw Jira API responses to Context-OS node property dicts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _make_id(source_id: str, tenant_id: str, prefix: str = "jira") -> str:
    """Generate a deterministic UUID from source_id + tenant_id + prefix."""
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000002")
    return str(uuid.uuid5(namespace, f"{prefix}:{tenant_id}:{source_id}"))


class JiraNomalizer:  # Note: intentional typo per task spec
    """Normalize Jira API responses to Context-OS ontology node dicts.

    Each method returns a node property dict with 'node_type' plus all
    required BaseNodeSchema fields.
    """

    def __init__(self, tenant_id: str) -> None:
        """Initialize normalizer for a specific tenant.

        Args:
            tenant_id: Clerk org ID for all produced nodes.
        """
        self.tenant_id = tenant_id

    def project_to_initiative(self, project: dict[str, Any]) -> dict[str, Any]:
        """Map a Jira project to an Initiative node.

        Args:
            project: Raw Jira project API response.

        Returns:
            Initiative node property dict.
        """
        source_id = str(project.get("id", project.get("key", "")))
        now = _now_iso()

        return {
            "node_type": "Initiative",
            "id": _make_id(source_id, self.tenant_id, "jira_project"),
            "tenant_id": self.tenant_id,
            "source": "jira",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            # Initiative-specific
            "title": project.get("name", ""),
            "description": project.get("description") or "",
            "status": "active",
            "url": project.get("self", ""),
        }

    def epic_to_goal(self, epic: dict[str, Any]) -> dict[str, Any]:
        """Map a Jira epic to a Goal node.

        Args:
            epic: Raw Jira epic issue API response.

        Returns:
            Goal node property dict.
        """
        source_id = str(epic.get("id", epic.get("key", "")))
        now = _now_iso()

        fields = epic.get("fields", {})
        status_name = ""
        if isinstance(fields.get("status"), dict):
            status_name = fields["status"].get("name", "")

        status_map = {
            "To Do": "open",
            "In Progress": "in_progress",
            "Done": "done",
        }
        status = status_map.get(status_name, "open")

        return {
            "node_type": "Goal",
            "id": _make_id(source_id, self.tenant_id, "jira_epic"),
            "tenant_id": self.tenant_id,
            "source": "jira",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": fields.get("created", now),
            "updated_at": fields.get("updated", now),
            # Goal-specific
            "title": fields.get("summary", ""),
            "description": fields.get("description") or "",
            "status": status,
            "due_date": fields.get("duedate") or "",
            "url": epic.get("self", ""),
        }

    def issue_to_signal_or_artifact(
        self,
        issue: dict[str, Any],
    ) -> dict[str, Any]:
        """Map a Jira issue to Signal (in-progress) or Artifact (done).

        Args:
            issue: Raw Jira issue API response.

        Returns:
            Signal or Artifact node property dict.
        """
        source_id = str(issue.get("id", issue.get("key", "")))
        now = _now_iso()

        fields = issue.get("fields", {})
        status_name = ""
        if isinstance(fields.get("status"), dict):
            status_name = fields["status"].get("name", "")

        is_done = status_name.lower() in ("done", "closed", "resolved", "complete")

        if is_done:
            return {
                "node_type": "Artifact",
                "id": _make_id(source_id, self.tenant_id, "jira_issue"),
                "tenant_id": self.tenant_id,
                "source": "jira",
                "source_id": source_id,
                "fetch_ts": now,
                "created_at": fields.get("created", now),
                "updated_at": fields.get("updated", now),
                # Artifact-specific
                "title": fields.get("summary", ""),
                "content": fields.get("description") or "",
                "artifact_type": "issue",
                "status": "closed",
                "url": issue.get("self", ""),
            }
        else:
            content_parts = [fields.get("summary", "")]
            if fields.get("description"):
                content_parts.append(fields["description"])
            if status_name:
                content_parts.append(f"Status: {status_name}")

            return {
                "node_type": "Signal",
                "id": _make_id(source_id, self.tenant_id, "jira_issue"),
                "tenant_id": self.tenant_id,
                "source": "jira",
                "source_id": source_id,
                "fetch_ts": now,
                "created_at": fields.get("created", now),
                "updated_at": fields.get("updated", now),
                # Signal-specific
                "content": " — ".join(filter(None, content_parts)),
                "signal_type": "status_change",
                "occurred_at": fields.get("updated", now),
                "url": issue.get("self", ""),
            }

    def user_to_actor(self, user: dict[str, Any]) -> dict[str, Any]:
        """Map a Jira user to an Actor node.

        Args:
            user: Raw Jira user API response.

        Returns:
            Actor node property dict.
        """
        source_id = str(user.get("accountId", ""))
        now = _now_iso()

        identities = [{"source": "jira", "id": source_id}]

        return {
            "node_type": "Actor",
            "id": _make_id(source_id, self.tenant_id, "jira_user"),
            "tenant_id": self.tenant_id,
            "source": "jira",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            # Actor-specific
            "name": user.get("displayName", ""),
            "email": user.get("emailAddress", ""),
            "identities": str(identities),
        }
