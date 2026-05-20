
from django.db import models
from django.utils import timezone


class AnalysisTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('RUNNING', 'RUNNING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
    ]

    name = models.CharField(max_length=200, default='Jira分析任务')
    role_index = models.PositiveIntegerField(default=0, db_index=True)
    role_label = models.CharField(max_length=200, blank=True, default='')
    jql = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default='')
    total_groups = models.PositiveIntegerField(default=0)
    finished_groups = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class IssueAnalysisResult(models.Model):
    RESULT_STATUS_CHOICES = [
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
        ('MANUAL', 'MANUAL'),
    ]

    task = models.ForeignKey(AnalysisTask, on_delete=models.CASCADE, related_name='results')
    issue_key = models.CharField(max_length=64)
    summary = models.CharField(max_length=500, blank=True, default='')
    model = models.CharField(max_length=100, blank=True, default='')
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS_CHOICES, default='SUCCESS')
    reply_text = models.TextField(blank=True, default='')
    can_trace_image = models.CharField(max_length=500, blank=True, default='')
    can_trace_image_url = models.CharField(max_length=500, blank=True, default='')
    raw_signals = models.TextField(blank=True, default='')
    has_commented_to_jira = models.BooleanField(default=False)
    commented_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('task', 'issue_key')


class FilterTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('RUNNING', 'RUNNING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
        ('EXPIRED', 'EXPIRED'),
    ]

    role_index = models.PositiveIntegerField(db_index=True)
    role_label = models.CharField(max_length=200, blank=True, default='')
    jql = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    issue_count = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())


class FilteredIssueSnapshot(models.Model):
    filter_task = models.ForeignKey(FilterTask, on_delete=models.CASCADE, related_name='issues')
    issue_key = models.CharField(max_length=64)
    summary = models.CharField(max_length=500, blank=True, default='')
    assignee = models.CharField(max_length=200, blank=True, default='')
    issue_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['issue_key']
        unique_together = ('filter_task', 'issue_key')


class IssueProcessTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('RUNNING', 'RUNNING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
    ]
    STAGE_CHOICES = [
        ('PREPARING', 'PREPARING'),
        ('DOWNLOADING', 'DOWNLOADING'),
        ('UNPACKING', 'UNPACKING'),
        ('PARSING', 'PARSING'),
        ('MODEL_INFERENCE', 'MODEL_INFERENCE'),
        ('GENERATING_REPLY', 'GENERATING_REPLY'),
        ('SAVING_RESULT', 'SAVING_RESULT'),
    ]

    filter_task = models.ForeignKey(FilterTask, on_delete=models.CASCADE, related_name='process_tasks')
    snapshot = models.ForeignKey(FilteredIssueSnapshot, on_delete=models.CASCADE, related_name='process_tasks')
    issue_key = models.CharField(max_length=64, db_index=True)
    summary = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    stage = models.CharField(max_length=40, choices=STAGE_CHOICES, default='PREPARING')
    progress = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class IssueProcessResult(models.Model):
    RESULT_STATUS_CHOICES = [
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
        ('MANUAL', 'MANUAL'),
    ]
    REVIEW_STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
    ]

    process_task = models.OneToOneField(IssueProcessTask, on_delete=models.CASCADE, related_name='result')
    issue_key = models.CharField(max_length=64)
    summary = models.CharField(max_length=500, blank=True, default='')
    model = models.CharField(max_length=100, blank=True, default='')
    result_status = models.CharField(max_length=20, choices=RESULT_STATUS_CHOICES, default='SUCCESS')
    reply_text = models.TextField(blank=True, default='')
    upper_comment = models.TextField(blank=True, null=True, default='')
    can_trace_image = models.CharField(max_length=500, blank=True, default='')
    can_trace_image_url = models.CharField(max_length=500, blank=True, default='')
    raw_signals = models.TextField(blank=True, default='')
    has_commented_to_jira = models.BooleanField(default=False)
    commented_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='PENDING')
    review_reason = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_model = models.CharField(max_length=100, blank=True, default='')
    manual_override_after_review = models.BooleanField(default=False)
    manual_error_reason = models.TextField(blank=True, default='')
    manual_correct_result = models.TextField(blank=True, default='')
    manual_review_saved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class IssueReviewSample(models.Model):
    role_index = models.PositiveIntegerField(db_index=True)
    issue_key = models.CharField(max_length=64)
    incorrect_conclusion = models.TextField()
    correct_conclusion = models.TextField()
    error_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']


class IssueLearningMemory(models.Model):
    role_index = models.PositiveIntegerField(db_index=True)
    issue_key = models.CharField(max_length=64)
    review_status = models.CharField(max_length=20, blank=True, default='')
    incorrect_conclusion = models.TextField(blank=True, default='')
    correct_conclusion = models.TextField(blank=True, default='')
    error_reason = models.TextField(blank=True, default='')
    signal_summary = models.TextField(blank=True, default='')
    memory_file_path = models.CharField(max_length=500, blank=True, default='')
    memory_content_hash = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        unique_together = ('role_index', 'issue_key')


class IssueValidationRun(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('RUNNING', 'RUNNING'),
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
    ]
    VERDICT_CHOICES = [
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
        ('WARNING', 'WARNING'),
        ('UNKNOWN', 'UNKNOWN'),
    ]

    process_result = models.ForeignKey(
        IssueProcessResult,
        on_delete=models.CASCADE,
        related_name='validation_runs',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    system_verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES, default='UNKNOWN')
    summary_reason = models.TextField(blank=True, default='')
    evidence_payload = models.JSONField(default=dict, blank=True)
    chart_payload = models.JSONField(default=dict, blank=True)
    ruleset_version = models.CharField(max_length=50, blank=True, default='v1')
    error_message = models.TextField(blank=True, default='')
    manual_verdict = models.CharField(max_length=20, blank=True, default='')
    manual_reason = models.TextField(blank=True, default='')
    manual_note = models.TextField(blank=True, default='')
    manual_operator = models.CharField(max_length=150, blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    manual_saved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class IssueValidationCheck(models.Model):
    validation_run = models.ForeignKey(
        IssueValidationRun,
        on_delete=models.CASCADE,
        related_name='checks',
    )
    check_type = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=IssueValidationRun.VERDICT_CHOICES,
        default='UNKNOWN',
    )
    title = models.CharField(max_length=200)
    reason = models.TextField(blank=True, default='')
    evidence_payload = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'id']
        unique_together = ('validation_run', 'check_type')
