from __future__ import annotations

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FilterTask
from .services.rule_group_payload import (
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
