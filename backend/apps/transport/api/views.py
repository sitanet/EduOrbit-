from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.transport.models import Route, Trip, VehicleLocation
from backend.apps.transport.api.serializers import (
    RouteSerializer, TripSerializer, LocationSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class RouteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        routes = Route.objects.filter(tenant=request.tenant)
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RouteSerializer(data=request.data)
        if serializer.is_valid():
            route = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("route.created", tenant_id=str(request.tenant.id), data={"id": str(route.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TripAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(tenant=request.tenant)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TripSerializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("trip.started", tenant_id=str(request.tenant.id), data={"id": str(trip.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VehicleLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        locations = VehicleLocation.objects.filter(tenant=request.tenant)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            loc = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("gps.location_logged", tenant_id=str(request.tenant.id), data={"id": str(loc.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
