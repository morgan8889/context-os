---
sidebar_position: 3
---

# Dependency

A dependency in Context-OS is a directional relationship between two initiatives where one's progress is contingent on the other's. Dependency A blocking B means B cannot proceed, ship, or be resolved without some output from A.

## How dependencies are detected

Context-OS detects dependencies from three signal types.

The first is explicit linking. When a Jira ticket in initiative B references a ticket in initiative A through a link relationship, Context-OS reads that as a potential dependency and evaluates whether it is blocking.

The second is pull request references. When a GitHub pull request in one repository references another PR or issue in a different repository, and those repositories belong to different initiatives, Context-OS surfaces the cross-initiative relationship.

The third is shared resource patterns. When engineers appear on active tickets in two different initiatives simultaneously, or when a PR touches shared infrastructure owned by a separate team, Context-OS flags the potential coupling for human review. These proposed dependencies go to the inbox for operator approval before they are committed to the memory graph.

## Why dependencies matter for briefings

A briefing without dependency context tells you what is happening. A briefing with dependency context tells you what is about to break.

When initiative B is in good shape but depends on initiative A, which is two weeks behind, the risk to B does not appear anywhere in B's own tickets. It only becomes visible when you look across initiative boundaries. Context-OS does that automatically and surfaces it in the dependencies section of your briefing.

This is one of the highest-value things Context-OS provides. Cross-team dependency risk is structurally hard to see from any single team's Jira board. It requires looking at the whole graph.
