"""Slack API response normalizer — maps Slack objects to core ontology types.

Extracts GitHub PR references from message text and records pending
cross-source REFERENCES edges with resolved=false.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def _make_id(source_id: str, tenant_id: str, prefix: str = "slack") -> str:
    """Generate a deterministic UUID from source_id + tenant_id + prefix."""
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000003")
    return str(uuid.uuid5(namespace, f"{prefix}:{tenant_id}:{source_id}"))


def _ts_to_iso(ts: str) -> str:
    """Convert a Slack Unix timestamp string to ISO 8601.

    Slack timestamps are Unix time with microsecond precision
    (e.g. "1716012345.678901").

    Args:
        ts: Slack timestamp string.

    Returns:
        ISO 8601 datetime string.
    """
    try:
        # ts is "seconds.microseconds"
        timestamp_float = float(ts)
        dt = datetime.fromtimestamp(timestamp_float, tz=UTC)
        return dt.isoformat()
    except (ValueError, OSError):
        return _now_iso()


# Regex for GitHub PR URLs in Slack messages
_GITHUB_PR_REGEX = re.compile(
    r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+",
    re.IGNORECASE,
)


class SlackNormalizer:
    """Normalize Slack API responses to Context-OS ontology node dicts."""

    def __init__(self, tenant_id: str) -> None:
        """Initialize normalizer for a specific tenant.

        Args:
            tenant_id: Clerk org ID for all produced nodes.
        """
        self.tenant_id = tenant_id

    def message_to_signal(
        self,
        msg: dict[str, Any],
        channel_id: str,
    ) -> dict[str, Any]:
        """Map a Slack message to a Signal node.

        Args:
            msg: Raw Slack message object from conversations.history.
            channel_id: Channel ID the message was fetched from.

        Returns:
            Signal node property dict.
        """
        ts = msg.get("ts", "")
        source_id = f"{channel_id}:{ts}"
        now = _now_iso()
        occurred_at = _ts_to_iso(ts) if ts else now

        return {
            "node_type": "Signal",
            "id": _make_id(source_id, self.tenant_id, "slack_msg"),
            "tenant_id": self.tenant_id,
            "source": "slack",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": occurred_at,
            "updated_at": occurred_at,
            # Signal-specific
            "content": msg.get("text", ""),
            "signal_type": "message",
            "occurred_at": occurred_at,
            "url": "",  # Slack deep links require workspace slug, omit for now
        }

    def user_to_actor(self, user: dict[str, Any]) -> dict[str, Any]:
        """Map a Slack user to an Actor node.

        Args:
            user: Raw Slack user object from users.info.

        Returns:
            Actor node property dict.
        """
        source_id = str(user.get("id", ""))
        now = _now_iso()

        profile = user.get("profile", {})
        email = profile.get("email", "")
        name = (
            user.get("real_name", "")
            or profile.get("display_name", "")
            or user.get("name", "")
        )

        identities = [{"source": "slack", "id": source_id}]

        return {
            "node_type": "Actor",
            "id": _make_id(source_id, self.tenant_id, "slack_user"),
            "tenant_id": self.tenant_id,
            "source": "slack",
            "source_id": source_id,
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            # Actor-specific
            "name": name,
            "email": email,
            "identities": str(identities),
        }

    def extract_github_pr_refs(self, text: str) -> list[str]:
        """Extract GitHub PR URLs from a Slack message text.

        Used to create pending REFERENCES edges between Slack Signal nodes
        and GitHub Artifact nodes that may not yet be in the graph.

        Args:
            text: Slack message text content.

        Returns:
            List of GitHub PR URLs found in the text.
        """
        if not text:
            return []
        return _GITHUB_PR_REGEX.findall(text)
