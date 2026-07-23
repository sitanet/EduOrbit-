from rest_framework import serializers
from backend.apps.administration.models import (
    PlatformSetting, SchoolSetting, SubscriptionPlan, SchoolSubscription, ModuleLicense, FeatureFlag, SchoolBranding, PlatformAudit, APIKey
)

class PlatformSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSetting
        fields = ['id', 'key', 'value']


class SchoolSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSetting
        fields = ['id', 'school', 'theme_color', 'motto']


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'monthly_price', 'student_limit']


class SchoolSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSubscription
        fields = ['id', 'school', 'plan', 'expiry_date']


class ModuleLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleLicense
        fields = ['id', 'school', 'module_name', 'is_enabled']


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ['id', 'flag_name', 'is_active']


class BrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolBranding
        fields = ['id', 'school', 'custom_domain', 'logo_path']


class PlatformAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformAudit
        fields = ['id', 'actor', 'action', 'details', 'timestamp']


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['id', 'school', 'token_key', 'is_active']
