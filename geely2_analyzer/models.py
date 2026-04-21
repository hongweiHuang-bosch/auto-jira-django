from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

from .services.credential_crypto import encrypt_secret


def _validate_same_user(errors, field_name, related_user_id, user_id):
    if related_user_id is not None and user_id is not None and related_user_id != user_id:
        errors[field_name] = 'Must belong to the same user.'


def _prepare_for_persist(instance):
    prepare = getattr(instance, '_prepare_for_save', None)
    if callable(prepare):
        prepare()
    instance.full_clean(validate_unique=False)


def _persisted_values(instance, *fields):
    if not instance.pk:
        return None
    return type(instance)._base_manager.filter(pk=instance.pk).values(*fields).first()


def _safe_related_value(instance, field_name, attr_name):
    relation_id = getattr(instance, f'{field_name}_id', None)
    if relation_id is None:
        return None

    try:
        related = getattr(instance, field_name)
    except ObjectDoesNotExist:
        return None

    return getattr(related, attr_name, None)


class ValidatedRelationQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            _prepare_for_persist(obj)
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        for obj in objs:
            _prepare_for_persist(obj)
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def update(self, **kwargs):
        raise RuntimeError(
            'Use model save() or bulk_update() with validated instances instead of QuerySet.update().'
        )


class ValidatedRelationManager(models.Manager.from_queryset(ValidatedRelationQuerySet)):
    pass


class ValidatedRelationModel(models.Model):
    objects = ValidatedRelationManager()

    class Meta:
        abstract = True
        base_manager_name = 'objects'
        default_manager_name = 'objects'

    def save(self, *args, **kwargs):
        _prepare_for_persist(self)
        return super().save(*args, **kwargs)


class JiraCredentialBinding(ValidatedRelationModel):
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
        base_manager_name = 'objects'
        default_manager_name = 'objects'
        unique_together = ("user", "project_code")

    def clean(self):
        errors = {}
        user_id = getattr(self, 'user_id', None)
        persisted = _persisted_values(self, 'user_id')
        if persisted and persisted['user_id'] != user_id:
            errors['user'] = 'Cannot change user after creation.'
        if errors:
            raise ValidationError(errors)

    def _prepare_for_save(self):
        if not self.encrypted_password:
            return

        persisted = _persisted_values(self, 'encrypted_password')
        if persisted and persisted['encrypted_password'] == self.encrypted_password:
            return

        if self.encrypted_password:
            self.encrypted_password = encrypt_secret(self.encrypted_password)


class Geely2SyncTask(ValidatedRelationModel):
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
        base_manager_name = 'objects'
        default_manager_name = 'objects'
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        user_id = getattr(self, 'user_id', None)
        credential_binding_id = getattr(self, 'credential_binding_id', None)
        related_user_id = _safe_related_value(self, 'credential_binding', 'user_id')
        _validate_same_user(errors, 'credential_binding', related_user_id, user_id)
        if self.status in {'PENDING', 'RUNNING'} and user_id is not None:
            running_tasks = Geely2SyncTask.objects.filter(
                user_id=user_id,
                status__in=['PENDING', 'RUNNING'],
            )
            if self.pk:
                running_tasks = running_tasks.exclude(pk=self.pk)
            if running_tasks.exists():
                errors['status'] = 'Another pending or running sync task already exists for this user.'
        persisted = _persisted_values(self, 'user_id', 'credential_binding_id')
        if persisted:
            if persisted['user_id'] != user_id:
                errors['user'] = 'Cannot change user after creation.'
            if persisted['credential_binding_id'] != credential_binding_id:
                errors['credential_binding'] = 'Cannot change credential_binding after creation.'
        if errors:
            raise ValidationError(errors)


class Geely2IssueSnapshot(ValidatedRelationModel):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        base_manager_name = 'objects'
        default_manager_name = 'objects'
        ordering = ["issue_key"]
        unique_together = ("user", "issue_key")

    def clean(self):
        errors = {}
        user_id = getattr(self, 'user_id', None)
        related_user_id = _safe_related_value(self, 'last_sync_task', 'user_id')
        _validate_same_user(errors, 'last_sync_task', related_user_id, user_id)
        persisted = _persisted_values(self, 'user_id', 'issue_key')
        if persisted:
            if persisted['user_id'] != user_id:
                errors['user'] = 'Cannot change user after creation.'
            if persisted['issue_key'] != self.issue_key:
                errors['issue_key'] = 'Cannot change issue_key after creation.'
        if errors:
            raise ValidationError(errors)


class Geely2AnalysisTask(ValidatedRelationModel):
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
        base_manager_name = 'objects'
        default_manager_name = 'objects'
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        user_id = getattr(self, 'user_id', None)
        credential_binding_id = getattr(self, 'credential_binding_id', None)
        issue_snapshot_id = getattr(self, 'issue_snapshot_id', None)
        binding_user_id = _safe_related_value(self, 'credential_binding', 'user_id')
        snapshot_user_id = _safe_related_value(self, 'issue_snapshot', 'user_id')
        _validate_same_user(errors, 'credential_binding', binding_user_id, user_id)
        _validate_same_user(errors, 'issue_snapshot', snapshot_user_id, user_id)
        snapshot_issue_key = _safe_related_value(self, 'issue_snapshot', 'issue_key')
        if snapshot_issue_key and self.issue_key and snapshot_issue_key != self.issue_key:
            errors['issue_key'] = 'Must match issue_snapshot.issue_key.'
        persisted = _persisted_values(self, 'user_id', 'issue_key', 'credential_binding_id', 'issue_snapshot_id')
        if persisted:
            if persisted['user_id'] != user_id:
                errors['user'] = 'Cannot change user after creation.'
            if persisted['issue_key'] != self.issue_key:
                errors['issue_key'] = 'Cannot change issue_key after creation.'
            if persisted['credential_binding_id'] != credential_binding_id:
                errors['credential_binding'] = 'Cannot change credential_binding after creation.'
            if persisted['issue_snapshot_id'] != issue_snapshot_id:
                errors['issue_snapshot'] = 'Cannot change issue_snapshot after creation.'
        if errors:
            raise ValidationError(errors)


class Geely2AnalysisResult(ValidatedRelationModel):
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
    evidence_payload = models.JSONField(default=dict, blank=True)
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

    class Meta:
        base_manager_name = 'objects'
        default_manager_name = 'objects'

    def clean(self):
        errors = {}
        user_id = getattr(self, 'user_id', None)
        analysis_task_id = getattr(self, 'analysis_task_id', None)
        related_user_id = _safe_related_value(self, 'analysis_task', 'user_id')
        _validate_same_user(errors, 'analysis_task', related_user_id, user_id)
        task_issue_key = _safe_related_value(self, 'analysis_task', 'issue_key')
        if task_issue_key and self.issue_key and task_issue_key != self.issue_key:
            errors['issue_key'] = 'Must match analysis_task.issue_key.'
        persisted = _persisted_values(self, 'analysis_task_id', 'user_id', 'issue_key')
        if persisted:
            if persisted['analysis_task_id'] != analysis_task_id:
                errors['analysis_task'] = 'Cannot change analysis_task after creation.'
            if persisted['user_id'] != user_id:
                errors['user'] = 'Cannot change user after creation.'
            if persisted['issue_key'] != self.issue_key:
                errors['issue_key'] = 'Cannot change issue_key after creation.'
        if errors:
            raise ValidationError(errors)

