from django.urls import path

from .views import CredentialView, Geely2StreamView, IssueListView, SyncTaskCreateView, SyncTaskDetailView


urlpatterns = [
    path('credential/', CredentialView.as_view(), name='geely2-credential'),
    path('sync-tasks/', SyncTaskCreateView.as_view(), name='geely2-sync-create'),
    path('sync-tasks/<int:pk>/', SyncTaskDetailView.as_view(), name='geely2-sync-detail'),
    path('issues/', IssueListView.as_view(), name='geely2-issue-list'),
    path('stream/', Geely2StreamView.as_view(), name='geely2-stream'),
]