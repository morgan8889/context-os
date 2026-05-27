"""Unit tests for Phase 4 auth dependencies.

TDD: These tests MUST be observed to fail before T004/T005 implementations exist.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from context_os.auth.dependencies import TenantContext


class TestRequirePlatformOperator:
    """T004: require_platform_operator() dependency."""

    @pytest.mark.asyncio
    async def test_non_po_user_gets_403(self):
        """Non-PO user calling a PO-only endpoint receives 403."""
        from context_os.auth.dependencies import require_platform_operator

        ctx = TenantContext(
            tenant_id="org_test",
            db_tenant_id=uuid.uuid4(),
            user_id="user_not_operator",
        )

        with patch("context_os.auth.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.platform_operator_clerk_user_id = (
                "user_platform_op"
            )
            with pytest.raises(HTTPException) as exc_info:
                await require_platform_operator(ctx)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "not_platform_operator"

    @pytest.mark.asyncio
    async def test_po_user_passes(self):
        """Platform Operator user ID passes the guard without raising."""
        from context_os.auth.dependencies import require_platform_operator

        po_user_id = "user_platform_op"
        ctx = TenantContext(
            tenant_id="org_test",
            db_tenant_id=uuid.uuid4(),
            user_id=po_user_id,
        )

        with patch("context_os.auth.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.platform_operator_clerk_user_id = po_user_id
            result = await require_platform_operator(ctx)

        assert result is ctx

    @pytest.mark.asyncio
    async def test_empty_po_config_always_403(self):
        """When platform_operator_clerk_user_id is unconfigured, all callers get 403."""
        from context_os.auth.dependencies import require_platform_operator

        ctx = TenantContext(
            tenant_id="org_test",
            db_tenant_id=uuid.uuid4(),
            user_id="user_platform_op",
        )

        with patch("context_os.auth.dependencies.get_settings") as mock_settings:
            mock_settings.return_value.platform_operator_clerk_user_id = ""
            with pytest.raises(HTTPException) as exc_info:
                await require_platform_operator(ctx)

        assert exc_info.value.status_code == 403


class TestImpersonationWriteBlock:
    """T005: check_not_impersonation() dependency."""

    @pytest.mark.asyncio
    async def test_write_blocked_during_impersonation(self):
        """check_not_impersonation() raises 403 when is_impersonation=True."""
        from context_os.auth.dependencies import check_not_impersonation

        ctx = TenantContext(
            tenant_id="org_target",
            db_tenant_id=uuid.uuid4(),
            user_id="user_po",
            is_impersonation=True,
        )

        with pytest.raises(HTTPException) as exc_info:
            await check_not_impersonation(ctx)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "write_blocked_during_impersonation"

    @pytest.mark.asyncio
    async def test_write_allowed_without_impersonation(self):
        """check_not_impersonation() passes when is_impersonation=False."""
        from context_os.auth.dependencies import check_not_impersonation

        ctx = TenantContext(
            tenant_id="org_normal",
            db_tenant_id=uuid.uuid4(),
            user_id="user_normal",
            is_impersonation=False,
        )

        result = await check_not_impersonation(ctx)
        assert result is ctx

    def test_tenant_context_has_is_impersonation_field(self):
        """TenantContext dataclass has is_impersonation field defaulting to False."""
        ctx = TenantContext(
            tenant_id="org_x",
            db_tenant_id=uuid.uuid4(),
            user_id="user_x",
        )
        assert ctx.is_impersonation is False
