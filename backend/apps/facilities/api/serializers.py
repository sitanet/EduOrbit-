from rest_framework import serializers
from backend.apps.facilities.models import (
    Building, Floor, Room, Facility, WorkRequest, WorkOrder, WorkLog, FacilityMaintenancePlan, FacilityMaintenanceSchedule, Inspection, UtilityMeter, UtilityReading
)

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'school', 'name', 'code', 'gps_latitude', 'gps_longitude']


class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ['id', 'building', 'name']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'floor', 'room_number', 'room_type']


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'room', 'name', 'category']


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkRequest
        fields = ['id', 'requester', 'room', 'description', 'priority']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = ['id', 'request', 'assigned_to', 'status', 'actual_cost']


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLog
        fields = ['id', 'order', 'action', 'timestamp']


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityMaintenancePlan
        fields = ['id', 'name', 'recurrence']


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityMaintenanceSchedule
        fields = ['id', 'plan', 'next_due_date']


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = ['id', 'building', 'inspector', 'score', 'inspection_date']


class MeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityMeter
        fields = ['id', 'building', 'meter_type']


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityReading
        fields = ['id', 'meter', 'reading_value', 'reading_date']
