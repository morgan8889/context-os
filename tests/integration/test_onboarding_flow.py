"""Integration tests for the onboarding API endpoints.

Uses FastAPI TestClient with DB and auth dependencies mocked.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from context_os.auth.dependencies import TenantContext
from context_os.db.models import IngestJob, OnboardingSession


def _make_ctx(db_id: uuid.UUID | None = None) -> TenantContext:
    return TenantContext(
        tenant_id="org_test_123",
        db_tenant_id=db_id or uuid.uuid4(),
        user_id="user_test",
    )


def _make_onboarding_session(
    step: str = "survey",
    tenant_id: uuid.UUID | None = None,
    ingest_job_id: uuid.UUID | None = None,
    step_started_at: dict | None = None,
    step_completed_at: dict | None = None,
) -> MagicMock:
    session = MagicMock(spec=OnboardingSession)
    session.id = uuid.uuid4()
    session.tenant_id = tenant_id or uuid.uuid4()
    session.current_step = step
    session.survey_answer = None
    session.connected_integrations = []
    session.scope_selection = None
    session.ingest_job_id = ingest_job_id
    session.step_started_at = step_started_at or {}
    session.step_completed_at = step_completed_at or {}
    session.activated_at = None
    session.created_at = datetime.now(UTC)
    session.updated_at = datetime.now(UTC)
    return session


def _make_ingest_job(
    tenant_id: uuid.UUID | None = None,
    source: str = "all",
    status: str = "running",
) -> MagicMock:
    job = MagicMock(spec=IngestJob)
    job.id = uuid.uuid4()
    job.tenant_id = tenant_id or uuid.uuid4()
    job.source = source
    job.status = status
    job.progress_pct = 0
    job.record_counts = {}
    job.last_record_at = None
    job.started_at = datetime.now(UTC)
    job.completed_at = None
    job.error_detail = None
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    return job


@pytest.fixture
def onboarding_client():
    """TestClient for the onboarding router with auth mocked."""
    from context_os.api.onboarding import router as onboarding_router
    from context_os.auth.dependencies import get_current_tenant

    app = FastAPI()
    app.include_router(onboarding_router, prefix="/onboarding")

    db_id = uuid.uuid4()
    ctx = _make_ctx(db_id=db_id)
    app.dependency_overrides[get_current_tenant] = lambda: ctx

    return TestClient(app, raise_server_exceptions=False), ctx, db_id


class TestOnboardingSurvey:
    def test_post_survey_advances_to_connect(self, onboarding_client) -> None:
        """POST /onboarding/survey advances the session from survey to connect."""
        client, ctx, db_id = onboarding_client
        session = _make_onboarding_session(step="survey", tenant_id=db_id)
        advanced_session = _make_onboarding_session(step="connect", tenant_id=db_id)

        with (
            patch("context_os.api.onboarding.OnboardingService") as mock_svc_cls,
            patch("context_os.api.onboarding.get_session_factory") as mock_factory,
        ):
            mock_db = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = MagicMock(return_value=mock_db)

            mock_svc = MagicMock()
            mock_svc.get_or_create = AsyncMock(return_value=session)
            mock_svc.advance_step = AsyncMock(return_value=advanced_session)
            mock_svc_cls.return_value = mock_svc

            resp = client.post(
                "/onboarding/survey",
                json={"option": "briefings"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["current_step"] == "connect"


class TestOnboardingScope:
    def test_post_scope_creates_ingest_job(self, onboarding_client) -> None:
        """POST /onboarding/scope creates an IngestJob and advances to ingest."""
        client, ctx, db_id = onboarding_client
        session = _make_onboarding_session(step="connect", tenant_id=db_id)
        ingest_job = _make_ingest_job(tenant_id=db_id)
        advanced_session = _make_onboarding_session(
            step="ingest",
            tenant_id=db_id,
            ingest_job_id=ingest_job.id,
        )

        with (
            patch("context_os.api.onboarding.OnboardingService") as mock_svc_cls,
            patch("context_os.api.onboarding.IngestService") as mock_ingest_cls,
            patch("context_os.api.onboarding.get_session_factory") as mock_factory,
        ):
            mock_db = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = MagicMock(return_value=mock_db)

            mock_svc = MagicMock()
            mock_svc.get_or_create = AsyncMock(return_value=session)
            mock_svc.advance_step = AsyncMock(return_value=advanced_session)
            mock_svc_cls.return_value = mock_svc

            mock_ingest = MagicMock()
            mock_ingest.create_job = AsyncMock(return_value=ingest_job)
            mock_ingest_cls.return_value = mock_ingest

            resp = client.post(
                "/onboarding/scope",
                json={"sources": ["jira", "github"]},
            )

        assert resp.status_code == 200
        data = resp.json()
        # Should return ingest job details
        assert data["status"] == "running"


class TestOnboardingIngestStatus:
    def test_get_ingest_status_returns_job(self, onboarding_client) -> None:
        """GET /onboarding/ingest-status returns the IngestJob for the session."""
        client, ctx, db_id = onboarding_client
        ingest_job_id = uuid.uuid4()
        session = _make_onboarding_session(
            step="ingest",
            tenant_id=db_id,
            ingest_job_id=ingest_job_id,
        )
        ingest_job = _make_ingest_job(tenant_id=db_id, status="running")
        ingest_job.id = ingest_job_id

        with (
            patch("context_os.api.onboarding.OnboardingService") as mock_svc_cls,
            patch("context_os.api.onboarding.get_session_factory") as mock_factory,
            patch("context_os.api.onboarding.IngestService") as mock_ingest_cls,
        ):
            mock_db = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)

            mock_result_job = MagicMock()
            mock_result_job.scalar_one_or_none.return_value = ingest_job
            mock_db.execute = AsyncMock(return_value=mock_result_job)

            mock_factory.return_value = MagicMock(return_value=mock_db)

            mock_svc = MagicMock()
            mock_svc.get_or_create = AsyncMock(return_value=session)
            mock_svc_cls.return_value = mock_svc

            mock_ingest = MagicMock()
            mock_ingest_cls.return_value = mock_ingest

            resp = client.get("/onboarding/ingest-status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"


class TestOnboardingActivation:
    def test_post_activation_advances_and_creates_event(
        self, onboarding_client
    ) -> None:
        """POST /activation advances to activated and creates ActivationEvent."""
        client, ctx, db_id = onboarding_client
        briefing_id = uuid.uuid4()
        session = _make_onboarding_session(
            step="briefing",
            tenant_id=db_id,
            step_started_at={
                "survey": "2026-05-21T09:00:00+00:00",
                "connect": "2026-05-21T09:05:00+00:00",
                "briefing": "2026-05-21T09:30:00+00:00",
            },
            step_completed_at={
                "survey": "2026-05-21T09:01:00+00:00",
                "connect": "2026-05-21T09:10:00+00:00",
                "ingest": "2026-05-21T09:25:00+00:00",
            },
        )
        activated_session = _make_onboarding_session(
            step="activated", tenant_id=db_id
        )
        activated_session.activated_at = datetime.now(UTC)

        from context_os.db.models import ApprovalItem

        mock_briefing = MagicMock(spec=ApprovalItem)
        mock_briefing.id = briefing_id
        mock_briefing.tenant_id = ctx.tenant_id

        with (
            patch("context_os.api.onboarding.OnboardingService") as mock_svc_cls,
            patch("context_os.api.onboarding.get_session_factory") as mock_factory,
        ):
            mock_db = AsyncMock()
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            # execute calls: 1) briefing lookup, 2) activation_event check
            mock_result_briefing = MagicMock()
            mock_result_briefing.scalar_one_or_none.return_value = mock_briefing
            mock_result_event = MagicMock()
            mock_result_event.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(
                side_effect=[mock_result_briefing, mock_result_event]
            )

            mock_factory.return_value = MagicMock(return_value=mock_db)

            mock_svc = MagicMock()
            mock_svc.get_or_create = AsyncMock(return_value=session)
            mock_svc.advance_step = AsyncMock(return_value=activated_session)
            mock_svc_cls.return_value = mock_svc

            resp = client.post(
                "/onboarding/activation",
                json={"briefing_id": str(briefing_id), "accepted_as_is": True},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["current_step"] == "activated"
