from rest_framework import serializers

from .models import (
    Geely2AnalysisResult,
    Geely2AnalysisTask,
    Geely2IssueSnapshot,
    Geely2SyncTask,
    JiraCredentialBinding,
)


class JiraCredentialBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraCredentialBinding
        fields = "__all__"


class Geely2SyncTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geely2SyncTask
        fields = "__all__"


class Geely2IssueSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geely2IssueSnapshot
        fields = "__all__"


class Geely2AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geely2AnalysisResult
        fields = "__all__"


class Geely2AnalysisTaskSerializer(serializers.ModelSerializer):
    result = Geely2AnalysisResultSerializer(read_only=True)

    class Meta:
        model = Geely2AnalysisTask
        fields = "__all__"
