---
sidebar_position: 1
---

# Briefing

A briefing in Context-OS is a structured summary of your organization's operational state at a point in time. It covers what has progressed, what is at risk, what decisions have been made, what dependencies exist between teams or systems, and what requires escalation.

## How it differs from a report

A report is a static document produced by a person synthesizing data from multiple sources. Writing one takes time, requires access to the right tools and systems, and produces something that is already partially out of date by the time it is read.

A briefing in Context-OS is drafted by an AI agent that has continuous access to your Jira, GitHub, and Slack data. The agent pulls signals from those systems, organizes them into the standard briefing structure, and surfaces the result for operator review. The human's job is to review and approve, not to write.

The distinction matters because it changes what is economically feasible. A briefing that takes an hour to write happens weekly at best. One that takes five minutes to review can happen daily, or on demand before any meeting where situational awareness matters.

## What "approve" means

Approval is a deliberate gate. The AI draft is never published to the organizational memory without a human reviewing it. When you approve a briefing, you are confirming that the content accurately represents the current state to the best of your knowledge.

Approved content becomes part of the memory graph. Future briefings reference it when describing what has changed since the last briefing. Approval is not a rubber stamp. It is a governance action.

You can edit any section of the draft before approving. Edits are saved to the memory graph alongside the source-derived content, so the record reflects your corrections.

## Scheduling

After your first briefing is approved, you can configure recurring briefing generation. Context-OS will draft briefings on your chosen cadence and surface them for review. Recurring briefings use the same ingest and drafting pipeline as the first one.
