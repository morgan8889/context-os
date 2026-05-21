---
sidebar_position: 2
---

# Initiative

An initiative in Context-OS is the highest-level unit of tracked work. It represents a meaningful chunk of effort that spans multiple issues, pull requests, or conversations, and has a discernible goal and timeline.

## Relation to Jira and GitHub entities

Context-OS maps initiatives from the structures you already use. A Jira epic is the most common source. When Context-OS ingests your Jira data, it treats each epic as a candidate initiative and looks at the issues nested under it to understand current status, velocity, and risk.

GitHub repositories and individual pull requests do not become initiatives on their own, but they are associated with initiatives when their content relates to a tracked Jira epic. A pull request that references a Jira ticket through its title or description gets linked to the corresponding initiative in the Context-OS memory graph.

Slack threads do not directly create initiatives, but decisions and blockers surfaced in Slack are attributed to the initiative they most closely relate to based on the people involved and the projects referenced.

## Why the distinction matters

Initiatives are the grain at which briefings are organized. When Context-OS drafts a briefing, it presents progress, risks, decisions, and dependencies at the initiative level. This means you see what is happening with each meaningful piece of work, not a flat list of hundreds of individual tickets or commits.

The initiative model also drives dependency detection. When two initiatives share engineering resources, share a downstream system, or have tickets with explicit links between them, Context-OS surfaces that relationship as a dependency. Dependencies at the initiative level are meaningful. Dependencies at the ticket level would be noise.
