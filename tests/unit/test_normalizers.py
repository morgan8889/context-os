"""Unit tests for all three normalizers.

Tests verify the source normalization map from data-model.md:
- GitHub Repo → Initiative (name → title)
- GitHub PR → Artifact (title, body, state)
- GitHub Issue open → Signal
- GitHub Issue closed → Artifact
- GitHub Milestone → Goal
- GitHub User → Actor
- GitHub PR Review → Signal
- Jira Project → Initiative
- Jira Epic → Goal
- Jira Issue done → Artifact
- Jira Issue in-progress → Signal
- Jira User → Actor
- Slack Message → Signal (ts → occurred_at)
- Slack User → Actor
"""

from __future__ import annotations

from datetime import datetime

TENANT_ID = "org_test_tenant_123"


# ── GitHub Normalizer Tests ────────────────────────────────────────────────────


class TestGitHubNormalizerRepo:
    """Tests for repo_to_initiative()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)

    def test_repo_to_initiative_basic_fields(self) -> None:
        """GitHub repo maps to Initiative with correct fields."""
        repo = {
            "id": 12345,
            "name": "my-repo",
            "description": "A test repository",
            "html_url": "https://github.com/org/my-repo",
            "archived": False,
        }
        result = self.normalizer.repo_to_initiative(repo)

        assert result["node_type"] == "Initiative"
        assert result["source"] == "github"
        assert result["source_id"] == "12345"
        assert result["title"] == "my-repo"
        assert result["description"] == "A test repository"
        assert result["status"] == "active"
        assert result["url"] == "https://github.com/org/my-repo"
        assert result["tenant_id"] == TENANT_ID

    def test_repo_to_initiative_archived(self) -> None:
        """Archived repo maps to status=archived."""
        repo = {"id": 1, "name": "old-repo", "archived": True}
        result = self.normalizer.repo_to_initiative(repo)
        assert result["status"] == "archived"

    def test_repo_to_initiative_has_base_fields(self) -> None:
        """Result has all required BaseNodeSchema fields."""
        repo = {"id": 1, "name": "repo"}
        result = self.normalizer.repo_to_initiative(repo)

        required_fields = (
            "id",
            "tenant_id",
            "source",
            "source_id",
            "fetch_ts",
            "created_at",
            "updated_at",
        )
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_repo_to_initiative_deterministic_id(self) -> None:
        """Same repo + tenant always produces same node id."""
        repo = {"id": 99999, "name": "stable-repo"}
        result1 = self.normalizer.repo_to_initiative(repo)
        result2 = self.normalizer.repo_to_initiative(repo)
        assert result1["id"] == result2["id"]


class TestGitHubNormalizerPR:
    """Tests for pr_to_artifact()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)
        self.repo = "owner/repo"

    def test_pr_to_artifact_basic(self) -> None:
        """GitHub PR maps to Artifact with correct fields."""
        pr = {
            "number": 42,
            "title": "Fix authentication bug",
            "body": "This PR fixes the auth issue",
            "state": "open",
            "html_url": "https://github.com/owner/repo/pull/42",
            "draft": False,
            "merged_at": None,
        }
        result = self.normalizer.pr_to_artifact(pr, self.repo)

        assert result["node_type"] == "Artifact"
        assert result["source"] == "github"
        assert result["title"] == "Fix authentication bug"
        assert result["content"] == "This PR fixes the auth issue"
        assert result["artifact_type"] == "pull_request"
        assert result["status"] == "open"

    def test_pr_to_artifact_merged(self) -> None:
        """Merged PR has status=merged."""
        pr = {
            "number": 1,
            "title": "Merge PR",
            "state": "closed",
            "merged_at": "2026-05-01T10:00:00Z",
        }
        result = self.normalizer.pr_to_artifact(pr, self.repo)
        assert result["status"] == "merged"

    def test_pr_to_artifact_draft(self) -> None:
        """Draft PR has status=draft."""
        pr = {
            "number": 2,
            "title": "WIP: Draft PR",
            "state": "open",
            "draft": True,
            "merged_at": None,
        }
        result = self.normalizer.pr_to_artifact(pr, self.repo)
        assert result["status"] == "draft"

    def test_pr_to_artifact_closed_not_merged(self) -> None:
        """Closed (not merged) PR has status=closed."""
        pr = {
            "number": 3,
            "title": "Abandoned PR",
            "state": "closed",
            "merged_at": None,
        }
        result = self.normalizer.pr_to_artifact(pr, self.repo)
        assert result["status"] == "closed"


