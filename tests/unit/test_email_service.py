"""Unit tests for EmailService.notify_ingest_complete().

All HTTP calls are mocked — no real Resend API is called.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch


class TestEmailServiceNotifyIngestComplete:
    """notify_ingest_complete() behaviour tests."""

    async def test_sends_correct_subject(self) -> None:
        """Subject contains initiative count from record_counts."""
        from context_os.services.email_service import EmailService

        counts = {"initiatives": 7, "decisions": 2}
        tenant_id = uuid.uuid4()
        recipient = "admin@example.com"

        captured: list[dict] = []

        async def _fake_post(url: str, **kwargs) -> MagicMock:  # type: ignore[return]
            captured.append({"url": url, **kwargs})
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp

        with (
            patch("context_os.services.email_service.get_settings") as mock_settings,
            patch("httpx.AsyncClient.post", side_effect=_fake_post),
        ):
            settings = MagicMock()
            settings.resend_api_key = "re_test_key"
            settings.resend_from_email = "noreply@contextops.ai"
            mock_settings.return_value = settings

            svc = EmailService()
            await svc.notify_ingest_complete(tenant_id, recipient, counts)

        assert len(captured) == 1
        payload = captured[0]["json"]
        assert "7 initiatives found" in payload["subject"]

    async def test_sends_to_correct_recipient(self) -> None:
        """Email is addressed to the given recipient."""
        from context_os.services.email_service import EmailService

        counts = {"initiatives": 3}
        tenant_id = uuid.uuid4()
        recipient = "user@acme.com"

        captured: list[dict] = []

        async def _fake_post(url: str, **kwargs) -> MagicMock:  # type: ignore[return]
            captured.append({"url": url, **kwargs})
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp

        with (
            patch("context_os.services.email_service.get_settings") as mock_settings,
            patch("httpx.AsyncClient.post", side_effect=_fake_post),
        ):
            settings = MagicMock()
            settings.resend_api_key = "re_test_key"
            settings.resend_from_email = "noreply@contextops.ai"
            mock_settings.return_value = settings

            svc = EmailService()
            await svc.notify_ingest_complete(tenant_id, recipient, counts)

        payload = captured[0]["json"]
        assert payload["to"] == [recipient]

    async def test_payload_includes_record_counts(self) -> None:
        """HTML body includes record_count summary data."""
        from context_os.services.email_service import EmailService

        counts = {"initiatives": 5, "decisions": 1, "signals": 12}
        tenant_id = uuid.uuid4()
        recipient = "ops@example.com"

        captured: list[dict] = []

        async def _fake_post(url: str, **kwargs) -> MagicMock:  # type: ignore[return]
            captured.append({"url": url, **kwargs})
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            return resp

        with (
            patch("context_os.services.email_service.get_settings") as mock_settings,
            patch("httpx.AsyncClient.post", side_effect=_fake_post),
        ):
            settings = MagicMock()
            settings.resend_api_key = "re_test_key"
            settings.resend_from_email = "noreply@contextops.ai"
            mock_settings.return_value = settings

            svc = EmailService()
            await svc.notify_ingest_complete(tenant_id, recipient, counts)

        payload = captured[0]["json"]
        html_body: str = payload["html"]
        assert "5" in html_body  # initiative count present in body
        assert "initiatives" in html_body.lower()

    async def test_no_resend_call_when_api_key_is_none(self) -> None:
        """When resend_api_key is None, no HTTP call is made (silent no-op)."""
        from context_os.services.email_service import EmailService

        counts = {"initiatives": 4}
        tenant_id = uuid.uuid4()

        post_mock = AsyncMock()

        with (
            patch("context_os.services.email_service.get_settings") as mock_settings,
            patch("httpx.AsyncClient.post", post_mock),
        ):
            settings = MagicMock()
            settings.resend_api_key = None
            mock_settings.return_value = settings

            svc = EmailService()
            await svc.notify_ingest_complete(tenant_id, "any@example.com", counts)

        post_mock.assert_not_called()
