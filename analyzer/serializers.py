
from rest_framework import serializers
from .models import (
    AnalysisTask,
    FilterTask,
    FilteredIssueSnapshot,
    IssueAnalysisResult,
    IssueProcessResult,
    IssueProcessTask,
    IssueValidationCheck,
    IssueValidationRun,
)


class IssueAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueAnalysisResult
        fields = '__all__'


class AnalysisTaskSerializer(serializers.ModelSerializer):
    results = IssueAnalysisResultSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisTask
        fields = '__all__'


class IssueProcessResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueProcessResult
        fields = '__all__'


class IssueProcessTaskSerializer(serializers.ModelSerializer):
    result = IssueProcessResultSerializer(read_only=True)

    class Meta:
        model = IssueProcessTask
        fields = '__all__'


class IssueValidationCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueValidationCheck
        fields = '__all__'


class IssueValidationRunSerializer(serializers.ModelSerializer):
    checks = IssueValidationCheckSerializer(many=True, read_only=True)

    class Meta:
        model = IssueValidationRun
        fields = '__all__'


class FilteredIssueSnapshotSerializer(serializers.ModelSerializer):
    latest_process_task = serializers.SerializerMethodField()
    latest_result = serializers.SerializerMethodField()

    class Meta:
        model = FilteredIssueSnapshot
        fields = '__all__'

    def get_latest_process_task(self, obj):
        task = obj.process_tasks.order_by('-created_at').first()
        return IssueProcessTaskSerializer(task).data if task else None

    def get_latest_result(self, obj):
        task = obj.process_tasks.order_by('-created_at').first()
        result = getattr(task, 'result', None) if task else None
        return IssueProcessResultSerializer(result).data if result else None


class FilterTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterTask
        fields = '__all__'
