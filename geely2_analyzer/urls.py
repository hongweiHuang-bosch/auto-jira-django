from django.urls import path

from .views import CredentialView


urlpatterns = [
    path('credential/', CredentialView.as_view(), name='geely2-credential'),
]