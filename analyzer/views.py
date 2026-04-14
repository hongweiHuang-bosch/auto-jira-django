
from __future__ import annotations
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AnalysisTask, IssueAnalysisResult
from .serializers import AnalysisTaskSerializer, IssueAnalysisResultSerializer
from .services.task_executor import submit_analysis_task
from .services.task_catalog import get_role_entry, get_role_label
from .services.task_stream import build_group_payload, publish_groups_snapshot, stream_group_events
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
        print("TaskStartView")
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