class TestGitHubNormalizerIssue:
    """Tests for issue_to_signal_or_artifact()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)
        self.repo = "owner/repo"

    def test_open_issue_to_signal(self) -> None:
        """Open GitHub issue maps to Signal."""
        issue = {
            "number": 10,
            "title": "Bug: login fails",
            "body": "Cannot log in",
            "state": "open",
            "html_url": "https://github.com/owner/repo/issues/10",
        }
        result = self.normalizer.issue_to_signal_or_artifact(issue, self.repo)

        assert result["node_type"] == "Signal"
        assert result["source"] == "github"

    def test_closed_issue_to_artifact(self) -> None:
        """Closed GitHub issue maps to Artifact."""
        issue = {
            "number": 11,
            "title": "Completed feature",
            "body": "Feature implemented",
            "state": "closed",
        }
        result = self.normalizer.issue_to_signal_or_artifact(issue, self.repo)

        assert result["node_type"] == "Artifact"
        assert result["artifact_type"] == "issue"
        assert result["status"] == "closed"


class TestGitHubNormalizerMilestone:
    """Tests for milestone_to_goal()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)

    def test_milestone_to_goal(self) -> None:
        """GitHub milestone maps to Goal."""
        milestone = {
            "number": 5,
            "title": "v2.0 Release",
            "description": "Major release milestone",
            "state": "open",
            "due_on": "2026-06-01T00:00:00Z",
            "html_url": "https://github.com/owner/repo/milestone/5",
        }
        result = self.normalizer.milestone_to_goal(milestone, "owner/repo")

        assert result["node_type"] == "Goal"
        assert result["source"] == "github"
        assert result["title"] == "v2.0 Release"
        assert result["status"] == "open"
        assert result["due_date"] == "2026-06-01T00:00:00Z"

    def test_closed_milestone_to_goal_done(self) -> None:
        """Closed milestone maps to status=done."""
        milestone = {"number": 1, "title": "v1.0", "state": "closed"}
        result = self.normalizer.milestone_to_goal(milestone, "owner/repo")
        assert result["status"] == "done"


