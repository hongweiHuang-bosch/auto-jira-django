from django.urls import path

from .views import CsrfBootstrapView, LoginView, LogoutView, SessionView


urlpatterns = [
    path('csrf/', CsrfBootstrapView.as_view(), name='platform-csrf'),
    path('login/', LoginView.as_view(), name='platform-login'),
    path('logout/', LogoutView.as_view(), name='platform-logout'),
    path('session/', SessionView.as_view(), name='platform-session'),
]
