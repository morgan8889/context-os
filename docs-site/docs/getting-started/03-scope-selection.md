---
id: 03-scope-selection
sidebar_position: 3
---

# Scope Selection

After connecting your integrations, Context-OS asks which initiatives your briefing should cover. This step determines the signal perimeter for your first briefing and all recurring briefings until you change it.

## What the question is asking

Your Jira instance may contain hundreds of projects, your GitHub organization dozens of repositories, and your Slack workspace hundreds of channels. Not all of them are relevant to the briefing you need.

Scope selection is where you tell Context-OS which subset of that material matters to you. The list it shows you is pre-filtered to items that have been active in the last 90 days. An initiative, repository, or channel is considered active if it had a meaningful update during that window. For Jira, that means a status change, a comment, or a new ticket added to the epic. For GitHub, it means a pull request opened, closed, or merged. For Slack, it means a message posted in that channel.

## What "active in last 90 days" means

The 90-day window is a practical default. Most initiatives that are relevant to a current engineering briefing have had some activity in the last three months. Initiatives that have gone quiet for longer than that are either complete, on hold, or low enough priority that including them would dilute the briefing.

If you have a project that has been dormant for more than 90 days but needs to be tracked, you can add it manually. The scope selection screen includes a search field that queries all available items across your connected sources, not just the pre-filtered active list.

## How to deselect items

The list starts with everything active in the last 90 days pre-checked. This is a starting point, not a fixed selection.

If your team manages many concurrent workstreams, you may find that the list includes projects that are technically active but are low priority for your briefing. Unchecking a project removes it from the scope. Context-OS will not pull signals from unchecked sources, and they will not appear in your briefing.

The selection summary at the bottom of the screen shows the count of Jira projects, GitHub repositories, and Slack channels currently included. Use this to get a sense of the scope you are setting. For most teams, a first briefing covering between five and fifteen active initiatives produces the most useful output.

## Confirming your selection

When you are satisfied with the scope, click Confirm Selection. Context-OS will begin ingesting data from your connected sources for the items you selected. The next screen shows the progress of that ingest.

You can change your scope at any time after setup. Adding or removing initiatives from scope takes effect on the next scheduled briefing.
