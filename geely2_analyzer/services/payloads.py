from django.db.models import OuterRef, Subquery

from geely2_analyzer.models import Geely2AnalysisResult, Geely2AnalysisTask, Geely2IssueSnapshot, Geely2SyncTask


def build_issue_list_payload(user):
    latest_sync = Geely2SyncTask.objects.filter(user=user).order_by('-created_at').first()
    latest_task_ids = Geely2AnalysisTask.objects.filter(issue_snapshot_id=OuterRef('pk')).order_by('-created_at')
    latest_result_ids = Geely2AnalysisResult.objects.filter(
        analysis_task__issue_snapshot_id=OuterRef('pk')
    ).order_by('-created_at')
    items = list(
        Geely2IssueSnapshot.objects.filter(user=user)
        .annotate(
            latest_analysis_task_id=Subquery(latest_task_ids.values('id')[:1]),
            latest_result_id=Subquery(latest_result_ids.values('id')[:1]),
        )
        .order_by('issue_key')
        .values(
            'id',
            'issue_key',
            'summary',
            'assignee',
            'jira_updated_at',
            'current_analysis_status',
            'latest_analysis_task_id',
            'latest_result_id',
        )
    )
    for item in items:
        jira_updated_at = item.get('jira_updated_at')
        if jira_updated_at is not None:
            item['jira_updated_at'] = jira_updated_at.isoformat()
    return {
        'latest_sync_task': None if latest_sync is None else {
            'id': latest_sync.id,
            'status': latest_sync.status,
            'issue_count': latest_sync.issue_count,
            'message': latest_sync.message,
            'error_code': latest_sync.error_code,
            'error_message': latest_sync.error_message,
        },
        'items': items,
    }