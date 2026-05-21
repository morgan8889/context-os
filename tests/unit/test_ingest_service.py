"""Unit tests for IngestService.

DB session is mocked — no real database required.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from context_os.db.models import IngestJob


def _make_job(
    tenant_id: uuid.UUID | None = None,
    source: str = "all",
    status: str = "running",
    progress_pct: int = 0,
    record_counts: dict | None = None,
    last_record_at: datetime | None = None,
    started_at: datetime | None = None,
) -> IngestJob:
    """Build a minimal IngestJob ORM mock."""
    job = MagicMock(spec=IngestJob)
    job.id = uuid.uuid4()
    job.tenant_id = tenant_id or uuid.uuid4()
    job.source = source
    job.status = status
    job.progress_pct = progress_pct
    job.record_counts = record_counts or {}
    job.last_record_at = last_record_at
    job.started_at = started_at or datetime.now(UTC)
    job.completed_at = None
    job.error_detail = None
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    return job


class TestIngestServiceCreateJob:
    async def test_create_job_returns_running_job(self) -> None:
        """create_job persists a new IngestJob with status='running'."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)
        tenant_id = uuid.uuid4()

        created_job = _make_job(tenant_id=tenant_id, source="all", status="running")

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "context_os.services.ingest_service.IngestJob",
            return_value=created_job,
        ):
            with patch("context_os.services.ingest_service.select"):
                job = await svc.create_job(tenant_id, "all")

        assert job.status == "running"
        assert job.source == "all"


class TestIngestServiceUpdateProgress:
    async def test_update_progress_sets_fields(self) -> None:
        """update_progress sets progress_pct, record_counts, and last_record_at."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)

        job = _make_job()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db.execute.return_value = mock_result

        with patch("context_os.services.ingest_service.select"):
            updated = await svc.update_progress(job.id, 50, {"initiatives": 10})

        assert updated.progress_pct == 50
        assert updated.record_counts == {"initiatives": 10}
        assert updated.last_record_at is not None


class TestIngestServiceMarkComplete:
    async def test_mark_complete_sets_status_and_completed_at(self) -> None:
        """mark_complete transitions status to 'completed' with a timestamp."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)

        job = _make_job()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db.execute.return_value = mock_result

        with (
            patch("context_os.services.ingest_service.select"),
            patch(
                "context_os.services.ingest_service.EmailService"
            ) as mock_email_cls,
            patch(
                "context_os.services.ingest_service.OnboardingService"
            ) as mock_onboarding_cls,
        ):
            mock_email_cls.return_value.notify_ingest_complete = AsyncMock()
            mock_onboarding_cls.return_value.advance_step = AsyncMock()

            # Stub out the onboarding session lookup
            mock_session_result = MagicMock()
            mock_session_result.scalar_one_or_none.return_value = None
            mock_db.execute.side_effect = [
                mock_result,           # job lookup
                mock_session_result,   # onboarding session lookup
            ]

            updated = await svc.mark_complete(job.id)

        assert updated.status == "completed"
        assert updated.completed_at is not None


class TestIngestServiceMarkStalled:
    async def test_mark_stalled_sets_status(self) -> None:
        """mark_stalled transitions status to 'stalled'."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)

        job = _make_job()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db.execute.return_value = mock_result

        with patch("context_os.services.ingest_service.select"):
            updated = await svc.mark_stalled(job.id)

        assert updated.status == "stalled"


class TestIngestServiceIsStalled:
    async def test_is_stalled_returns_true_when_stalled(self) -> None:
        """is_stalled returns True when last_record_at < now()-2h AND status=running."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)

        stale_time = datetime.now(UTC) - timedelta(hours=3)
        job = _make_job(status="running", last_record_at=stale_time)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db.execute.return_value = mock_result

        with patch("context_os.services.ingest_service.select"):
            result = await svc.is_stalled(job.id)

        assert result is True

    async def test_is_stalled_returns_false_when_recent(self) -> None:
        """is_stalled returns False when last_record_at is recent."""
        from context_os.services.ingest_service import IngestService

        mock_db = AsyncMock()
        svc = IngestService(mock_db)

        recent_time = datetime.now(UTC) - timedelta(minutes=30)
        job = _make_job(status="running", last_record_at=recent_time)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = job
        mock_db.execute.return_value = mock_result

        with patch("context_os.services.ingest_service.select"):
            result = await svc.is_stalled(job.id)

        assert result is False
