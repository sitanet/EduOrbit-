from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from backend.apps.workflow.models import WorkflowInstance, WorkflowTask, WorkflowApproval
from backend.apps.workflow.api.serializers import (
    InstanceSerializer, TaskSerializer, ApprovalSerializer
)
from backend.apps.core.events import event_bus, DomainEvent

class WorkflowInstanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        instances = WorkflowInstance.objects.filter(tenant=request.tenant)
        serializer = InstanceSerializer(instances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = InstanceSerializer(data=request.data)
        if serializer.is_valid():
            inst = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("workflow.instance_started", tenant_id=str(request.tenant.id), data={"id": str(inst.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkflowTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = WorkflowTask.objects.filter(tenant=request.tenant)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            tk = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("workflow.task_created", tenant_id=str(request.tenant.id), data={"id": str(tk.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkflowApprovalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        approvals = WorkflowApproval.objects.filter(tenant=request.tenant)
        serializer = ApprovalSerializer(approvals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ApprovalSerializer(data=request.data)
        if serializer.is_valid():
            app = serializer.save(tenant=request.tenant)
            event_bus.publish(DomainEvent("workflow.approved", tenant_id=str(request.tenant.id), data={"id": str(app.id)}))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
