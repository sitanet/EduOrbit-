from rest_framework import serializers
from backend.apps.hostel.models import (
    Hostel, HostelBlock, HostelRoom, HostelBed, BedAllocation, HostelRollCall, HostelVisitor, HostelIncident, RoomInspection
)

class HostelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hostel
        fields = ['id', 'school', 'name', 'gender']


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelBlock
        fields = ['id', 'hostel', 'name']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRoom
        fields = ['id', 'block', 'room_number', 'floor', 'capacity']


class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelBed
        fields = ['id', 'room', 'bed_number', 'status']


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedAllocation
        fields = ['id', 'bed', 'student', 'start_date', 'end_date', 'status']


class RollCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelRollCall
        fields = ['id', 'student', 'date', 'status']


class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelVisitor
        fields = ['id', 'visitor_name', 'purpose', 'checked_in_at', 'checked_out_at']


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HostelIncident
        fields = ['id', 'student', 'title', 'description', 'incident_date']
