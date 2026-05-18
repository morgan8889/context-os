"""Context-OS CLI for graph management, tenant administration, and ingest.

Commands:
    graph init            — Create the AGE graph
    tenant create         — Register a new tenant
    auth github           — Store GitHub App installation token
    auth jira             — OAuth 2.0 3LO flow for Jira
    auth slack            — Store Slack bot token
    ingest github|jira|slack|all — Run ingest for one or all sources
"""

from __future__ import annotations

import asyncio
import logging
import uuid

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="context-os",
    help="Context-OS management CLI",
    no_args_is_help=True,
)

graph_app = typer.Typer(help="Graph management commands")
tenant_app = typer.Typer(help="Tenant management commands")
auth_app = typer.Typer(help="OAuth token management commands")
ingest_app = typer.Typer(help="Data ingest commands")

app.add_typer(graph_app, name="graph")
app.add_typer(tenant_app, name="tenant")
app.add_typer(auth_app, name="auth")
app.add_typer(ingest_app, name="ingest")


def _load_settings() -> object:
    """Load application settings, printing a helpful error on failure."""
    try:
        from context_os.config import get_settings

        return get_settings()
    except Exception as e:
        typer.echo(f"Error loading settings: {e}", err=True)
        typer.echo(
            "Ensure .env file exists and all required variables are set.", err=True
        )
        raise typer.Exit(1) from e


# ── Graph commands ─────────────────────────────────────────────────────────────


@graph_app.command("init")
def graph_init() -> None:
    """Initialize the AGE property graph 'context_os'."""

    async def _init() -> None:
        from context_os.graph.client import close_age_pool, create_age_pool, init_graph

        typer.echo("Connecting to database...")
        pool = await create_age_pool()
        try:
            await init_graph(pool)
            typer.echo("Graph 'context_os' initialized successfully.")
        finally:
            await close_age_pool()

    _load_settings()
    asyncio.run(_init())


# ── Tenant commands ────────────────────────────────────────────────────────────


@tenant_app.command("create")
def tenant_create(
    clerk_org_id: str = typer.Option(
        ..., "--clerk-org-id", help="Clerk organization ID"
    ),
    name: str = typer.Option(..., "--name", help="Organization name"),
) -> None:
    """Register a new tenant in the database."""

    async def _create() -> None:
        from context_os.db.engine import close_db, get_session_factory, init_db
        from context_os.relational.repositories import TenantRepository

        await init_db()
        try:
            factory = get_session_factory()
            async with factory() as session:
                repo = TenantRepository(session)

                # Check if already exists
                existing = await repo.get_by_clerk_org_id(clerk_org_id)
                if existing:
                    typer.echo(f"Tenant already exists: {existing.id}")
                    return

                tenant = await repo.create(clerk_org_id=clerk_org_id, name=name)
                await session.commit()
                typer.echo(f"Tenant created: {tenant.id}")
        finally:
            await close_db()

    _load_settings()
    asyncio.run(_create())


# ── Auth commands ──────────────────────────────────────────────────────────────


@auth_app.command("github")
def auth_github(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
) -> None:
    """Generate and store a GitHub App installation access token."""

    async def _auth() -> None:
        from context_os.config import get_settings
        from context_os.db.engine import close_db, get_session_factory, init_db
        from context_os.ingestion.github.client import get_installation_token
        from context_os.relational.repositories import OAuthTokenRepository

        settings = get_settings()

        if not settings.github_app_id or not settings.github_installation_id:
            typer.echo(
                "GITHUB_APP_ID and GITHUB_INSTALLATION_ID must be set in .env", err=True
            )
            raise typer.Exit(1)

        typer.echo(
            f"Generating GitHub installation token for app {settings.github_app_id}..."
        )

        await init_db()
        try:
            token = await get_installation_token(
                app_id=settings.github_app_id,
                private_key_path=settings.github_app_private_key_path,
                installation_id=settings.github_installation_id,
            )

            factory = get_session_factory()
            async with factory() as session:
                repo = OAuthTokenRepository(session)
                await repo.upsert(
                    tenant_id=tenant_id,
                    integration="github",
                    access_token=token,
                    metadata={"installation_id": settings.github_installation_id},
                )
                await session.commit()

            typer.echo("GitHub token stored successfully.")
        finally:
            await close_db()

    _load_settings()
    asyncio.run(_auth())


