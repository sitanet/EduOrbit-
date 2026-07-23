from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from backend.apps.attendance.models import AttendanceRecord, AttendanceCorrection, OfflineSyncQueue
from backend.apps.attendance.api.serializers import (
    RecordSerializer, CorrectionSerializer, SyncQueueSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class AttendanceRecordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = AttendanceRecord.objects.filter(tenant=request.tenant)
        serializer = RecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RecordSerializer(data=request.data)
        if serializer.is_valid():
            record = serializer.save(tenant=request.tenant)
            
            # Fire event alerts for absenteeism
            if record.status.code == 'absent':
                event_bus.publish(DomainEvent("student.absent", tenant_id=str(request.tenant.id), data={"person": str(record.person.id)}))
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceCorrectionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CorrectionSerializer(data=request.data)
        if serializer.is_valid():
            correction = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("attendance.corrected", tenant_id=str(request.tenant.id), data={"id": str(correction.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfflineSyncAPIView(APIView):
    """
    Offline first synchronization endpoints reconciling client status updates.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        records = request.data.get('records', [])
        saved_logs = []
        
        for payload in records:
            client_uuid = payload.get('client_uuid')
            
            # Check duplicate sync logs
            if OfflineSyncQueue.objects.filter(client_uuid=client_uuid, tenant=request.tenant).exists():
                continue
                
            sync_log = OfflineSyncQueue.objects.create(
                client_uuid=client_uuid,
                tenant=request.tenant,
                payload=payload,
                local_timestamp=payload.get('timestamp'),
                sync_status='success'
            )
            saved_logs.append(str(sync_log.client_uuid))
            
        return Response({
            "detail": "Synchronization logs successfully committed.",
            "synced_uuids": saved_logs
        }, status=status.HTTP_201_CREATED)
