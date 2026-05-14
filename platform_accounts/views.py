from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class SessionStatusCodeAuthentication(SessionAuthentication):
    def authenticate_header(self, request):
        return 'Session'


class CsrfBootstrapView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        SessionAuthentication().enforce_csrf(request)

        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': '用户名或密码错误'}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        return Response({'authenticated': True, 'username': user.username})


class SessionView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'authenticated': True, 'username': request.user.username})


class LogoutView(APIView):
    authentication_classes = [SessionStatusCodeAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'authenticated': False})
