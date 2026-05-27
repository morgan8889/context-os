---
id: 02-connect-integrations
sidebar_position: 2
---

# Connect Integrations

Context-OS builds your briefings from three sources: Jira, GitHub, and Slack. Each one contributes a different kind of signal, and together they give Context-OS a complete picture of what your team is doing.

## What each integration provides

**Jira** is the source of record for initiatives. When Context-OS reads your Jira instance, it identifies epics and projects that are actively in flight, maps their current status, and flags which ones have outstanding risks or blockers. Without Jira, Context-OS cannot speak meaningfully to cross-team progress or initiative-level dependencies.

**GitHub** tracks the work happening at the code level. Pull requests, review states, and recently merged changes tell Context-OS which features are close to shipping, which are stalled, and which carry technical debt or unresolved reviews. For engineering-heavy organizations, GitHub signals are often the most precise leading indicator of delivery risk.

**Slack** captures decisions. Most consequential decisions in modern engineering teams happen in a Slack thread, not in a formal document. Context-OS reads the channels you designate and extracts decision records from that conversation history. These become part of your briefing and part of your searchable organizational memory.

## How to connect

Each integration appears as a card on the connection screen. To connect one, click the Connect button on its card. A browser popup will open and take you through the standard authorization flow for that provider. You log in with your credentials for that service and approve the requested permissions.

When the authorization is complete, the popup closes automatically. The card on the screen updates to show a green checkmark confirming the connection is active. Context-OS does not store your credentials. It holds an access token that you can revoke at any time from within that provider's settings.

## Partial connection

You do not need all three integrations connected before you continue. Context-OS can generate a useful briefing from any combination of connected sources.

If you connect only GitHub, your briefing will focus on pull request activity and code-level signals. If you connect only Jira, it will focus on initiative status and blockers. The more sources you connect, the more complete the picture.

That said, Jira and Slack together provide the strongest signal for most teams. If you can connect at least two of the three, the first briefing will be substantially more useful.

## What happens if a connection fails

OAuth connections occasionally fail due to permission settings on the provider side or expired login sessions. If the popup closes without the card showing a green checkmark, try clicking Connect again. If it continues to fail, check that you have the necessary permissions in that service. Jira connections require that your account has read access to the projects you want included. GitHub requires read access to your organization's repositories. Slack requires that you are a member of the channels you want Context-OS to monitor.

When you have connected at least one source and are ready to continue, click Continue to move to scope selection.
