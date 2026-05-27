---
sidebar_position: 2
---

# Dependency Scan Workflow

The Dependency Scan workflow identifies potential cross-initiative dependencies and proposes them for operator review before committing them to the memory graph.

## 1. Trigger

A dependency scan is triggered manually from the dependency scan dashboard or automatically at a configured interval. Scans can also be triggered by the briefing workflow when a new briefing ingest surfaces signals suggesting a cross-initiative relationship.

## 2. Graph Traversal

The Mapper agent begins from a starting initiative or from the full set of active initiatives in scope. It traverses the initiative graph looking for edges that suggest dependency relationships.

The agent examines explicit Jira link relationships between tickets in different initiatives, GitHub pull requests that reference issues across repository boundaries, shared engineer allocation patterns across concurrent epics, and infrastructure components that appear in multiple initiatives' pull requests.

The traversal is bounded by tenant scope. The agent only examines initiatives and resources that belong to your organization.

## 3. Proposed Edges

For each potential dependency found, the Mapper agent produces a proposed dependency edge. The edge includes the from-initiative, the to-initiative, the direction of dependency, the evidence signals that support the relationship, and a confidence level based on the strength and number of signals.

Proposed edges are not added to the memory graph. They are placed in the operator inbox for review.

## 4. Operator Approval in Inbox

Each proposed dependency edge appears in the inbox as a review item. The operator sees the two initiatives involved, the evidence signals, and the proposed dependency direction.

Approving the edge commits it to the memory graph. Rejecting it dismisses the proposal. Rejected proposals are logged but do not affect future scans, which may re-propose the same edge if the evidence remains.

Approved edges appear in the Topology view and are included in future briefings when either of the connected initiatives is relevant.

## 5. Memory Graph Update

Approved dependency edges are committed to the organizational memory graph as directional relationships between the two initiative nodes. The relationship includes metadata: the approval timestamp, the approving operator, and the evidence signals that supported the proposal.

The memory graph update triggers re-evaluation of any scheduled briefing that includes either connected initiative, ensuring the next briefing reflects the newly confirmed dependency.
