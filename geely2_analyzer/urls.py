from django.urls import path

from .views import (
    AnalysisResultCommentView,
    AnalysisResultView,
    AnalysisTaskCreateView,
    AnalysisTaskDetailView,
    CredentialView,
    Geely2StreamView,
    IssueListView,
    SyncTaskCreateView,
    SyncTaskDetailView,
)


urlpatterns = [
    path('credential/', CredentialView.as_view(), name='geely2-credential'),
    path('sync-tasks/', SyncTaskCreateView.as_view(), name='geely2-sync-create'),
    path('sync-tasks/<int:pk>/', SyncTaskDetailView.as_view(), name='geely2-sync-detail'),
    path('issues/', IssueListView.as_view(), name='geely2-issue-list'),
    path('issues/<str:issue_key>/analysis-tasks/', AnalysisTaskCreateView.as_view(), name='geely2-analysis-create'),
    path('analysis-tasks/<int:pk>/', AnalysisTaskDetailView.as_view(), name='geely2-analysis-detail'),
    path('analysis-results/<int:pk>/', AnalysisResultView.as_view(), name='geely2-result-detail'),
    path('analysis-results/<int:pk>/comment/', AnalysisResultCommentView.as_view(), name='geely2-result-comment'),
    path('stream/', Geely2StreamView.as_view(), name='geely2-stream'),
]