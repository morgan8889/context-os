"""GitHub App installation client for Context-OS ingest.

Uses GitHub App installation access tokens (JWT-signed, exchanged for
installation tokens) rather than OAuth App tokens. This provides fine-grained
permissions and 15K req/hr rate limits not tied to individual users.

Pagination: Link: rel="next" header traversal with max page=100.
Incremental: 'since' ISO 8601 filter on updated_at for issues/PRs.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

import httpx
import jwt as pyjwt

from context_os.core.errors import RateLimitError, TokenExpiredError

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """GitHub REST API client using App installation tokens.

    Handles JWT generation, installation token exchange, pagination,
    and error mapping to Context-OS error types.
    """

    def __init__(self, access_token: str) -> None:
        """Initialize with a pre-fetched installation access token.

        Args:
            access_token: GitHub installation access token (starts with "ghs_").
        """
        self._token = access_token
        self._http = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> GitHubClient:
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
            httpx.HTTPStatusError: For other error responses.
        """
        if response.status_code == 401:
            raise TokenExpiredError(
                code="token_expired",
                message="GitHub installation token expired or invalid",
            )
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(
                code="rate_limited",
                message="GitHub API rate limit exceeded",
                retry_after=retry_after,
            )
        response.raise_for_status()

    async def _paginate(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all pages from a GitHub API endpoint via Link header pagination.

        Args:
            url: Initial URL (relative to base or absolute).
            params: Query parameters for the first request.

        Returns:
            Concatenated list of all items across all pages.
        """
        all_items: list[dict[str, Any]] = []
        next_url: str | None = url

        while next_url:
            if next_url.startswith("https://"):
                p = params if all_items == [] else None
                response = await self._http.get(next_url, params=p)
            else:
                p = params if not all_items else None
                response = await self._http.get(next_url, params=p)

            self._check_response(response)
            data = response.json()

            if isinstance(data, list):
                all_items.extend(data)
            elif isinstance(data, dict) and "items" in data:
                all_items.extend(data["items"])

            # Follow Link: rel="next" header
            link_header = response.headers.get("Link", "")
            next_url = _parse_next_link(link_header)
            params = None  # Params are encoded in the next URL

        return all_items

    async def list_repos(
        self,
        since: datetime | None = None,
        installation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List repositories accessible to the installation.

        Args:
            since: Optional datetime filter (not directly supported for repos,
                   used for filtering by pushed_at client-side).
            installation_id: Installation ID (uses config if not provided).

        Returns:
            List of repository objects.
        """
        items = await self._paginate(
            "/installation/repositories",
            params={"per_page": 100},
        )
        repos = items

        if since:
            since_str = since.isoformat()
            repos = [
                r
                for r in repos
                if (
                    r.get("pushed_at", "") >= since_str
                    or r.get("updated_at", "") >= since_str
                )
            ]

        return repos

    async def list_milestones(
        self,
        repo_full_name: str,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List milestones for a repository.

        Args:
            repo_full_name: "owner/repo" format.
            since: Optional filter by updated_at.

        Returns:
            List of milestone objects.
        """
        owner, repo = repo_full_name.split("/", 1)
        params: dict[str, Any] = {"per_page": 100, "state": "all"}
        items = await self._paginate(f"/repos/{owner}/{repo}/milestones", params=params)

        if since:
            since_str = since.isoformat()
            items = [m for m in items if m.get("updated_at", "") >= since_str]

        return items

    async def list_pulls(
        self,
        repo_full_name: str,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List pull requests for a repository.

        Args:
            repo_full_name: "owner/repo" format.
            since: Optional filter — PRs updated after this datetime.

        Returns:
            List of pull request objects.
        """
        owner, repo = repo_full_name.split("/", 1)
        params: dict[str, Any] = {
            "per_page": 100,
            "state": "all",
            "sort": "updated",
            "direction": "desc",
        }

        if since:
            params["since"] = since.isoformat()

        return await self._paginate(f"/repos/{owner}/{repo}/pulls", params=params)

    async def list_issues(
        self,
        repo_full_name: str,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """List issues for a repository (excludes PRs by filter).

        Args:
            repo_full_name: "owner/repo" format.
            since: Optional filter — issues updated after this datetime.

        Returns:
            List of issue objects (excluding pull requests).
        """
        owner, repo = repo_full_name.split("/", 1)
        params: dict[str, Any] = {
            "per_page": 100,
            "state": "all",
            "sort": "updated",
            "direction": "desc",
        }

        if since:
            params["since"] = since.isoformat()

        items = await self._paginate(f"/repos/{owner}/{repo}/issues", params=params)
        # Filter out PRs (they appear in the issues endpoint too)
        return [i for i in items if "pull_request" not in i]

    async def list_pull_reviews(
        self,
        repo_full_name: str,
        pull_number: int,
    ) -> list[dict[str, Any]]:
        """List reviews for a pull request.

        Args:
            repo_full_name: "owner/repo" format.
            pull_number: PR number.

        Returns:
            List of review objects.
        """
        owner, repo = repo_full_name.split("/", 1)
        return await self._paginate(
            f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
            params={"per_page": 100},
        )

    async def get_user(self, login: str) -> dict[str, Any]:
        """Fetch a GitHub user by login.

        Args:
            login: GitHub username.

        Returns:
            User object dict.
        """
        response = await self._http.get(f"/users/{login}")
        self._check_response(response)
        return dict(response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()


def _parse_next_link(link_header: str) -> str | None:
    """Extract the 'next' URL from a GitHub Link header.

    Example header:
        <https://api.github.com/repos/...?page=2>; rel="next",
        <https://api.github.com/repos/...?page=5>; rel="last"

    Args:
        link_header: Raw Link header string.

    Returns:
        Next page URL or None if no next page.
    """
    if not link_header:
        return None

    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            # Extract URL between < and >
            start = part.find("<") + 1
            end = part.find(">")
            if start > 0 and end > start:
                return part[start:end]
    return None


def generate_github_app_jwt(app_id: str, private_key_path: str) -> str:
    """Generate a GitHub App JWT for installation token exchange.

    The JWT is signed with RS256 and valid for 10 minutes.

    Args:
        app_id: GitHub App numeric ID.
        private_key_path: Path to the PEM private key file.

    Returns:
        Signed JWT string.
    """
    with open(private_key_path, "rb") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,  # issued at (60s in past for clock skew)
        "exp": now + 540,  # expires in 9 minutes (max 10 min)
        "iss": app_id,
    }

    return pyjwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_token(
    app_id: str,
    private_key_path: str,
    installation_id: str,
) -> str:
    """Exchange a GitHub App JWT for an installation access token.

    Args:
        app_id: GitHub App numeric ID.
        private_key_path: Path to the PEM private key file.
        installation_id: GitHub App installation ID.

    Returns:
        Installation access token string (starts with "ghs_").
    """
    app_jwt = generate_github_app_jwt(app_id, private_key_path)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        if response.status_code == 401:
            raise TokenExpiredError(
                code="token_expired",
                message="GitHub App JWT invalid or expired",
            )
        response.raise_for_status()

        data = response.json()
        token: str = data["token"]
        return token
