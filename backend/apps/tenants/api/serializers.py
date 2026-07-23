from rest_framework import serializers
from backend.apps.tenants.models import Tenant, School, Campus, CustomDomain

class TenantOnboardSerializer(serializers.Serializer):
    org_name = serializers.CharField(max_length=255)
    admin_email = serializers.EmailField()
    admin_username = serializers.CharField(max_length=150)
    admin_password = serializers.CharField(write_only=True)
    billing_model = serializers.ChoiceField(choices=Tenant.BILLING_MODELS, default='school_pays')
    school_name = serializers.CharField(max_length=255, required=False)
    school_types = serializers.ListField(child=serializers.CharField(), required=False)


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'school_types', 'curriculum_codes', 'is_active']


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['id', 'name', 'address', 'contact_phone', 'contact_email', 'principal_user_id']


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDomain
        fields = ['id', 'domain_name', 'is_verified', 'verification_token', 'ssl_active']
