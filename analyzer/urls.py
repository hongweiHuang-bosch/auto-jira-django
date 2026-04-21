
from django.urls import path
from .views import (
    TaskGroupListView, TaskGroupStreamView, TaskStartView, TaskDetailView,
    ResultListView, ResultUpdateView, ResultCommentView,
    FilterTaskCreateView,
    IssueProcessTaskCreateView, IssueProcessTaskDetailView,
    IssueProcessResultUpdateView, IssueProcessResultCommentView,
)
from .views_rule_groups import (
    FilterTaskIssueListView,
    LatestFilterTaskView,
    RuleGroupDetailView,
    RuleGroupListView,
    RuleGroupStreamView,
)

urlpatterns = [
    path('tasks/groups/', TaskGroupListView.as_view(), name='task-groups'),
    path('tasks/stream/', TaskGroupStreamView.as_view(), name='task-stream'),
    path('tasks/start/', TaskStartView.as_view(), name='task-start'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('results/', ResultListView.as_view(), name='result-list'),
    path('results/<int:pk>/save/', ResultUpdateView.as_view(), name='result-save'),
    path('results/<int:pk>/comment/', ResultCommentView.as_view(), name='result-comment'),
    # 新增：规则组筛票 & 单票处理
    path('rule-groups/', RuleGroupListView.as_view(), name='rule-group-list'),
    path('rule-groups/stream/', RuleGroupStreamView.as_view(), name='rule-group-stream'),
    path('rule-groups/<int:role_index>/detail/', RuleGroupDetailView.as_view(), name='rule-group-detail'),
    path('rule-groups/<int:role_index>/filter-tasks/', FilterTaskCreateView.as_view(), name='filter-task-create'),
    path('rule-groups/<int:role_index>/filter-tasks/latest/', LatestFilterTaskView.as_view(), name='latest-filter-task'),
    path('filter-tasks/<int:pk>/issues/', FilterTaskIssueListView.as_view(), name='filter-task-issues'),
    path('filter-tasks/<int:filter_task_id>/issues/<str:issue_key>/process-tasks/', IssueProcessTaskCreateView.as_view(), name='issue-process-task-create'),
    path('process-tasks/<int:pk>/', IssueProcessTaskDetailView.as_view(), name='issue-process-task-detail'),
    path('process-results/<int:pk>/', IssueProcessResultUpdateView.as_view(), name='issue-process-result-update'),
    path('process-results/<int:pk>/comment/', IssueProcessResultCommentView.as_view(), name='issue-process-result-comment'),
]
