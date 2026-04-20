from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from analyzer.models import (
    FilterTask,
    FilteredIssueSnapshot,
    IssueProcessResult,
    IssueProcessTask,
)


class TaskDomainModelTests(TestCase):
    def test_filter_task_is_expired_property(self):
        task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertTrue(task.is_expired)

    def test_snapshot_is_unique_per_filter_task(self):
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-1',
            summary='黑屏问题',
            assignee='alice',
        )

        with self.assertRaises(IntegrityError):
            FilteredIssueSnapshot.objects.create(
                filter_task=filter_task,
                issue_key='CHER-1',
                summary='黑屏问题',
                assignee='alice',
            )

    def test_process_result_is_one_to_one_with_process_task(self):
        filter_task = FilterTask.objects.create(
            role_index=0,
            role_label='规则组 1',
            jql='project = CHER',
            status='SUCCESS',
            expires_at=timezone.now() + timedelta(hours=24),
        )
        snapshot = FilteredIssueSnapshot.objects.create(
            filter_task=filter_task,
            issue_key='CHER-2',
            summary='花屏问题',
            assignee='bob',
        )
        process_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=snapshot,
            issue_key='CHER-2',
            summary='花屏问题',
            status='SUCCESS',
        )
        IssueProcessResult.objects.create(
            process_task=process_task,
            issue_key='CHER-2',
            summary='花屏问题',
        )

        with self.assertRaises(IntegrityError):
            IssueProcessResult.objects.create(
                process_task=process_task,
                issue_key='CHER-2',
                summary='重复结果',
            )