class TestGitHubNormalizerUser:
    """Tests for user_to_actor()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)

    def test_user_to_actor(self) -> None:
        """GitHub user maps to Actor with login as name fallback."""
        user = {
            "id": 999,
            "login": "johndoe",
            "name": "John Doe",
            "email": "john@example.com",
        }
        result = self.normalizer.user_to_actor(user)

        assert result["node_type"] == "Actor"
        assert result["source"] == "github"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert "github" in result["identities"]

    def test_user_to_actor_login_fallback(self) -> None:
        """Actor uses login as name when name is not set."""
        user = {"id": 1, "login": "noname_user", "name": None}
        result = self.normalizer.user_to_actor(user)
        assert result["name"] == "noname_user"


class TestGitHubNormalizerReview:
    """Tests for review_to_signal()."""

    def setup_method(self) -> None:
        from context_os.ingestion.github.normalizer import GitHubNormalizer

        self.normalizer = GitHubNormalizer(tenant_id=TENANT_ID)

    def test_review_to_signal(self) -> None:
        """GitHub PR review maps to Signal with signal_type=review."""
        review = {
            "id": 777,
            "state": "APPROVED",
            "body": "LGTM! Great work.",
            "submitted_at": "2026-05-10T15:30:00Z",
            "html_url": "https://github.com/owner/repo/pull/42#pullrequestreview-777",
        }
        result = self.normalizer.review_to_signal(review, "owner/repo", 42)

        assert result["node_type"] == "Signal"
        assert result["signal_type"] == "review"
        assert "APPROVED" in result["content"]
        assert "LGTM" in result["content"]
        assert result["occurred_at"] == "2026-05-10T15:30:00Z"


# ── Jira Normalizer Tests ──────────────────────────────────────────────────────


class TestJiraNormalizerProject:
    """Tests for project_to_initiative()."""

    def setup_method(self) -> None:
        from context_os.ingestion.jira.normalizer import JiraNomalizer

        self.normalizer = JiraNomalizer(tenant_id=TENANT_ID)

    def test_project_to_initiative(self) -> None:
        """Jira project maps to Initiative."""
        project = {
            "id": "10001",
            "key": "PROJ",
            "name": "My Project",
            "description": "Project description",
            "self": "https://mysite.atlassian.net/rest/api/3/project/10001",
        }
        result = self.normalizer.project_to_initiative(project)

        assert result["node_type"] == "Initiative"
        assert result["source"] == "jira"
        assert result["title"] == "My Project"
        assert result["status"] == "active"

    def test_project_has_base_fields(self) -> None:
        """Jira project result has all required fields."""
        project = {"id": "1", "name": "Test"}
        result = self.normalizer.project_to_initiative(project)

        for field in ("id", "tenant_id", "source", "source_id", "fetch_ts"):
            assert field in result


class TestJiraNormalizerEpic:
    """Tests for epic_to_goal()."""

    def setup_method(self) -> None:
        from context_os.ingestion.jira.normalizer import JiraNomalizer

        self.normalizer = JiraNomalizer(tenant_id=TENANT_ID)

    def test_epic_to_goal(self) -> None:
        """Jira epic maps to Goal."""
        epic = {
            "id": "10050",
            "key": "PROJ-1",
            "fields": {
                "summary": "Epic: New UI Design",
                "description": "Redesign the user interface",
                "status": {"name": "In Progress"},
                "duedate": "2026-07-01",
            },
        }
        result = self.normalizer.epic_to_goal(epic)

        assert result["node_type"] == "Goal"
        assert result["source"] == "jira"
        assert result["title"] == "Epic: New UI Design"
        assert result["status"] == "in_progress"
        assert result["due_date"] == "2026-07-01"


class TestJiraNormalizerIssue:
    """Tests for issue_to_signal_or_artifact()."""

    def setup_method(self) -> None:
        from context_os.ingestion.jira.normalizer import JiraNomalizer

        self.normalizer = JiraNomalizer(tenant_id=TENANT_ID)

    def test_done_issue_to_artifact(self) -> None:
        """Jira issue with status Done maps to Artifact."""
        issue = {
            "id": "10100",
            "fields": {
                "summary": "Completed task",
                "description": "Task description",
                "status": {"name": "Done"},
            },
        }
        result = self.normalizer.issue_to_signal_or_artifact(issue)

        assert result["node_type"] == "Artifact"
        assert result["artifact_type"] == "issue"
        assert result["title"] == "Completed task"

    def test_inprogress_issue_to_signal(self) -> None:
        """Jira issue with status In Progress maps to Signal."""
        issue = {
            "id": "10101",
            "fields": {
                "summary": "Work in progress",
                "status": {"name": "In Progress"},
            },
        }
        result = self.normalizer.issue_to_signal_or_artifact(issue)

        assert result["node_type"] == "Signal"
        assert result["signal_type"] == "status_change"


class TestJiraNormalizerUser:
    """Tests for user_to_actor()."""

    def setup_method(self) -> None:
        from context_os.ingestion.jira.normalizer import JiraNomalizer

        self.normalizer = JiraNomalizer(tenant_id=TENANT_ID)

    def test_user_to_actor(self) -> None:
        """Jira user maps to Actor with displayName as name."""
        user = {
            "accountId": "abc123",
            "displayName": "Jane Smith",
            "emailAddress": "jane@example.com",
        }
        result = self.normalizer.user_to_actor(user)

        assert result["node_type"] == "Actor"
        assert result["source"] == "jira"
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane@example.com"
        assert "jira" in result["identities"]


# ── Slack Normalizer Tests ─────────────────────────────────────────────────────


class TestSlackNormalizerMessage:
    """Tests for message_to_signal()."""

    def setup_method(self) -> None:
        from context_os.ingestion.slack.normalizer import SlackNormalizer

        self.normalizer = SlackNormalizer(tenant_id=TENANT_ID)

    def test_message_to_signal(self) -> None:
        """Slack message maps to Signal."""
        msg = {
            "ts": "1716012345.678901",
            "text": "Hello team, check this PR: https://github.com/org/repo/pull/42",
            "user": "U0123ABCDEF",
        }
        result = self.normalizer.message_to_signal(msg, "C0CHANNEL")

        assert result["node_type"] == "Signal"
        assert result["source"] == "slack"
        assert result["signal_type"] == "message"
        assert result["content"] == msg["text"]

    def test_message_ts_to_occurred_at_iso(self) -> None:
        """Slack ts (Unix timestamp) is converted to ISO 8601 occurred_at."""
        msg = {"ts": "1716012345.678901", "text": "test"}
        result = self.normalizer.message_to_signal(msg, "C0123")

        occurred_at = result["occurred_at"]
        # Should be a valid ISO 8601 datetime string
        assert "T" in occurred_at, f"occurred_at should be ISO 8601: {occurred_at}"
        # Parse to verify it's a valid datetime
        dt = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        assert dt.year == 2024, "2026-05-18 unix ts 1716012345 corresponds to 2024"

    def test_message_has_source_id(self) -> None:
        """Signal source_id includes channel and ts."""
        msg = {"ts": "1716012345.123456", "text": "hello"}
        result = self.normalizer.message_to_signal(msg, "C0CHANNEL")
        assert "C0CHANNEL" in result["source_id"]
        assert "1716012345" in result["source_id"]


class TestSlackNormalizerUser:
    """Tests for user_to_actor()."""

    def setup_method(self) -> None:
        from context_os.ingestion.slack.normalizer import SlackNormalizer

        self.normalizer = SlackNormalizer(tenant_id=TENANT_ID)

    def test_user_to_actor(self) -> None:
        """Slack user maps to Actor with real_name as name."""
        user = {
            "id": "U0123",
            "name": "jdoe",
            "real_name": "John Doe",
            "profile": {"email": "jdoe@example.com", "display_name": "jdoe"},
        }
        result = self.normalizer.user_to_actor(user)

        assert result["node_type"] == "Actor"
        assert result["source"] == "slack"
        assert result["name"] == "John Doe"
        assert result["email"] == "jdoe@example.com"


class TestSlackNormalizerPRExtraction:
    """Tests for extract_github_pr_refs()."""

    def setup_method(self) -> None:
        from context_os.ingestion.slack.normalizer import SlackNormalizer

        self.normalizer = SlackNormalizer(tenant_id=TENANT_ID)

    def test_extract_pr_ref_from_text(self) -> None:
        """GitHub PR URLs extracted from Slack message text."""
        text = "Hey, reviewed https://github.com/org/repo/pull/42 and LGTM!"
        refs = self.normalizer.extract_github_pr_refs(text)
        assert len(refs) == 1
        assert "pull/42" in refs[0]

    def test_extract_multiple_pr_refs(self) -> None:
        """Multiple GitHub PR URLs all extracted."""
        text = (
            "See https://github.com/org/repo/pull/1 and "
            "https://github.com/org/other/pull/99 for context"
        )
        refs = self.normalizer.extract_github_pr_refs(text)
        assert len(refs) == 2

    def test_no_pr_refs_in_plain_text(self) -> None:
        """Text without PR URLs returns empty list."""
        text = "Just a regular message with no GitHub links"
        refs = self.normalizer.extract_github_pr_refs(text)
        assert refs == []

    def test_empty_text_returns_empty(self) -> None:
        """Empty/None text returns empty list."""
        assert self.normalizer.extract_github_pr_refs("") == []
        assert self.normalizer.extract_github_pr_refs(None) == []  # type: ignore[arg-type]
