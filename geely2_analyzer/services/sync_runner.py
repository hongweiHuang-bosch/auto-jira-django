import logging

from django.utils import timezone

from geely2_analyzer.models import Geely2IssueSnapshot, Geely2SyncTask
from geely2_analyzer.services.client_factory import build_jira_client
from geely2_analyzer.services.stream import publish_geely2_snapshot

logger = logging.getLogger('geely2_analyzer')


def run_sync_task(task_id):
    task = Geely2SyncTask.objects.select_related('credential_binding', 'user').get(pk=task_id)
    try:
        jira_client = build_jira_client(task.credential_binding)
        issues = jira_client.search_issues(
            'assignee = currentUser() ORDER BY updated DESC',
            expand='changelog',
        )

        seen_issue_keys = []
        for issue in issues:
            assignee = getattr(getattr(issue.fields, 'assignee', None), 'displayName', '')
            Geely2IssueSnapshot.objects.update_or_create(
                user=task.user,
                issue_key=issue.key,
                defaults={
                    'last_sync_task': task,
                    'summary': issue.fields.summary,
                    'assignee': assignee,
                    'jira_updated_at': timezone.now(),
                },
            )
            seen_issue_keys.append(issue.key)

        Geely2IssueSnapshot.objects.filter(user=task.user).exclude(
            issue_key__in=seen_issue_keys
        ).delete()

        task.status = 'SUCCESS'
        task.issue_count = len(seen_issue_keys)
        task.finished_at = timezone.now()
        task.message = f'同步完成，共 {len(seen_issue_keys)} 张票'
        task.save(update_fields=['status', 'issue_count', 'finished_at', 'message', 'updated_at'])
    except Exception as exc:
        task.status = 'FAILED'
        task.finished_at = timezone.now()
        task.error_message = str(exc)
        task.message = '同步失败'
        task.save(update_fields=['status', 'finished_at', 'error_message', 'message', 'updated_at'])
        logger.exception('Sync task %s failed', task_id)
        return

    publish_geely2_snapshot(task.user)
