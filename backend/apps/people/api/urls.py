from django.urls import path
from backend.apps.people.api.views import (
    PeopleAPIView, PeopleSearchAPIView, PersonRoleAPIView, RelationshipAPIView
)

app_name = 'people_api'

urlpatterns = [
    path('people/', PeopleAPIView.as_view(), name='people_list'),
    path('people/search/', PeopleSearchAPIView.as_view(), name='people_search'),
    path('people/roles/', PersonRoleAPIView.as_view(), name='role_assign'),
    path('people/relationships/', RelationshipAPIView.as_view(), name='relationship_create'),
]
