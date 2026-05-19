"""Slack API client for Context-OS ingest.

Uses bot token (xoxb-) with channels:history scope.
Incremental sync via 'oldest' Unix timestamp cursor.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from context_os.core.errors import RateLimitError, TokenExpiredError

logger = logging.getLogger(__name__)

SLACK_API_BASE = "https://slack.com/api"


class SlackClient:
    """Slack API client using a bot token.

    Handles conversations.history pagination, users.info lookup,
    and error mapping to Context-OS error types.
    """

    def __init__(self, bot_token: str) -> None:
        """Initialize with a Slack bot token.

        Args:
            bot_token: Slack bot token starting with 'xoxb-'.
        """
        self._token = bot_token
        self._http = httpx.AsyncClient(
            base_url=SLACK_API_BASE,
            headers={
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> SlackClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._http.aclose()

    def _check_response(self, data: dict[str, Any], headers: httpx.Headers) -> None:
        """Check Slack API response for errors.

        Slack always returns 200 with ok=true/false. Check for auth errors
        and rate limits in the response body and headers.

        Args:
            data: Parsed JSON response body.
            headers: HTTP response headers.

        Raises:
            TokenExpiredError: For invalid_auth or token_revoked errors.
            RateLimitError: For rate_limited errors.
        """
        if not data.get("ok", False):
            error = data.get("error", "unknown_error")
            if error in (
                "invalid_auth",
                "token_revoked",
                "not_authed",
                "account_inactive",
            ):
                raise TokenExpiredError(
                    code="token_expired",
                    message=f"Slack bot token invalid or revoked: {error}",
                )
            if error == "ratelimited":
                retry_after = int(headers.get("Retry-After", "1"))
                raise RateLimitError(
                    code="rate_limited",
                    message="Slack API rate limit exceeded",
                    retry_after=retry_after,
                )
            # Log other errors but don't raise (Slack has many soft errors)
            logger.warning("Slack API error: %s", error)

    async def list_messages(
        self,
        channel_id: str,
        oldest: str | None = None,
        limit: int = 200,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch messages from a Slack channel.

        Uses conversations.history with cursor-based pagination and 'oldest'
        for incremental sync. The newest message's ts should be stored as
        the next 'oldest' cursor.

        Args:
            channel_id: Slack channel ID (e.g. "C0123ABCDEF").
            oldest: Unix timestamp string — fetch messages after this time.
            limit: Maximum messages per API call.

        Returns:
            Tuple of (messages_list, next_cursor).
            next_cursor is None if there are no more pages.
        """
        params: dict[str, Any] = {
            "channel": channel_id,
            "limit": limit,
        }
        if oldest:
            params["oldest"] = oldest

        response = await self._http.get("/conversations.history", params=params)
        response.raise_for_status()
        data = response.json()

        self._check_response(data, response.headers)

        messages = data.get("messages", [])
        next_cursor: str | None = None

        if data.get("has_more"):
            next_cursor = data.get("response_metadata", {}).get("next_cursor")

        return messages, next_cursor

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Fetch a Slack user by user ID.

        Args:
            user_id: Slack user ID (e.g. "U0123ABCDEF").

        Returns:
            User object dict or None if not found.
        """
        response = await self._http.get(
            "/users.info",
            params={"user": user_id},
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            error = data.get("error", "")
            if error in ("user_not_found", "no_user_provided"):
                return None
            self._check_response(data, response.headers)

        return data.get("user")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
