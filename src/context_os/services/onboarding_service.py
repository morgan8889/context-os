"""OnboardingService: state machine for the Workflow-First onboarding flow.

Legal step transitions (forward only):
    survey → connect → scope → ingest → briefing → activated

get_or_create  — upsert a session for the given tenant
advance_step   — validate transition, write timestamps, update current_step
revert_step    — roll back to a prior step (used on OAuth failure / ingest stall)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.db.models import OnboardingSession

# Ordered list of legal steps
_STEPS: list[str] = ["survey", "connect", "scope", "ingest", "briefing", "activated"]
_STEP_INDEX: dict[str, int] = {s: i for i, s in enumerate(_STEPS)}


class InvalidTransitionError(Exception):
    """Raised when advance_step attempts an illegal step transition.

    Attributes:
        from_step: The step the session is currently on.
        to_step: The step that was requested.
    """

    def __init__(self, from_step: str, to_step: str) -> None:
        self.from_step = from_step
        self.to_step = to_step
        super().__init__(
            f"Cannot transition from '{from_step}' to '{to_step}'; "
            f"only forward-only transitions are legal"
        )


class SessionNotFoundError(Exception):
    """Raised when a session_id does not exist in the database."""

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__(f"OnboardingSession {session_id} not found")


class OnboardingService:
    """Manages the onboarding state machine for a tenant.

    Args:
        db: SQLAlchemy AsyncSession for database operations.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create(self, tenant_id: uuid.UUID) -> OnboardingSession:
        """Return the existing onboarding session or create one at 'survey'.

        Args:
            tenant_id: Internal DB UUID of the tenant.

        Returns:
            OnboardingSession instance (persisted).
        """
        result = await self._db.execute(
            select(OnboardingSession).where(OnboardingSession.tenant_id == tenant_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        now_iso = datetime.now(UTC).isoformat()
        session = OnboardingSession(
            tenant_id=tenant_id,
            current_step="survey",
            step_started_at={"survey": now_iso},
            step_completed_at={},
            connected_integrations=[],
        )
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def advance_step(
        self,
        session_id: uuid.UUID,
        step: str,
        data: dict | None = None,
    ) -> OnboardingSession:
        """Advance the onboarding session to the next step.

        Idempotent: if the requested step is already completed (i.e. the session
        has already moved past it), the session is returned unchanged.

        Args:
            session_id: PK of the OnboardingSession to advance.
            step: Target step name.
            data: Optional payload to persist against the step
                  (survey_answer, scope_selection, etc.).

        Returns:
            Updated OnboardingSession.

        Raises:
            SessionNotFoundError: If the session does not exist.
            InvalidTransitionError: If the transition is not legal (backwards
                or skipped).
        """
        result = await self._db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise SessionNotFoundError(session_id)

        current_idx = _STEP_INDEX.get(session.current_step, -1)
        target_idx = _STEP_INDEX.get(step, -1)

        # Idempotent: step already completed (session already past it)
        if step in session.step_completed_at:
            return session

        # Illegal transition: target is not the immediate next step
        if target_idx != current_idx + 1:
            raise InvalidTransitionError(session.current_step, step)

        now_iso = datetime.now(UTC).isoformat()

        # Mark current step as completed
        completed = dict(session.step_completed_at or {})
        completed[session.current_step] = now_iso
        session.step_completed_at = completed

        # Advance
        session.current_step = step

        # Record start time for the new step
        started = dict(session.step_started_at or {})
        started[step] = now_iso
        session.step_started_at = started

        # Persist step-specific data
        if data:
            self._apply_step_data(session, step, data)

        if step == "activated":
            session.activated_at = datetime.now(UTC)

        session.updated_at = datetime.now(UTC)
        await self._db.flush()
        return session

    async def revert_step(
        self,
        session_id: uuid.UUID,
        step: str,
    ) -> OnboardingSession:
        """Revert the session back to the given step.

        Clears the completion timestamp for *step* and sets current_step = step.
        Earlier step completions are preserved.

        Args:
            session_id: PK of the OnboardingSession to revert.
            step: Step name to revert to.

        Returns:
            Updated OnboardingSession.

        Raises:
            SessionNotFoundError: If the session does not exist.
        """
        result = await self._db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise SessionNotFoundError(session_id)

        # Clear completion timestamp for the reverted step
        completed = dict(session.step_completed_at or {})
        completed.pop(step, None)
        session.step_completed_at = completed

        session.current_step = step
        session.updated_at = datetime.now(UTC)
        await self._db.flush()
        return session

    # ── helpers ───────────────────────────────────────────────────────────────

    def _apply_step_data(
        self, session: OnboardingSession, step: str, data: dict
    ) -> None:
        """Persist step-specific payload fields onto the session row."""
        if step == "connect" and "option" in data:
            session.survey_answer = data
        elif step == "scope":
            session.scope_selection = data
