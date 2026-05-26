
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
from .models import AnalysisTask, IssueAnalysisResult, FilterTask, FilteredIssueSnapshot, IssueProcessTask, IssueProcessResult, IssueReviewSample, IssueValidationRun
from .serializers import AnalysisTaskSerializer, IssueAnalysisResultSerializer, FilterTaskSerializer, IssueProcessTaskSerializer, IssueProcessResultSerializer, IssueValidationRunSerializer
from .services.issue_review_service import review_issue_result
from .services.learning_memory_service import delete_learning_memory, persist_learning_memory
from .services.bulk_task_actions import create_bulk_filter_tasks, create_bulk_issue_process_tasks, prepare_filter_task, prepare_issue_process_task
from .services.task_executor import submit_analysis_task
from .services.filter_task_executor import submit_filter_task
from .services.task_catalog import get_role_entry, get_role_label
from .services.task_stream import build_group_payload, publish_groups_snapshot, stream_group_events
from .services.rule_group_payload import build_rule_group_payload, get_latest_filter_task_detail, get_filter_task_issue_page
from .services.rule_group_stream import publish_rule_group_snapshot, stream_rule_group_events
from legacy_core.utils import load_config
from legacy_core.jira_utils import JiraClient


FILTER_TASK_STALE_TIMEOUT = timedelta(minutes=10)


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
            use_system_proxy=jira_cfg.get('use_system_proxy', True),
            proxies=jira_cfg.get('proxies'),
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
        outcome = prepare_filter_task(role_index)
        if outcome['status'] == 'failed':
            return Response({'detail': '无效的规则组索引'}, status=status.HTTP_400_BAD_REQUEST)

        task = outcome['task']
        if outcome['status'] == 'conflict':
            return Response({'detail': outcome['detail'], 'filter_task_id': task.id}, status=status.HTTP_409_CONFLICT)

        publish_rule_group_snapshot()
        submit_filter_task(task.id)
        return Response(FilterTaskSerializer(task).data, status=status.HTTP_201_CREATED)


class BulkFilterTaskCreateView(APIView):
    def post(self, request):
        payload, created_task_ids = create_bulk_filter_tasks()
        if created_task_ids:
            publish_rule_group_snapshot()
            for task_id in created_task_ids:
                submit_filter_task(task_id)
        return Response(payload, status=status.HTTP_201_CREATED)


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

        outcome = prepare_issue_process_task(filter_task, snapshot)
        process_task = outcome['task']
        if outcome['status'] == 'conflict':
            return Response({'detail': outcome['detail'], 'process_task_id': process_task.id}, status=status.HTTP_409_CONFLICT)

        publish_rule_group_snapshot()
        return Response(IssueProcessTaskSerializer(process_task).data, status=status.HTTP_201_CREATED)


class BulkIssueProcessTaskCreateView(APIView):
    def post(self, request):
        payload, created_any = create_bulk_issue_process_tasks()
        if created_any:
            publish_rule_group_snapshot()
        return Response(payload, status=status.HTTP_201_CREATED)


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

        edited_after_fail = result.review_status == 'FAIL' and reply_text != result.reply_text
        result.reply_text = reply_text
        if edited_after_fail:
            result.review_status = 'PENDING'
            result.review_reason = ''
            result.manual_override_after_review = False
            result.manual_error_reason = ''
            result.manual_correct_result = ''
            result.manual_review_saved_at = None
        result.save(update_fields=[
            'reply_text',
            'review_status',
            'review_reason',
            'manual_override_after_review',
            'manual_error_reason',
            'manual_correct_result',
            'manual_review_saved_at',
            'updated_at',
        ])
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)


class IssueProcessResultReviewView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        process_task = result.process_task
        samples = list(
            IssueReviewSample.objects.filter(role_index=process_task.filter_task.role_index)
            .order_by('-updated_at', '-id')[:3]
        )
        review = review_issue_result(result, samples)

        result.review_status = review['review_status']
        result.review_reason = review['review_reason']
        result.review_model = review['review_model']
        result.reviewed_at = timezone.now()
        result.manual_override_after_review = False
        result.save(update_fields=[
            'review_status', 'review_reason', 'review_model',
            'reviewed_at', 'manual_override_after_review', 'updated_at',
        ])

        if review['review_status'] == 'FAIL':
            IssueReviewSample.objects.create(
                role_index=process_task.filter_task.role_index,
                issue_key=result.issue_key,
                incorrect_conclusion=result.reply_text,
                correct_conclusion=review.get('correct_conclusion', ''),
                error_reason=review['review_reason'],
            )

        return Response(review)


