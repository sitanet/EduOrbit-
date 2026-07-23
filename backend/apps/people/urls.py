from django.urls import path, include
from backend.apps.people.views_web import PersonDirectoryWebView, FamilyRelationshipWebView

urlpatterns = [
    # Web views
    path('directory/', PersonDirectoryWebView.as_view(), name='people_directory_web'),
    path('relationships/', FamilyRelationshipWebView.as_view(), name='family_relationship_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.people.api.urls')),
]
