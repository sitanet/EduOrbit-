from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from django.shortcuts import get_object_or_404
from backend.apps.people.models import Person, PersonRole, FamilyRelationship
from backend.apps.people.api.serializers import (
    PersonSerializer, PersonRoleSerializer, RelationshipSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class PeopleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        people = Person.objects.filter(tenant=request.tenant)
        serializer = PersonSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("person.created", tenant_id=str(request.tenant.id), data={"person": person.person_number}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PeopleSearchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([], status=status.HTTP_200_OK)
            
        people = Person.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(person_number__icontains=query),
            tenant=request.tenant
        )
        serializer = PersonSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PersonRoleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PersonRoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("role.assigned", tenant_id=str(request.tenant.id), data={"role": role.role}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RelationshipAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RelationshipSerializer(data=request.data)
        if serializer.is_valid():
            rel = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("familyrelationship.created", tenant_id=str(request.tenant.id), data={"relationship": rel.relationship_type}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
