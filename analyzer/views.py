
from __future__ import annotations
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AnalysisTask, IssueAnalysisResult, FilterTask, FilteredIssueSnapshot, IssueProcessTask, IssueProcessResult
from .serializers import AnalysisTaskSerializer, IssueAnalysisResultSerializer, FilterTaskSerializer, IssueProcessTaskSerializer, IssueProcessResultSerializer
from .services.task_executor import submit_analysis_task
from .services.task_catalog import get_role_entry, get_role_label
from .services.task_stream import build_group_payload, publish_groups_snapshot, stream_group_events
from .services.rule_group_payload import build_rule_group_payload, get_latest_filter_task_detail, get_filter_task_issue_page
from .services.rule_group_stream import publish_rule_group_snapshot, stream_rule_group_events
from legacy_core.utils import load_config
from legacy_core.jira_utils import JiraClient


class IndexView(TemplateView):
    template_name = 'index.html'


# 开始分析按钮后端请求
class TaskStartView(APIView):
    def post(self, request):
        try:
            role_index = int(request.data.get('role_index'))
            role_entry = get_role_entry(role_index)
        except (TypeError, ValueError, IndexError):
            return Response({'detail': '无效的规则组索引'}, status=status.HTTP_400_BAD_REQUEST)

        #  db中存在 PENDING 或者RUNNING 的任务，不可以执行任务，显示冲突
        running_task = AnalysisTask.objects.filter(
            role_index=role_index,
            status__in=['PENDING', 'RUNNING'],
        ).order_by('-created_at').first()
        if running_task is not None:
            return Response({
                'detail': '该规则组已有运行中的任务',
                'task_id': running_task.id,
            }, status=status.HTTP_409_CONFLICT)

        role_label = get_role_label(role_index, role_entry)
        task = AnalysisTask.objects.create(
            name=f'Jira 自动分析任务 - {role_label}',
            role_index=role_index,
            role_label=role_label,
            jql=role_entry.get('jql', ''),
            status='PENDING',
            message='任务已创建',
        )
        publish_groups_snapshot()
        submit_analysis_task(task.id)
        return Response({
            'task_id': task.id,
            'status': task.status,
            'role_index': task.role_index,
            'role_label': task.role_label,
        }, status=status.HTTP_201_CREATED)


class TaskGroupListView(APIView):
    def get(self, request):
        return Response(build_group_payload())


