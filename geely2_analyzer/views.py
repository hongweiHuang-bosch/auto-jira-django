import os

from django.db import transaction
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from platform_accounts.views import SessionStatusCodeAuthentication

from .models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)
from .serializers import JiraCredentialBindingSerializer
from .services.client_factory import build_jira_client
from .services.payloads import build_issue_list_payload
from .services.stream import publish_geely2_snapshot, stream_geely2_events


class CredentialView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        binding = JiraCredentialBinding.objects.filter(user=request.user, project_code='geely2').first()
        if binding is None:
            return Response({'configured': False})

        return Response({'configured': True, **JiraCredentialBindingSerializer(binding).data})

    def put(self, request):
        binding = JiraCredentialBinding.objects.filter(user=request.user, project_code='geely2').first()
        serializer = JiraCredentialBindingSerializer(
            instance=binding,
            data=request.data,
            partial=bool(binding),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, project_code='geely2', is_active=True)
        return Response({'configured': True, **serializer.data})


class SyncTaskCreateView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            binding = JiraCredentialBinding.objects.select_for_update().filter(
                user=request.user,
                project_code='geely2',
            ).first()
            if binding is None:
                return Response({'detail': '请先配置 Jira 凭据'}, status=status.HTTP_400_BAD_REQUEST)

            running = Geely2SyncTask.objects.filter(
                user=request.user,
                status__in=['PENDING', 'RUNNING'],
            ).order_by('-created_at').first()
            if running is not None:
                return Response(
                    {'detail': '已有进行中的同步任务', 'task_id': running.id},
                    status=status.HTTP_409_CONFLICT,
                )

            task = Geely2SyncTask.objects.create(
                user=request.user,
                credential_binding=binding,
                status='PENDING',
                message='同步任务已创建',
            )

        publish_geely2_snapshot(request.user)
        return Response({'id': task.id, 'status': task.status}, status=status.HTTP_201_CREATED)


class SyncTaskDetailView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        task = get_object_or_404(Geely2SyncTask, pk=pk, user=request.user)
        return Response(
            {
                'id': task.id,
                'status': task.status,
                'issue_count': task.issue_count,
                'message': task.message,
                'error_code': task.error_code,
                'error_message': task.error_message,
            }
        )


class IssueListView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(build_issue_list_payload(request.user))


class Geely2StreamView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = StreamingHttpResponse(
            streaming_content=stream_geely2_events(request.user),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class AnalysisTaskCreateView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, issue_key):
        snapshot = get_object_or_404(Geely2IssueSnapshot, user=request.user, issue_key=issue_key)
        binding = get_object_or_404(JiraCredentialBinding, user=request.user, project_code='geely2')
        running = Geely2AnalysisTask.objects.filter(
            user=request.user,
            issue_key=issue_key,
            status__in=['PENDING', 'RUNNING'],
        ).first()
        if running is not None:
            return Response(
                {'detail': '当前票已有进行中的分析任务', 'task_id': running.id},
                status=status.HTTP_409_CONFLICT,
            )
        task = Geely2AnalysisTask.objects.create(
            user=request.user,
            credential_binding=binding,
            issue_snapshot=snapshot,
            issue_key=issue_key,
            status='PENDING',
            stage='FETCH_COMMENTS',
            message='分析任务已创建',
        )
        snapshot.current_analysis_status = 'PENDING'
        snapshot.save(update_fields=['current_analysis_status', 'updated_at'])
        publish_geely2_snapshot(request.user)
        return Response({'id': task.id, 'status': task.status}, status=status.HTTP_201_CREATED)


class AnalysisTaskDetailView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        task = get_object_or_404(Geely2AnalysisTask, pk=pk, user=request.user)
        return Response({
            'id': task.id,
            'status': task.status,
            'stage': task.stage,
            'progress': task.progress,
            'message': task.message,
            'error_code': task.error_code,
            'error_message': task.error_message,
        })


class AnalysisResultView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        result = get_object_or_404(Geely2AnalysisResult, pk=pk, user=request.user)
        return Response({
            'id': result.id,
            'issue_key': result.issue_key,
            'ai_summary': result.ai_summary,
            'reply_text': result.reply_text,
            'evidence_payload': result.evidence_payload,
            'confidence': result.confidence,
            'risk_notes': result.risk_notes,
            'comment_status': result.comment_status,
            'last_error': result.last_error,
        })

    def patch(self, request, pk):
        result = get_object_or_404(Geely2AnalysisResult, pk=pk, user=request.user)
        result.reply_text = request.data.get('reply_text', result.reply_text)
        result.save(update_fields=['reply_text', 'updated_at'])
        return Response({'id': result.id, 'reply_text': result.reply_text})


class AnalysisResultCommentView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        result = get_object_or_404(Geely2AnalysisResult, pk=pk, user=request.user)
        if result.comment_status == 'COMMENTED':
            return Response({'detail': '该结果已回填 Jira'})
        try:
            jira_client = build_jira_client(result.analysis_task.credential_binding)
            image_path = (result.evidence_payload or {}).get('can_trace_image_path', '')
            if image_path and os.path.isfile(image_path):
                jira_client.add_comment_with_image(result.issue_key, result.reply_text, image_path)
            else:
                jira_client.add_comment(result.issue_key, result.reply_text)
            result.comment_status = 'COMMENTED'
            result.commented_at = timezone.now()
            result.last_error = ''
            result.save(update_fields=['comment_status', 'commented_at', 'last_error', 'updated_at'])
            return Response({'detail': '已成功回填 Jira'})
        except Exception as exc:
            result.comment_status = 'COMMENT_FAILED'
            result.last_error = str(exc)
            result.save(update_fields=['comment_status', 'last_error', 'updated_at'])
            return Response(
                {'detail': '回填失败', 'error': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )