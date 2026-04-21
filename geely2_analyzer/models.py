from django.conf import settings
from django.db import models


class JiraCredentialBinding(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jira_bindings",
    )
    project_code = models.CharField(max_length=32, default="geely2")
    jira_base_url = models.URLField(default="https://boolbool.atlassian.net/")
    jira_username = models.CharField(max_length=255)
    encrypted_password = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "project_code")


class Geely2SyncTask(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("RUNNING", "RUNNING"),
        ("SUCCESS", "SUCCESS"),
        ("FAILED", "FAILED"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geely2_sync_tasks",
    )
    credential_binding = models.ForeignKey(
        JiraCredentialBinding,
        on_delete=models.CASCADE,
        related_name="sync_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    issue_count = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default="")
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class Geely2IssueSnapshot(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geely2_issue_snapshots",
    )
    last_sync_task = models.ForeignKey(
        Geely2SyncTask,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="snapshots",
    )
    issue_key = models.CharField(max_length=64)
    summary = models.CharField(max_length=500, blank=True, default="")
    assignee = models.CharField(max_length=255, blank=True, default="")
    jira_updated_at = models.DateTimeField(null=True, blank=True)
    current_analysis_status = models.CharField(max_length=20, default="IDLE")
    latest_analysis_task_id = models.PositiveIntegerField(null=True, blank=True)
    latest_result_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["issue_key"]
        unique_together = ("user", "issue_key")


class Geely2AnalysisTask(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "PENDING"),
        ("RUNNING", "RUNNING"),
        ("SUCCESS", "SUCCESS"),
        ("FAILED", "FAILED"),
    ]
    STAGE_CHOICES = [
        ("FETCH_COMMENTS", "FETCH_COMMENTS"),
        ("EXTRACT_RELATED_SIGNALS", "EXTRACT_RELATED_SIGNALS"),
        ("DOWNLOAD_ARCHIVES", "DOWNLOAD_ARCHIVES"),
        ("UNPACK_QNX_LOG", "UNPACK_QNX_LOG"),
        ("SELECT_TARGET_CYCLES", "SELECT_TARGET_CYCLES"),
        ("FILTER_BOSCH_LOGS", "FILTER_BOSCH_LOGS"),
        ("EXTRACT_UPPER_REQUIREMENTS", "EXTRACT_UPPER_REQUIREMENTS"),
        ("AI_ANALYZE", "AI_ANALYZE"),
        ("SAVE_RESULT", "SAVE_RESULT"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geely2_analysis_tasks",
    )
    credential_binding = models.ForeignKey(
        JiraCredentialBinding,
        on_delete=models.CASCADE,
        related_name="analysis_tasks",
    )
    issue_snapshot = models.ForeignKey(
        Geely2IssueSnapshot,
        on_delete=models.CASCADE,
        related_name="analysis_tasks",
    )
    issue_key = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    stage = models.CharField(max_length=64, choices=STAGE_CHOICES, default="FETCH_COMMENTS")
    progress = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default="")
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    workspace_dir = models.CharField(max_length=500, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class Geely2AnalysisResult(models.Model):
    COMMENT_STATUS_CHOICES = [
        ("NOT_CONFIRMED", "NOT_CONFIRMED"),
        ("CONFIRMED_NOT_COMMENTED", "CONFIRMED_NOT_COMMENTED"),
        ("COMMENTED", "COMMENTED"),
        ("COMMENT_FAILED", "COMMENT_FAILED"),
    ]

    analysis_task = models.OneToOneField(
        Geely2AnalysisTask,
        on_delete=models.CASCADE,
        related_name="result",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="geely2_results",
    )
    issue_key = models.CharField(max_length=64)
    ai_summary = models.TextField(blank=True, default="")
    reply_text = models.TextField(blank=True, default="")
    evidence_payload = models.JSONField(default=dict)
    confidence = models.FloatField(default=0)
    risk_notes = models.TextField(blank=True, default="")
    needs_user_confirmation = models.BooleanField(default=True)
    comment_status = models.CharField(
        max_length=32,
        choices=COMMENT_STATUS_CHOICES,
        default="NOT_CONFIRMED",
    )
    commented_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
