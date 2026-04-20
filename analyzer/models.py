
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

    process_task = models.OneToOneField(IssueProcessTask, on_delete=models.CASCADE, related_name='result')
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
