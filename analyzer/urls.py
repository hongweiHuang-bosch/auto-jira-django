
from django.urls import path
from .views import TaskGroupListView, TaskGroupStreamView, TaskStartView, TaskDetailView, ResultListView, ResultUpdateView, ResultCommentView

urlpatterns = [
    path('tasks/groups/', TaskGroupListView.as_view(), name='task-groups'),
    path('tasks/stream/', TaskGroupStreamView.as_view(), name='task-stream'),
    path('tasks/start/', TaskStartView.as_view(), name='task-start'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('results/', ResultListView.as_view(), name='result-list'),
    path('results/<int:pk>/save/', ResultUpdateView.as_view(), name='result-save'),
    path('results/<int:pk>/comment/', ResultCommentView.as_view(), name='result-comment'),
]
