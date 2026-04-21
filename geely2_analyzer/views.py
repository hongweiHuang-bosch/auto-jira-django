from django.db import transaction
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from platform_accounts.views import SessionStatusCodeAuthentication

from .models import Geely2SyncTask, JiraCredentialBinding
from .serializers import JiraCredentialBindingSerializer
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