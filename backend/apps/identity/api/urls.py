from django.urls import path
from backend.apps.identity.api.views import LoginAPIView, LogoutAPIView, RefreshAPIView, SessionListAPIView

app_name = 'identity_api'

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='login'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),
    path('auth/refresh/', RefreshAPIView.as_view(), name='refresh'),
    path('auth/sessions/', SessionListAPIView.as_view(), name='sessions_list'),
    path('auth/sessions/<uuid:pk>/', SessionListAPIView.as_view(), name='session_revoke'),
]
