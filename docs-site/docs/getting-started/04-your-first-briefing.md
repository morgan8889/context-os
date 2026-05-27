---
id: 04-your-first-briefing
sidebar_position: 4
---

# Your First Briefing

After you confirm your scope selection, Context-OS begins pulling data from your connected sources. This is the ingest phase, and it takes time.

## The wait period

The first ingest is the longest one. Context-OS is reading the history of your selected projects, repositories, and channels to understand the current state of each initiative. For a typical scope of ten initiatives with active Jira, GitHub, and Slack connections, this takes between two and fifteen minutes.

A progress indicator on screen shows you where the ingest stands. You do not need to stay on the page. If you leave and return, Context-OS resumes where it left off and the progress indicator updates when you come back.

When the ingest is complete, you will see a completion summary. It shows how many initiatives were found, how many pull requests were processed, and how many active threads from Slack were included. This summary tells you whether the ingest captured what you expected. If a major initiative is missing, check that it was included in scope selection and that your connected integration has access to it.

## Reviewing the draft

After the ingest completes, Context-OS generates a draft briefing. The draft is organized into sections: progress, risks, decisions, dependencies, and escalations. Each item in the briefing links back to the source signal that produced it.

You can edit any part of the draft inline. Click on a section, change the text, and the edit is saved automatically. The goal of the review is not to rewrite the briefing from scratch but to correct anything the AI got wrong and to add context that the signals alone could not capture.

Pay particular attention to the risks and escalations sections on your first briefing. These sections reflect what Context-OS detected as potentially high-priority across your scope, and they are worth verifying against your own awareness of what is actually at risk this week.

## Approving the briefing

When the draft reflects an accurate picture of the current state, click Approve. This action does two things.

First, it marks this briefing as your organization's current operational snapshot. The approved content becomes part of Context-OS's organizational memory. Future briefings will reference it when describing what has changed.

Second, it activates your Context-OS workspace. Approval of the first briefing is the activation event. After activation, you gain access to the full navigation including the Galaxy view, the Topology view, and the Decisions view. You also receive access to recurring briefing scheduling, which will automatically draft and surface briefings for your review on the cadence you configure.

## After activation

Activation is not a one-time event in terms of the product's utility. It is the starting point. Each subsequent briefing builds on the approved history. Dependencies, decisions, and risks accumulate in the memory graph over time, making each briefing more accurate and more useful than the last.

The first briefing is the hardest one. From here, the work is review and approval, not discovery.
