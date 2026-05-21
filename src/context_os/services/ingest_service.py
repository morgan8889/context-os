"""IngestService: lifecycle management for IngestJob records.

Status transitions: running → completed | stalled | failed

On mark_complete:
  - Calls EmailService.notify_ingest_complete (best-effort)
  - Calls OnboardingService.advance_step to 'briefing' (best-effort)
  - Updates Prometheus gauge for last_record_at
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

from opentelemetry import metrics
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.db.models import IngestJob, OnboardingSession
from context_os.services.email_service import EmailService
from context_os.services.onboarding_service import OnboardingService

logger = logging.getLogger(__name__)

# Prometheus / OTEL gauge for last ingested record timestamp
_meter = metrics.get_meter("context_os")
_last_record_gauge = _meter.create_gauge(
    "context_os_ingest_last_record_at",
    description="Unix timestamp of last ingested record per tenant and source",
)

_STALL_THRESHOLD = timedelta(hours=2)


class JobNotFoundError(Exception):
    """Raised when an IngestJob with the given ID does not exist."""

    def __init__(self, job_id: uuid.UUID) -> None:
        super().__init__(f"IngestJob {job_id} not found")


class IngestService:
    """Manages IngestJob lifecycle.

    Args:
        db: SQLAlchemy AsyncSession.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_job(self, tenant_id: uuid.UUID, source: str = "all") -> IngestJob:
        """Create and persist a new IngestJob at status='running'.

        Args:
            tenant_id: Internal UUID of the tenant.
            source: Integration source name ('all', 'jira', 'github', 'slack').

        Returns:
            The newly created IngestJob.
        """
        job = IngestJob(
            tenant_id=tenant_id,
            source=source,
            status="running",
            progress_pct=0,
            record_counts={},
        )
        self._db.add(job)
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def update_progress(
        self,
        job_id: uuid.UUID,
        progress_pct: int,
        record_counts: dict[str, int],
    ) -> IngestJob:
        """Update ingest progress.

        Sets progress_pct, record_counts, last_record_at, and emits the
        Prometheus gauge.

        Args:
            job_id: PK of the IngestJob to update.
            progress_pct: Percentage complete (0–100).
            record_counts: Dict of record type → count ingested so far.

        Returns:
            Updated IngestJob.

        Raises:
            JobNotFoundError: If no job with the given ID exists.
        """
        job = await self._get_job(job_id)
        now = datetime.now(UTC)

        job.progress_pct = progress_pct
        job.record_counts = dict(record_counts)  # type: ignore[assignment]
        job.last_record_at = now
        job.updated_at = now

        # Prometheus gauge
        _last_record_gauge.set(
            time.time(),
            {"tenant_id": str(job.tenant_id), "source": job.source},
        )

        await self._db.flush()
        return job

    async def mark_complete(self, job_id: uuid.UUID) -> IngestJob:
        """Transition job to 'completed', trigger email and onboarding advance.

        Side-effects (best-effort, failures logged not raised):
          - EmailService.notify_ingest_complete
          - OnboardingService.advance_step(session_id, 'briefing')

        Args:
            job_id: PK of the IngestJob.

        Returns:
            Updated IngestJob with status='completed'.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        job = await self._get_job(job_id)
        now = datetime.now(UTC)

        job.status = "completed"
        job.completed_at = now
        job.updated_at = now

        await self._db.flush()

        # Best-effort email notification
        try:
            email_svc = EmailService()
            await email_svc.notify_ingest_complete(
                job.tenant_id,
                recipient_email="",  # caller should pass real email; stub for now
                counts={k: int(v) for k, v in (job.record_counts or {}).items()},  # type: ignore[arg-type]
            )
        except Exception as exc:
            logger.error(
                "Failed to send ingest-complete email for job %s: %s",
                job_id,
                exc,
            )

        # Best-effort onboarding advancement
        try:
            onboarding_svc = OnboardingService(self._db)
            result = await self._db.execute(
                select(OnboardingSession).where(
                    OnboardingSession.tenant_id == job.tenant_id
                )
            )
            session = result.scalar_one_or_none()
            if session is not None and session.current_step == "ingest":
                await onboarding_svc.advance_step(session.id, "briefing")
        except Exception as exc:
            logger.error(
                "Failed to advance onboarding to briefing for tenant %s: %s",
                job.tenant_id,
                exc,
            )

        return job

    async def mark_stalled(self, job_id: uuid.UUID) -> IngestJob:
        """Transition job to 'stalled'.

        Args:
            job_id: PK of the IngestJob.

        Returns:
            Updated IngestJob with status='stalled'.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        job = await self._get_job(job_id)
        job.status = "stalled"
        job.updated_at = datetime.now(UTC)
        await self._db.flush()
        return job

    async def is_stalled(self, job_id: uuid.UUID) -> bool:
        """Return True if the job is running but last_record_at is > 2 hours ago.

        Args:
            job_id: PK of the IngestJob.

        Returns:
            True when the job meets stall criteria; False otherwise.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        job = await self._get_job(job_id)
        if job.status != "running":
            return False
        if job.last_record_at is None:
            return False
        threshold = datetime.now(UTC) - _STALL_THRESHOLD
        return job.last_record_at < threshold

    async def get_job(self, job_id: uuid.UUID) -> IngestJob:
        """Fetch an IngestJob by PK.

        Args:
            job_id: PK of the IngestJob.

        Returns:
            The IngestJob.

        Raises:
            JobNotFoundError: If no job with the given ID exists.
        """
        return await self._get_job(job_id)

    # ── internals ─────────────────────────────────────────────────────────────

    async def _get_job(self, job_id: uuid.UUID) -> IngestJob:
        """Fetch an IngestJob by PK or raise JobNotFoundError."""
        result = await self._db.execute(select(IngestJob).where(IngestJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            raise JobNotFoundError(job_id)
        return job
