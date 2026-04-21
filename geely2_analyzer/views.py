from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from platform_accounts.views import SessionStatusCodeAuthentication

from .models import JiraCredentialBinding
from .serializers import JiraCredentialBindingSerializer


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