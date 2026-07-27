from django.urls import path, include

urlpatterns = [
    # API endpoints versions
    path('api/v1/', include('backend.apps.integration.api.urls')),
]