class TaskGroupStreamView(View):
    def get(self, request):
        response = StreamingHttpResponse(
            streaming_content=stream_group_events(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class TaskDetailView(APIView):
    def get(self, request, pk: int):
        task = get_object_or_404(AnalysisTask, pk=pk)
        return Response(AnalysisTaskSerializer(task).data)


class ResultListView(APIView):
    def get(self, request):
        task_id = request.query_params.get('task_id')
        qs = IssueAnalysisResult.objects.all()
        if task_id:
            qs = qs.filter(task_id=task_id)
        return Response(IssueAnalysisResultSerializer(qs, many=True).data)


class ResultUpdateView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueAnalysisResult, pk=pk)
        reply_text = request.data.get('reply_text')
        if reply_text is None:
            return Response({'detail': '缺少 reply_text 字段'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(reply_text, str):
            return Response({'detail': 'reply_text 必须是字符串'}, status=status.HTTP_400_BAD_REQUEST)

        result.reply_text = reply_text
        result.save(update_fields=['reply_text', 'updated_at'])
        publish_groups_snapshot()
        return Response({
            'detail': '保存成功',
            'result': IssueAnalysisResultSerializer(result).data,
        })


class ResultCommentView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueAnalysisResult, pk=pk)
        if result.has_commented_to_jira:
            return Response({'detail': '该结果已回填 Jira'}, status=status.HTTP_200_OK)

        cfg = load_config('config.yaml')
        jira_cfg = cfg['jira']
        jira = JiraClient(
            server=jira_cfg['server'],
            username=jira_cfg['username'],
            password=jira_cfg['password'],
        )
        if result.can_trace_image:
            jira.add_comment_with_image(result.issue_key, result.reply_text, result.can_trace_image)
        else:
            jira.add_comment(result.issue_key, result.reply_text)
        result.has_commented_to_jira = True
        result.commented_at = timezone.now()
        result.save(update_fields=['has_commented_to_jira', 'commented_at', 'updated_at'])
        publish_groups_snapshot()
        return Response({'detail': '已成功回填 Jira'})


# ==================== 新增：规则组筛票 & 单票处理 API ====================


class RuleGroupListView(APIView):
    def get(self, request):
        return Response(build_rule_group_payload())


class FilterTaskCreateView(APIView):
    def post(self, request, role_index: int):
        try:
            role_entry = get_role_entry(role_index)
        except (IndexError, ValueError):
            return Response({'detail': '无效的规则组索引'}, status=status.HTTP_400_BAD_REQUEST)

        running = FilterTask.objects.filter(role_index=role_index, status__in=['PENDING', 'RUNNING']).first()
        if running:
            if running.updated_at < timezone.now() - timedelta(seconds=30):
                running.status = 'EXPIRED'
                running.message = '筛票超时，已被新任务替换'
                running.save(update_fields=['status', 'message', 'updated_at'])
            else:
                return Response({'detail': '该规则组已有进行中的筛票任务', 'filter_task_id': running.id}, status=status.HTTP_409_CONFLICT)

        task = FilterTask.objects.create(
            role_index=role_index,
            role_label=get_role_label(role_index, role_entry),
            jql=role_entry.get('jql', ''),
            status='PENDING',
            message='筛票任务已创建',
        )
        publish_rule_group_snapshot()
        return Response(FilterTaskSerializer(task).data, status=status.HTTP_201_CREATED)


class LatestFilterTaskView(APIView):
    def get(self, request, role_index: int):
        include_issues = request.query_params.get('include_issues') == 'true'
        return Response(get_latest_filter_task_detail(role_index, include_issues=include_issues))


class FilterTaskIssueListView(APIView):
    def get(self, request, pk: int):
        task = get_object_or_404(FilterTask, pk=pk)
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        return Response(get_filter_task_issue_page(task, page=page, page_size=page_size))


class RuleGroupStreamView2(View):
    def get(self, request):
        response = StreamingHttpResponse(
            streaming_content=stream_rule_group_events(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class IssueProcessTaskCreateView(APIView):
    def post(self, request, filter_task_id: int, issue_key: str):
        filter_task = get_object_or_404(FilterTask, pk=filter_task_id)
        snapshot = get_object_or_404(FilteredIssueSnapshot, filter_task=filter_task, issue_key=issue_key)

        running = IssueProcessTask.objects.filter(issue_key=issue_key, status__in=['PENDING', 'RUNNING']).order_by('-created_at').first()
        if running is not None:
            return Response({'detail': '当前票已有进行中的处理任务', 'process_task_id': running.id}, status=status.HTTP_409_CONFLICT)

        process_task = IssueProcessTask.objects.create(
            filter_task=filter_task,
            snapshot=snapshot,
            issue_key=snapshot.issue_key,
            summary=snapshot.summary,
            status='PENDING',
            stage='PREPARING',
            message='单票处理任务已创建',
        )
        publish_rule_group_snapshot()
        return Response(IssueProcessTaskSerializer(process_task).data, status=status.HTTP_201_CREATED)


class IssueProcessTaskDetailView(APIView):
    def get(self, request, pk: int):
        task = get_object_or_404(IssueProcessTask, pk=pk)
        return Response(IssueProcessTaskSerializer(task).data)


class IssueProcessResultUpdateView(APIView):
    def patch(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        reply_text = request.data.get('reply_text')
        if not isinstance(reply_text, str):
            return Response({'detail': 'reply_text 必须是字符串'}, status=status.HTTP_400_BAD_REQUEST)

        result.reply_text = reply_text
        result.save(update_fields=['reply_text', 'updated_at'])
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)


class IssueProcessResultCommentView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        if result.has_commented_to_jira:
            return Response({'detail': '该结果已回填 Jira'}, status=status.HTTP_200_OK)

        cfg = load_config('config.yaml')
        jira_cfg = cfg['jira']
        jira = JiraClient(
            server=jira_cfg['server'],
            username=jira_cfg['username'],
            password=jira_cfg['password'],
        )
        if result.can_trace_image:
            jira.add_comment_with_image(result.issue_key, result.reply_text, result.can_trace_image)
        else:
            jira.add_comment(result.issue_key, result.reply_text)
        result.has_commented_to_jira = True
        result.commented_at = timezone.now()
        result.save(update_fields=['has_commented_to_jira', 'commented_at', 'updated_at'])
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)
