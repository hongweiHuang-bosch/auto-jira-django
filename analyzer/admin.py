
from django.contrib import admin
from .models import AnalysisTask, IssueAnalysisResult

@admin.register(AnalysisTask)
class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'progress', 'created_at')
    search_fields = ('name', 'message')

@admin.register(IssueAnalysisResult)
class IssueAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'issue_key', 'model', 'result_status', 'has_commented_to_jira', 'created_at')
    search_fields = ('issue_key', 'summary', 'reply_text')
    list_filter = ('result_status', 'has_commented_to_jira', 'model')
