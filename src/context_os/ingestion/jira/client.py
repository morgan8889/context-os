"""Jira Cloud REST API client for Context-OS ingest.

Uses OAuth 2.0 3LO access token from OAuthTokenRepository.
Fetches cloudId from accessible-resources on first call and caches in metadata.
Incremental sync via 'updated >= "cursor"' JQL filter.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from context_os.core.errors import RateLimitError, TokenExpiredError

logger = logging.getLogger(__name__)

JIRA_API_BASE = "https://api.atlassian.com"
ACCESSIBLE_RESOURCES_URL = f"{JIRA_API_BASE}/oauth/token/accessible-resources"


class JiraClient:
    """Jira Cloud REST API client using OAuth 2.0 token.

    Handles cloudId discovery, pagination via nextPageToken,
    and error mapping to Context-OS error types.
    """

    def __init__(
        self,
        access_token: str,
        cloud_id: str | None = None,
    ) -> None:
        """Initialize with a pre-fetched OAuth access token.

        Args:
            access_token: Jira OAuth 2.0 access token.
            cloud_id: Optional cached cloudId. If not provided, fetched on first use.
        """
        self._token = access_token
        self._cloud_id = cloud_id
        self._http = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> JiraClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._http.aclose()

    def _check_response(self, response: httpx.Response) -> None:
        """Raise appropriate errors for non-2xx responses.

        Args:
            response: HTTP response to check.

        Raises:
            TokenExpiredError: For 401 responses.
            RateLimitError: For 429 responses.
        """
        if response.status_code == 401:
            raise TokenExpiredError(
                code="token_expired",
                message="Jira OAuth token expired or invalid",
            )
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(
                code="rate_limited",
                message="Jira API rate limit exceeded",
                retry_after=retry_after,
            )
        response.raise_for_status()

    async def get_cloud_id(self) -> str:
        """Fetch and cache the Jira Cloud ID from accessible-resources.

        Returns:
            cloudId string for this Jira instance.

        Raises:
            TokenExpiredError: If the token is invalid.
            RuntimeError: If no accessible resources found.
        """
        if self._cloud_id:
            return self._cloud_id

        response = await self._http.get(ACCESSIBLE_RESOURCES_URL)
        self._check_response(response)
        resources = response.json()

        if not resources:
            raise RuntimeError("No Jira Cloud instances accessible with this token")

        self._cloud_id = resources[0]["id"]
        logger.info("Jira cloudId resolved: %s", self._cloud_id)
        return self._cloud_id

    def _jira_base(self, cloud_id: str) -> str:
        """Return the Jira Cloud API base URL for a cloudId."""
        return f"{JIRA_API_BASE}/ex/jira/{cloud_id}/rest"

    async def list_projects(
        self,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List all projects accessible to the authenticated user.

        Args:
            since: Optional datetime filter
                (client-side; Jira doesn't support it for projects).

        Returns:
            List of project objects.
        """
        cloud_id = await self.get_cloud_id()
        base = self._jira_base(cloud_id)

        all_projects: list[dict[str, Any]] = []
        start_at = 0
        max_results = 50

        while True:
            response = await self._http.get(
                f"{base}/api/3/project/search",
                params={"startAt": start_at, "maxResults": max_results},
            )
            self._check_response(response)
            data = response.json()

            projects = data.get("values", [])
            all_projects.extend(projects)

            if data.get("isLast", True) or len(projects) < max_results:
                break
            start_at += max_results

        return all_projects

    async def list_epics(
        self,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List epics via JQL search.

        Args:
            since: Optional filter for updated issues.

        Returns:
            List of epic issue objects.
        """
        jql_parts = ["issuetype = Epic"]
        if since:
            since_str = since.strftime("%Y-%m-%d %H:%M")
            jql_parts.append(f'updated >= "{since_str}"')

        jql = " AND ".join(jql_parts)
        results, _ = await self.search_issues(jql, cursor=None)
        return results

    async def search_issues(
        self,
        jql: str,
        cursor: str | None = None,
        max_results: int = 50,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Search Jira issues via JQL with nextPageToken pagination.

        Args:
            jql: JQL query string.
            cursor: Optional nextPageToken for pagination.
            max_results: Maximum results per page.

        Returns:
            Tuple of (issues_list, next_cursor). next_cursor is None if last page.
        """
        cloud_id = await self.get_cloud_id()
        base = self._jira_base(cloud_id)

        params: dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "*all",
        }
        if cursor:
            params["nextPageToken"] = cursor

        response = await self._http.get(f"{base}/agile/1.0/issue/search", params=params)
        self._check_response(response)
        data = response.json()

        issues = data.get("issues", [])
        next_cursor = data.get("nextPageToken")

        return issues, next_cursor

    async def get_user(self, account_id: str) -> dict[str, Any]:
        """Fetch a Jira user by accountId.

        Args:
            account_id: Jira Cloud account ID.

        Returns:
            User object dict.
        """
        cloud_id = await self.get_cloud_id()
        base = self._jira_base(cloud_id)

        response = await self._http.get(
            f"{base}/api/3/user",
            params={"accountId": account_id},
        )
        self._check_response(response)
        return dict(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
