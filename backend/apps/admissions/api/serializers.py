from rest_framework import serializers
from backend.apps.admissions.models import (
    AdmissionCampaign, AdmissionIntake, Applicant,
    AdmissionApplication, ApplicationDocument, AdmissionOffer
)

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionCampaign
        fields = ['id', 'school', 'academic_year', 'name', 'start_date', 'end_date', 'is_active']


class IntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionIntake
        fields = ['id', 'campaign', 'name', 'status']


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = ['id', 'school', 'person', 'applicant_number']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionApplication
        fields = ['id', 'intake', 'applicant', 'target_level', 'status', 'current_stage', 'submission', 'application_date']


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ['id', 'application', 'document_type', 'document_file', 'verification_status', 'notes']


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionOffer
        fields = ['id', 'application', 'status', 'acceptance_deadline', 'notes']
