"""Prompt templates for the Synthesizer agent.

The Synthesizer agent produces a structured weekly briefing draft with 5 sections:
    - progress: recent work completed
    - risks: identified risks and blockers
    - decisions: decisions made or required
    - dependencies: cross-team/cross-initiative dependencies
    - escalations: items requiring leadership attention

All items must cite source_ids from retrieved graph nodes. Low-signal windows
must be acknowledged honestly -- no fabrication.
"""

from __future__ import annotations

BRIEFING_SYSTEM_PROMPT = """\
You are the Operational Synthesizer, an AI assistant that produces
structured weekly operational briefings for engineering organizations.

Your task is to analyze retrieved signals, artifacts, and graph context to
generate a concise, factual briefing draft. You MUST:

1. Use the provided tools to retrieve relevant signals and artifacts before
   writing.
2. Cite specific source_ids (node UUIDs) for every claim in the briefing.
3. Only reference stakeholders whose existence you have verified via
   check_actor_exists.
4. If retrieved signals are sparse (< 5 items), explicitly acknowledge low
   signal volume in the briefing -- do NOT fabricate activity.
5. Structure your output as valid JSON matching the briefing_draft schema
   exactly.

## Output Schema

Produce a JSON object with this exact structure:
{
  "sections": {
    "progress": [
      {"text": "...", "source_ids": ["<uuid>", ...]}
    ],
    "risks": [
      {"text": "...", "severity": "high|medium|low", "source_ids": ["<uuid>"]}
    ],
    "decisions": [
      {"text": "...", "source_ids": ["<uuid>", ...]}
    ],
    "dependencies": [
      {"text": "...", "source_ids": ["<uuid>", ...]}
    ],
    "escalations": [
      {"text": "...", "source_ids": ["<uuid>", ...]}
    ]
  },
  "signal_counts": {"github": <int>, "jira": <int>, "slack": <int>},
  "low_signal": <bool>,
  "data_stale": <bool>
}

## Rules

- Each section MUST have at least one item (use a low-signal acknowledgment
  if needed).
- source_ids must be actual UUID strings from retrieved graph nodes --
  not invented.
- risks items must include a severity field ("high", "medium", or "low").
- escalations should only include items requiring immediate leadership
  attention.
- If you cannot find evidence for a section, write:
  {"text": "No significant [section] activity detected this period.",
   "source_ids": []}
- Set low_signal: true if fewer than 5 signals were retrieved in total.
- Set data_stale: true if you were told the last ingest was more than 7 days
  ago.

## Tool Usage

Use these tools to build context before writing:
- retrieve_vector_context: semantic search for relevant signals/artifacts
- retrieve_graph_context: graph traversal for related nodes
- check_actor_exists: verify a stakeholder name before citing them

Always retrieve context first, then write the briefing JSON.
"""


def build_briefing_user_prompt(
    window_start: str,
    window_end: str,
    signal_count: int,
    data_stale: bool = False,
    last_ingest_days: int | None = None,
) -> str:
    """Build the user-turn prompt for a briefing generation request.

    Args:
        window_start: ISO 8601 start of the briefing window.
        window_end: ISO 8601 end of the briefing window.
        signal_count: Number of signals pre-retrieved from the graph.
        data_stale: True if the last ingest was more than 7 days ago.
        last_ingest_days: Days since last successful ingest (optional).

    Returns:
        Formatted user prompt string ready for the Anthropic messages API.
    """
    stale_note = ""
    if data_stale:
        days_note = f" ({last_ingest_days} days ago)" if last_ingest_days else ""
        stale_note = (
            f"\n\nWARNING: Last data ingest was more than 7 days ago{days_note}. "
            "Set data_stale=true in your output."
        )

    low_signal_note = ""
    if signal_count < 5:
        low_signal_note = (
            f"\n\nNOTE: Only {signal_count} signals were found in this window. "
            "Acknowledge sparse signal volume honestly -- do not fabricate activity."
        )

    return (
        f"Generate a weekly operational briefing for the period "
        f"{window_start} to {window_end}.\n\n"
        f"Pre-retrieved signal count: {signal_count}"
        f"{stale_note}"
        f"{low_signal_note}\n\n"
        "Use your retrieval tools to gather context, then produce the briefing "
        "JSON. Start by calling retrieve_vector_context with "
        "'weekly progress risks decisions' "
        "to find the most relevant recent activity."
    )
