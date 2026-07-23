from rest_framework import serializers
from backend.apps.identity.models import UserSession

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    device_name = serializers.CharField(required=False, default='Unknown Mobile')
    device_fingerprint = serializers.CharField(required=False, default='')


class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.UUIDField(required=True)


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = [
            'id', 'login_method', 'device_name', 'browser', 'operating_system',
            'ip_address', 'country', 'city', 'login_time', 'last_activity', 
            'mfa_completed', 'trusted_device'
        ]