@auth_app.command("jira")
def auth_jira(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
) -> None:
    """OAuth 2.0 3LO flow for Jira Cloud (interactive)."""

    async def _auth() -> None:
        import urllib.parse

        from context_os.config import get_settings
        from context_os.db.engine import close_db, get_session_factory, init_db
        from context_os.relational.repositories import OAuthTokenRepository

        settings = get_settings()

        if not settings.jira_client_id or not settings.jira_client_secret:
            typer.echo(
                "JIRA_CLIENT_ID and JIRA_CLIENT_SECRET must be set in .env", err=True
            )
            raise typer.Exit(1)

        # Build authorization URL
        redirect_uri = "https://localhost/callback"
        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.jira_client_id,
            "scope": "read:jira-work read:jira-user offline_access",
            "redirect_uri": redirect_uri,
            "state": str(uuid.uuid4()),
            "response_type": "code",
            "prompt": "consent",
        }
        auth_url = "https://auth.atlassian.com/authorize?" + urllib.parse.urlencode(
            params
        )

        typer.echo("\nOpen this URL in your browser to authorize:")
        typer.echo(auth_url)
        typer.echo(
            "\nAfter authorizing, paste the 'code' parameter from the redirect URL:"
        )
        code = typer.prompt("Authorization code")

        # Exchange code for tokens
        import httpx

        async with httpx.AsyncClient() as http:
            response = await http.post(
                "https://auth.atlassian.com/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": settings.jira_client_id,
                    "client_secret": settings.jira_client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            token_data = response.json()

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")

        # Fetch cloudId
        async with httpx.AsyncClient() as http:
            resources_resp = await http.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resources_resp.raise_for_status()
            resources = resources_resp.json()

        cloud_id = resources[0]["id"] if resources else None
        cloud_name = resources[0].get("name", "unknown") if resources else "unknown"
        typer.echo(f"Connected to Jira Cloud: {cloud_name} ({cloud_id})")

        await init_db()
        try:
            factory = get_session_factory()
            async with factory() as session:
                repo = OAuthTokenRepository(session)
                await repo.upsert(
                    tenant_id=tenant_id,
                    integration="jira",
                    access_token=access_token,
                    refresh_token=refresh_token,
                    metadata={"cloud_id": cloud_id},
                )
                await session.commit()

            typer.echo("Jira token stored successfully.")
        finally:
            await close_db()

    _load_settings()
    asyncio.run(_auth())


@auth_app.command("slack")
def auth_slack(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
    token: str = typer.Option(..., "--token", help="Slack bot token (xoxb-...)"),
) -> None:
    """Store a Slack bot token for the tenant."""

    async def _auth() -> None:
        from context_os.db.engine import close_db, get_session_factory, init_db
        from context_os.relational.repositories import OAuthTokenRepository

        if not token.startswith("xoxb-"):
            typer.echo("Warning: Slack bot tokens should start with 'xoxb-'", err=True)

        await init_db()
        try:
            factory = get_session_factory()
            async with factory() as session:
                repo = OAuthTokenRepository(session)
                await repo.upsert(
                    tenant_id=tenant_id,
                    integration="slack",
                    access_token=token,
                )
                await session.commit()

            typer.echo("Slack token stored successfully.")
        finally:
            await close_db()

    _load_settings()
    asyncio.run(_auth())


# ── Ingest commands ────────────────────────────────────────────────────────────


def _run_ingest_command(
    source: str,
    tenant_id: uuid.UUID,
    full: bool = False,
) -> None:
    """Run ingest for a single source or all sources."""

    async def _ingest() -> None:
        from context_os.auth.dependencies import TenantContext
        from context_os.db.engine import close_db, get_session_factory, init_db
        from context_os.graph.client import close_age_pool, create_age_pool, init_graph
        from context_os.relational.repositories import TenantRepository

        await init_db()
        pool = await create_age_pool()
        await init_graph(pool)

        try:
            factory = get_session_factory()
            async with factory() as session:
                repo = TenantRepository(session)
                tenant = await repo.get_by_id(tenant_id)

            if tenant is None:
                typer.echo(f"Tenant not found: {tenant_id}", err=True)
                raise typer.Exit(1)

            tenant_ctx = TenantContext(
                tenant_id=tenant.clerk_org_id,
                db_tenant_id=tenant.id,
            )

            sources = ["github", "jira", "slack"] if source == "all" else [source]

            for src in sources:
                typer.echo(f"Running {src} ingest for tenant {tenant_id}...")
                try:
                    from context_os.api.ingest import run_ingest

                    result = await run_ingest(
                        integration=src,
                        tenant_ctx=tenant_ctx,
                        full=full,
                    )
                    typer.echo(
                        f"  {src}: status={result.status} "
                        f"records={result.records_processed or 0} "
                        f"checkpoint={result.checkpoint}"
                    )
                except Exception as e:
                    typer.echo(f"  {src} ingest failed: {e}", err=True)
        finally:
            await close_age_pool()
            await close_db()

    asyncio.run(_ingest())


@ingest_app.command("github")
def ingest_github(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
    full: bool = typer.Option(
        False, "--full", help="Full re-ingest (ignore checkpoint)"
    ),
) -> None:
    """Run GitHub ingest for the specified tenant."""
    _load_settings()
    _run_ingest_command("github", tenant_id, full)


@ingest_app.command("jira")
def ingest_jira(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
    full: bool = typer.Option(
        False, "--full", help="Full re-ingest (ignore checkpoint)"
    ),
) -> None:
    """Run Jira ingest for the specified tenant."""
    _load_settings()
    _run_ingest_command("jira", tenant_id, full)


@ingest_app.command("slack")
def ingest_slack(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
    full: bool = typer.Option(
        False, "--full", help="Full re-ingest (ignore checkpoint)"
    ),
) -> None:
    """Run Slack ingest for the specified tenant."""
    _load_settings()
    _run_ingest_command("slack", tenant_id, full)


@ingest_app.command("all")
def ingest_all(
    tenant_id: uuid.UUID = typer.Option(..., "--tenant-id", help="Tenant UUID"),
    full: bool = typer.Option(
        False, "--full", help="Full re-ingest (ignore checkpoint)"
    ),
) -> None:
    """Run ingest for all configured sources (github, jira, slack)."""
    _load_settings()
    _run_ingest_command("all", tenant_id, full)


if __name__ == "__main__":
    app()
