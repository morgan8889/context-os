"""Unit tests for OnboardingService state machine.

Tests validate state transitions, idempotency, and reversal. DB session
is mocked — no real database required.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from context_os.db.models import OnboardingSession


def _make_session(
    tenant_id: uuid.UUID | None = None,
    current_step: str = "survey",
    step_completed_at: dict | None = None,
    step_started_at: dict | None = None,
) -> OnboardingSession:
    """Build a minimal OnboardingSession ORM instance for testing."""
    session = MagicMock(spec=OnboardingSession)
    session.id = uuid.uuid4()
    session.tenant_id = tenant_id or uuid.uuid4()
    session.current_step = current_step
    session.step_completed_at = step_completed_at or {}
    session.step_started_at = step_started_at or {}
    session.survey_answer = None
    session.connected_integrations = []
    session.scope_selection = None
    session.ingest_job_id = None
    session.activated_at = None
    session.created_at = datetime.now(UTC)
    session.updated_at = datetime.now(UTC)
    return session


class TestOnboardingServiceAdvanceStep:
    """advance_step() state transition tests."""

    async def test_advance_survey_to_connect_succeeds(self) -> None:
        """Advancing from survey→connect is a legal transition."""
        from context_os.services.onboarding_service import OnboardingService

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        session = _make_session(current_step="survey")

        # Stub the DB lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = session
        mock_db.execute.return_value = mock_result

        updated = await svc.advance_step(session.id, "connect", {"option": "briefings"})

        assert updated.current_step == "connect"
        assert "survey" in updated.step_completed_at

    async def test_advance_connect_to_survey_raises(self) -> None:
        """Advancing backwards from connect→survey raises InvalidTransitionError."""
        from context_os.services.onboarding_service import (
            InvalidTransitionError,
            OnboardingService,
        )

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        session = _make_session(current_step="connect")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = session
        mock_db.execute.return_value = mock_result

        with pytest.raises(InvalidTransitionError):
            await svc.advance_step(session.id, "survey", {})

    async def test_advance_idempotent_completed_step(self) -> None:
        """Re-advancing a step that is already completed returns session unchanged."""
        from context_os.services.onboarding_service import OnboardingService

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        already_completed_at = "2026-05-21T10:00:00+00:00"
        session = _make_session(
            current_step="connect",
            step_completed_at={"survey": already_completed_at},
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = session
        mock_db.execute.return_value = mock_result

        result = await svc.advance_step(session.id, "survey", {})

        # session returned unchanged; step_completed_at for survey not overwritten
        assert result.step_completed_at["survey"] == already_completed_at


class TestOnboardingServiceRevertStep:
    """revert_step() rollback tests."""

    async def test_revert_connect_clears_completion_and_resets_step(self) -> None:
        """revert_step resets current_step to 'connect' and clears completion."""
        from context_os.services.onboarding_service import OnboardingService

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        session = _make_session(
            current_step="scope",
            step_completed_at={
                "survey": "2026-05-21T09:00:00+00:00",
                "connect": "2026-05-21T10:00:00+00:00",
            },
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = session
        mock_db.execute.return_value = mock_result

        updated = await svc.revert_step(session.id, "connect")

        assert updated.current_step == "connect"
        assert "connect" not in updated.step_completed_at
        assert "survey" in updated.step_completed_at  # earlier step preserved


class TestOnboardingServiceGetOrCreate:
    """get_or_create() upsert tests."""

    async def test_get_or_create_creates_session_at_survey(self) -> None:
        """get_or_create returns a new session at 'survey' step when none exists."""
        from context_os.services.onboarding_service import OnboardingService

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        tenant_id = uuid.uuid4()

        # execute returns None (no existing session), then None for refresh
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result_none

        # The ORM object that gets added to the session
        created_session = _make_session(tenant_id=tenant_id, current_step="survey")

        async def _fake_refresh(obj: object) -> None:
            # Nothing needed — the mock already has correct attributes
            pass

        mock_db.refresh = AsyncMock(side_effect=_fake_refresh)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        # Patch the ORM constructor so it returns our fixture object
        with patch(
            "context_os.services.onboarding_service.OnboardingSession",
            return_value=created_session,
        ):
            # Patch `select` to avoid SQLAlchemy introspecting the mock class
            with patch("context_os.services.onboarding_service.select"):
                result = await svc.get_or_create(tenant_id)

        assert result.current_step == "survey"
        assert result.tenant_id == tenant_id

    async def test_get_or_create_returns_existing_session(self) -> None:
        """get_or_create returns existing session when one already exists."""
        from context_os.services.onboarding_service import OnboardingService

        mock_db = AsyncMock()
        svc = OnboardingService(mock_db)
        tenant_id = uuid.uuid4()
        existing = _make_session(tenant_id=tenant_id, current_step="connect")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        result = await svc.get_or_create(tenant_id)

        assert result.current_step == "connect"
