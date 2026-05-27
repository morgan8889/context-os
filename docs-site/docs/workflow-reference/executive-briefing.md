---
sidebar_position: 1
---

# Executive Briefing Workflow

The Executive Briefing workflow produces a structured operational summary of your organization's current state. This reference describes each step in the workflow from trigger to delivery.

## 1. Trigger

A briefing run is triggered in one of two ways: on a recurring schedule that you configure after activation, or on demand by clicking Generate Briefing from the briefing dashboard.

Scheduled triggers fire at the configured time regardless of whether any operator is logged in. On-demand triggers are available at any time.

## 2. Ingest

When a briefing run begins, Context-OS re-ingests data from your connected sources within the configured scope. This is an incremental ingest. On the first briefing, the full history of each initiative is read. On subsequent briefings, only changes since the last briefing's timestamp are pulled.

Ingest reads Jira for ticket status changes and new issues within scoped epics. It reads GitHub for pull request state changes, new reviews, and merged commits. It reads Slack for new messages in scoped channels, with attention to decision-pattern signals.

Ingest typically completes in under three minutes for ongoing briefings after the initial full pull.

## 3. AI Drafting

After ingest, the Synthesizer agent reads all retrieved signals and produces a structured draft. The draft is organized into five sections: progress, risks, decisions, dependencies, and escalations.

Each item in the draft cites the signal that produced it. If the agent surfaces a risk based on a stalled pull request, the draft links to that PR. If it surfaces a decision based on a Slack thread, the draft links to that thread.

The agent also runs failure detection before committing the draft. It checks for hallucinated stakeholder names, stale dependency references, risks without corresponding escalations, and citations to signals that do not exist. Detected issues are flagged in the draft for operator attention.

## 4. Operator Review

The draft appears in the briefing review interface. The operator reads each section, edits inline where needed, and assesses the failure flags if any were raised.

Edits are saved automatically as you type. There is no save button. The draft persists between sessions, so you can leave and return without losing work.

## 5. Approval

When the draft accurately represents the current state, the operator clicks Approve. Approval commits the briefing content to the memory graph, making it the current operational snapshot for the organization.

Approval also advances the onboarding session to the activated state if this is the first briefing.

## 6. Scheduling

After activation, you can configure the briefing cadence from the settings panel. Options include daily, weekly on a specific day, and bi-weekly. The scheduler uses the activation timestamp as the starting anchor and generates the next run time based on the configured cadence.

Scheduled briefings are drafted automatically and placed in the inbox for review. You receive a notification when a draft is ready. Drafts do not auto-approve under any configuration.
