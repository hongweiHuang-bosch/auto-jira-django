
from rest_framework import serializers
from .models import AnalysisTask, IssueAnalysisResult


class IssueAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueAnalysisResult
        fields = '__all__'


class AnalysisTaskSerializer(serializers.ModelSerializer):
    results = IssueAnalysisResultSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisTask
        fields = '__all__'