class IssueProcessResultManualReviewView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        review_status = request.data.get('review_status')
        if review_status not in ('PASS', 'FAIL'):
            return Response({'detail': 'review_status 必须是 PASS 或 FAIL'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        if review_status == 'PASS':
            result.review_status = 'PASS'
            result.review_reason = ''
            result.reviewed_at = now
            result.review_model = ''
            result.manual_override_after_review = False
            result.manual_error_reason = ''
            result.manual_correct_result = ''
            result.manual_review_saved_at = None
            result.save(update_fields=[
                'review_status',
                'review_reason',
                'reviewed_at',
                'review_model',
                'manual_override_after_review',
                'manual_error_reason',
                'manual_correct_result',
                'manual_review_saved_at',
                'updated_at',
            ])
            IssueReviewSample.objects.filter(
                role_index=result.process_task.filter_task.role_index,
                issue_key=result.issue_key,
            ).delete()
            delete_learning_memory(result.process_task.filter_task.role_index, result.issue_key)
            publish_rule_group_snapshot()
            return Response(IssueProcessResultSerializer(result).data)

        error_reason = request.data.get('error_reason')
        correct_result = request.data.get('correct_result')
        if not isinstance(error_reason, str) or not error_reason.strip():
            return Response({'detail': '错误原因不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(correct_result, str) or not correct_result.strip():
            return Response({'detail': '正确结果不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        error_reason = error_reason.strip()
        correct_result = correct_result.strip()
        result.review_status = 'FAIL'
        result.review_reason = error_reason
        result.reviewed_at = now
        result.review_model = ''
        result.manual_override_after_review = True
        result.manual_error_reason = error_reason
        result.manual_correct_result = correct_result
        result.manual_review_saved_at = now
        result.save(update_fields=[
            'review_status',
            'review_reason',
            'reviewed_at',
            'review_model',
            'manual_override_after_review',
            'manual_error_reason',
            'manual_correct_result',
            'manual_review_saved_at',
            'updated_at',
        ])
        IssueReviewSample.objects.update_or_create(
            role_index=result.process_task.filter_task.role_index,
            issue_key=result.issue_key,
            defaults={
                'incorrect_conclusion': result.reply_text,
                'correct_conclusion': correct_result,
                'error_reason': error_reason,
            },
        )
        persist_learning_memory(result)
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)


class IssueProcessResultValidationRunCreateView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        run = IssueValidationRun.objects.create(process_result=result, status='PENDING')
        return Response(
            {'validation_run_id': run.id, 'status': run.status},
            status=status.HTTP_201_CREATED,
        )


class IssueProcessResultLatestValidationRunView(APIView):
    def get(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        run = result.validation_runs.order_by('-created_at').first()
        if run is None:
            return Response({'detail': '暂无校验记录'}, status=status.HTTP_404_NOT_FOUND)
        return Response(IssueValidationRunSerializer(run).data)


class IssueValidationRunDetailView(APIView):
    def get(self, request, pk: int):
        run = get_object_or_404(IssueValidationRun, pk=pk)
        return Response(IssueValidationRunSerializer(run).data)


class IssueValidationRunOverrideView(APIView):
    def patch(self, request, pk: int):
        run = get_object_or_404(IssueValidationRun, pk=pk)
        manual_verdict = request.data.get('manual_verdict')
        manual_reason = request.data.get('manual_reason')
        manual_note = request.data.get('manual_note')
        if manual_verdict not in ('PASS', 'FAIL', 'WARNING', 'UNKNOWN'):
            return Response({'detail': 'manual_verdict 必须是 PASS/FAIL/WARNING/UNKNOWN'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(manual_reason, str) or not manual_reason.strip():
            return Response({'detail': 'manual_reason 不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(manual_note, str) or not manual_note.strip():
            return Response({'detail': 'manual_note 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        run.manual_verdict = manual_verdict
        run.manual_reason = manual_reason.strip()
        run.manual_note = manual_note.strip()
        run.manual_operator = user.username if user.is_authenticated else 'anonymous'
        run.manual_saved_at = timezone.now()
        run.save(update_fields=[
            'manual_verdict',
            'manual_reason',
            'manual_note',
            'manual_operator',
            'manual_saved_at',
            'updated_at',
        ])
        return Response(IssueValidationRunSerializer(run).data)


class IssueProcessResultCommentView(APIView):
    def post(self, request, pk: int):
        result = get_object_or_404(IssueProcessResult, pk=pk)
        if result.has_commented_to_jira:
            return Response({'detail': '该结果已回填 Jira'}, status=status.HTTP_200_OK)
        if result.review_status == 'FAIL' and not (result.manual_override_after_review and result.manual_correct_result.strip()):
            return Response({'detail': '复核失败，请先人工修改分析结果并保存'}, status=status.HTTP_409_CONFLICT)
        if result.review_status == 'PENDING':
            return Response({'detail': '请先完成复核'}, status=status.HTTP_409_CONFLICT)

        cfg = load_config('config.yaml')
        jira_cfg = cfg['jira']
        jira = JiraClient(
            server=jira_cfg['server'],
            username=jira_cfg['username'],
            password=jira_cfg['password'],
            use_system_proxy=jira_cfg.get('use_system_proxy', True),
            proxies=jira_cfg.get('proxies'),
        )
        comment_text = result.manual_correct_result if result.review_status == 'FAIL' else result.reply_text
        if result.can_trace_image:
            jira.add_comment_with_image(result.issue_key, comment_text, result.can_trace_image)
        else:
            jira.add_comment(result.issue_key, comment_text)
        result.has_commented_to_jira = True
        result.commented_at = timezone.now()
        result.save(update_fields=['has_commented_to_jira', 'commented_at', 'updated_at'])
        publish_rule_group_snapshot()
        return Response(IssueProcessResultSerializer(result).data)
