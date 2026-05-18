"""Application configuration loaded from environment variables.

Fail-fast: missing required variables raise a clear ValidationError on startup.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="PostgreSQL asyncpg connection URL",
    )

    # ── Clerk Authentication ───────────────────────────────────────────────────
    clerk_secret_key: str = Field(
        ...,
        description="Clerk secret key (sk_test_... or sk_live_...)",
    )
    clerk_publishable_key: str = Field(
        ...,
        description="Clerk publishable key (pk_test_... or pk_live_...)",
    )

    # ── Langfuse Observability ─────────────────────────────────────────────────
    langfuse_public_key: str = Field(
        ...,
        description="Langfuse project public key",
    )
    langfuse_secret_key: str = Field(
        ...,
        description="Langfuse project secret key",
    )
    langfuse_host: str = Field(
        default="http://localhost:3000",
        description="Langfuse instance URL",
    )

    # ── Token Encryption ───────────────────────────────────────────────────────
    encryption_key: str = Field(
        ...,
        description="Fernet AES-256 key for OAuth token encryption at rest",
    )

    # ── GitHub App ─────────────────────────────────────────────────────────────
    github_app_id: str = Field(
        default="",
        description="GitHub App numeric ID",
    )
    github_app_private_key_path: str = Field(
        default="./secrets/github-app.pem",
        description="Path to GitHub App private key PEM file",
    )
    github_installation_id: str = Field(
        default="",
        description="GitHub App installation ID",
    )

    # ── Jira Cloud OAuth 2.0 ──────────────────────────────────────────────────
    jira_client_id: str = Field(
        default="",
        description="Jira Cloud OAuth 2.0 client ID",
    )
    jira_client_secret: str = Field(
        default="",
        description="Jira Cloud OAuth 2.0 client secret",
    )

    # ── Slack ──────────────────────────────────────────────────────────────────
    slack_bot_token: str = Field(
        default="",
        description="Slack bot token (xoxb-...)",
    )
    slack_channel_ids: str = Field(
        default="",
        description="Comma-separated Slack channel IDs to ingest",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_version: str = Field(
        default="0.1.0",
        description="Application semver for OTEL resource attributes",
    )

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Ensure encryption key is non-empty (Fernet validates format at use time)."""
        if not v or not v.strip():
            raise ValueError(
                "ENCRYPTION_KEY is required. Generate with: "
                'python -c "from cryptography.fernet import Fernet;'
                ' print(Fernet.generate_key().decode())"'
            )
        return v

    @property
    def slack_channel_ids_list(self) -> list[str]:
        """Return Slack channel IDs as a list, filtering empty strings."""
        if not self.slack_channel_ids:
            return []
        return [ch.strip() for ch in self.slack_channel_ids.split(",") if ch.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton.

    Raises:
        pydantic_settings.ValidationError: If any required env variable is missing.
    """
    return Settings()  # type: ignore[call-arg]
