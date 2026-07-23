from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.clinic.models import PatientProfile, Appointment, ClinicVisit
from backend.apps.clinic.api.serializers import (
    PatientSerializer, AppointmentSerializer, VisitSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class PatientProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        patients = PatientProfile.objects.filter(tenant=request.tenant)
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            pat = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("patient.registered", tenant_id=str(request.tenant.id), data={"id": str(pat.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        appointments = Appointment.objects.filter(tenant=request.tenant)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            appt = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("appointment.booked", tenant_id=str(request.tenant.id), data={"id": str(appt.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClinicVisitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        visits = ClinicVisit.objects.filter(tenant=request.tenant)
        serializer = VisitSerializer(visits, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = VisitSerializer(data=request.data)
        if serializer.is_valid():
            visit = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("clinic.visit_completed", tenant_id=str(request.tenant.id), data={"id": str(visit.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
