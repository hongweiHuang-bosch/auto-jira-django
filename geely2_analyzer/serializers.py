from rest_framework import serializers

from .models import JiraCredentialBinding


class JiraCredentialBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraCredentialBinding
        fields = ['jira_base_url', 'jira_username', 'is_active']
        read_only_fields = fields
