from rest_framework import serializers
from backend.apps.clinic.models import (
    Clinic, PatientProfile, Appointment, ClinicVisit, Drug, DrugBatch, Prescription, Ward, SickBayAdmission, Vaccination
)

class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ['id', 'school', 'name', 'location']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['id', 'person', 'blood_group', 'allergies', 'chronic_conditions']


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'appointment_date', 'status']


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicVisit
        fields = ['id', 'patient', 'visit_date', 'symptoms', 'diagnosis', 'status']


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = ['id', 'name', 'stock_qty']


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugBatch
        fields = ['id', 'drug', 'batch_number', 'expiry_date']


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'visit', 'drug', 'dosage']


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ['id', 'name']


class AdmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SickBayAdmission
        fields = ['id', 'patient', 'ward', 'bed_number', 'admitted_at', 'discharged_at']


class VaccinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccination
        fields = ['id', 'patient', 'vaccine_name', 'administered_date']
