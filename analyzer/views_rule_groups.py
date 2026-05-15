from __future__ import annotations

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import FilterTask
from .services.jira_issue_payload import build_jira_issue_payload, transition_jira_issue
from .services.rule_group_payload import (
    build_processed_issue_detail,
    build_processed_issue_page,
    build_rule_group_detail,
    build_rule_group_payload,
    get_filter_task_issue_page,
    get_latest_filter_task_detail,
)
from .services.rule_group_stream import stream_rule_group_events


class RuleGroupListView(APIView):
    def get(self, request):
        return Response(build_rule_group_payload())


class RuleGroupDetailView(APIView):
    def get(self, request, role_index: int):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        return Response(build_rule_group_detail(role_index=role_index, page=page, page_size=page_size))


class RuleGroupProcessedIssueListView(APIView):
    def get(self, request, role_index: int):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        query = request.query_params.get('q', '')
        status = request.query_params.get('status', '')
        return Response(build_processed_issue_page(
            role_index=role_index,
            page=page,
            page_size=page_size,
            query=query,
            status=status,
        ))


class RuleGroupProcessedIssueDetailView(APIView):
    def get(self, request, role_index: int, issue_key: str):
        payload = build_processed_issue_detail(role_index=role_index, issue_key=issue_key)
        if payload is None:
            return Response({'detail': '未找到该票的历史处理记录'}, status=404)
        return Response(payload)


class RuleGroupProcessedIssueJiraView(APIView):
    def get(self, request, role_index: int, issue_key: str):
        if build_processed_issue_detail(role_index=role_index, issue_key=issue_key) is None:
            return Response({'detail': '未找到该票的历史处理记录'}, status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(build_jira_issue_payload(issue_key))
        except Exception:
            return Response({'detail': 'Jira 信息加载失败'}, status=status.HTTP_502_BAD_GATEWAY)


class RuleGroupProcessedIssueTransitionView(APIView):
    def post(self, request, role_index: int, issue_key: str):
        transition_id = request.data.get('transition_id')
        target_user = request.data.get('target_user')
        if not transition_id or not target_user:
            return Response({'detail': '缺少 transition_id 或 target_user'}, status=status.HTTP_400_BAD_REQUEST)
        if build_processed_issue_detail(role_index=role_index, issue_key=issue_key) is None:
            return Response({'detail': '未找到该票的历史处理记录'}, status=status.HTTP_404_NOT_FOUND)
        try:
            transition_jira_issue(issue_key, str(transition_id), str(target_user))
        except Exception:
            return Response({'detail': 'Jira 流转失败'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'detail': '流转成功'})


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


class RuleGroupStreamView(View):
    def get(self, request):
        response = StreamingHttpResponse(
            streaming_content=stream_rule_group_events(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
