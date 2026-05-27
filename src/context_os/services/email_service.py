"""EmailService: transactional email via the Resend API.

Silent no-op when RESEND_API_KEY is not set — email is optional in dev/staging.
"""

from __future__ import annotations

import logging
import uuid

import httpx

from context_os.config import get_settings

logger = logging.getLogger(__name__)

_RESEND_EMAILS_URL = "https://api.resend.com/emails"


class EmailService:
    """Sends transactional emails through Resend.

    All methods silently no-op when ``settings.resend_api_key`` is None.
    """

    async def notify_ingest_complete(
        self,
        tenant_id: uuid.UUID,
        recipient_email: str,
        counts: dict[str, int],
    ) -> None:
        """Send a "data ready" notification email to the tenant operator.

        Args:
            tenant_id: Internal UUID of the tenant (used for logging).
            recipient_email: Email address of the recipient operator.
            counts: Mapping of record type → count (e.g. {"initiatives": 7}).
        """
        settings = get_settings()
        if settings.resend_api_key is None:
            logger.debug(
                "RESEND_API_KEY not set; skipping ingest-complete email for tenant %s",
                tenant_id,
            )
            return

        initiative_count = counts.get("initiatives", 0)
        subject = (
            f"Your Context-OS data is ready — {initiative_count} initiatives found"
        )

        html_body = _build_html(initiative_count, counts)

        payload = {
            "from": settings.resend_from_email,
            "to": [recipient_email],
            "subject": subject,
            "html": html_body,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    _RESEND_EMAILS_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
            logger.info(
                "Ingest-complete email sent to %s for tenant %s",
                recipient_email,
                tenant_id,
            )
        except httpx.HTTPError as exc:
            # Email failure must not block the main workflow
            logger.error(
                "Failed to send ingest-complete email for tenant %s: %s",
                tenant_id,
                exc,
            )


def _build_html(initiative_count: int, counts: dict[str, int]) -> str:
    """Return a simple inline-CSS HTML email body.

    Args:
        initiative_count: Number of initiatives ingested.
        counts: Full record counts mapping for display in the body.

    Returns:
        HTML string suitable for a Resend ``html`` payload field.
    """
    rows = "".join(
        f"<tr><td style='padding:4px 8px;'>{k.capitalize()}</td>"
        f"<td style='padding:4px 8px; font-weight:bold;'>{v}</td></tr>"
        for k, v in counts.items()
    )
    th_style = "text-align:left;padding:4px 8px;border-bottom:1px solid #ddd;"
    body_style = (
        "font-family:sans-serif;color:#111;"
        "max-width:600px;margin:0 auto;padding:24px;"
    )
    return (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body style="{body_style}">'
        f'<h1 style="font-size:20px;margin-bottom:8px;">'
        f"Your data is ready in Context-OS</h1>"
        f'<p style="margin:0 0 16px;">'
        f"We've finished ingesting your organization's data. "
        f"<strong>{initiative_count} initiatives</strong> were identified.</p>"
        f'<table style="border-collapse:collapse;width:100%;">'
        f"<thead><tr>"
        f'<th style="{th_style}">Type</th>'
        f'<th style="{th_style}">Count</th>'
        f"</tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f'<p style="margin-top:24px;font-size:13px;color:#666;">'
        f"Log in to Context-OS to review and approve your first briefing.</p>"
        f"</body></html>"
    )
