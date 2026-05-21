"""Unit tests for impersonation JWT issue/verify/revoke.

DB session is mocked. No real database required.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest


class TestIssueImpersonationToken:
    async def test_returns_valid_hs256_jwt(self) -> None:
        """issue_impersonation_token returns a valid HS256 JWT."""
        from context_os.auth.impersonation import issue_impersonation_token

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = "a" * 64
            mock_settings.return_value = settings

            token = issue_impersonation_token("user_op_123", "org_target_456")

        claims = jwt.decode(
            token,
            "a" * 64,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        assert claims["sub"] == "user_op_123"
        assert claims["impersonating_tenant_id"] == "org_target_456"
        assert claims["impersonator"] is True
        assert "jti" in claims

    async def test_raises_when_secret_empty(self) -> None:
        """issue_impersonation_token raises RuntimeError when secret is empty."""
        from context_os.auth.impersonation import issue_impersonation_token

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = ""
            mock_settings.return_value = settings

            with pytest.raises(RuntimeError, match="impersonation_secret"):
                issue_impersonation_token("user_op_123", "org_target_456")


class TestVerifyImpersonationToken:
    async def test_returns_correct_claims(self) -> None:
        """verify_impersonation_token returns claims for a valid token."""
        from context_os.auth.impersonation import (
            issue_impersonation_token,
            verify_impersonation_token,
        )

        secret = "b" * 64
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # not revoked
        mock_db.execute.return_value = mock_result

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = secret
            mock_settings.return_value = settings

            token = issue_impersonation_token("op_user", "org_tgt")

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = secret
            mock_settings.return_value = settings

            with patch("context_os.auth.impersonation.select"):
                claims = await verify_impersonation_token(token, mock_db)

        assert claims["impersonating_tenant_id"] == "org_tgt"
        assert claims["sub"] == "op_user"

    async def test_raises_on_expired_token(self) -> None:
        """verify_impersonation_token raises on an expired token."""
        from context_os.auth.impersonation import verify_impersonation_token

        secret = "c" * 64
        # Manually craft an expired token
        past = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": "op_user",
            "impersonating_tenant_id": "org_tgt",
            "impersonator": True,
            "jti": str(uuid.uuid4()),
            "exp": int(past.timestamp()),
        }
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        mock_db = AsyncMock()

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = secret
            mock_settings.return_value = settings

            with pytest.raises(jwt.InvalidTokenError):
                await verify_impersonation_token(expired_token, mock_db)

    async def test_raises_on_revoked_jti(self) -> None:
        """verify_impersonation_token raises when the JTI is in the revoked table."""
        from context_os.auth.impersonation import (
            issue_impersonation_token,
            verify_impersonation_token,
        )
        from context_os.db.models import RevokedImpersonationToken

        secret = "d" * 64
        mock_db = AsyncMock()
        # Simulate a revoked row returned from DB
        revoked_row = MagicMock(spec=RevokedImpersonationToken)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = revoked_row
        mock_db.execute.return_value = mock_result

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = secret
            mock_settings.return_value = settings

            token = issue_impersonation_token("op_user", "org_tgt")

        with patch("context_os.auth.impersonation.get_settings") as mock_settings:
            settings = MagicMock()
            settings.impersonation_secret = secret
            mock_settings.return_value = settings

            with patch("context_os.auth.impersonation.select"):
                with pytest.raises(jwt.InvalidTokenError, match="revoked"):
                    await verify_impersonation_token(token, mock_db)


class TestRevokeImpersonationToken:
    async def test_inserts_revoked_row(self) -> None:
        """revoke_impersonation_token inserts into revoked_impersonation_tokens."""
        from context_os.auth.impersonation import revoke_impersonation_token

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        jti = str(uuid.uuid4())

        with patch(
            "context_os.auth.impersonation.RevokedImpersonationToken"
        ) as mock_cls:
            mock_row = MagicMock()
            mock_cls.return_value = mock_row

            await revoke_impersonation_token(jti, mock_db)

        mock_db.add.assert_called_once_with(mock_row)
        mock_db.flush.assert_awaited_once()
