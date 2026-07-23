from rest_framework import serializers
from backend.apps.transport.models import (
    VehicleCategory, Vehicle, Driver, Route, RouteStop, Trip, TripPassenger, TransportSubscription, VehicleLocation, FuelLog, MaintenanceSchedule
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleCategory
        fields = ['id', 'name']


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'category', 'registration_number', 'plate_number', 'capacity', 'status']


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', 'person', 'license_number', 'status']


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'name', 'start_point', 'end_point', 'total_distance_km']


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = ['id', 'route', 'stop_name', 'stop_order', 'gps_latitude', 'gps_longitude']


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'route', 'vehicle', 'driver', 'trip_type', 'status']


class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPassenger
        fields = ['id', 'trip', 'student', 'boarded_time', 'status']


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportSubscription
        fields = ['id', 'student', 'route', 'stop', 'billing_type']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleLocation
        fields = ['id', 'vehicle', 'latitude', 'longitude', 'speed', 'timestamp']
