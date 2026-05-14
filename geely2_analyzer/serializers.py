from rest_framework import serializers

from .models import JiraCredentialBinding


class JiraCredentialBindingSerializer(serializers.ModelSerializer):
    jira_password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = JiraCredentialBinding
        fields = ['jira_base_url', 'jira_username', 'jira_password', 'is_active']

    def validate(self, attrs):
        if self.instance is None and not attrs.get('jira_password'):
            raise serializers.ValidationError({'jira_password': 'This field is required.'})
        return attrs

    def save(self, **kwargs):
        validated_data = {**self.validated_data, **kwargs}
        user = validated_data.pop('user')
        project_code = validated_data.pop('project_code')
        password = validated_data.pop('jira_password', None)
        defaults = {key: value for key, value in validated_data.items() if key in self.fields}
        if password:
            defaults['encrypted_password'] = password

        instance, _ = JiraCredentialBinding.objects.update_or_create(
            user=user,
            project_code=project_code,
            defaults=defaults,
        )
        self.instance = instance
        return instance
