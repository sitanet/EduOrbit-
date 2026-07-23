import jwt
import uuid
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.utils import timezone
from backend.apps.identity.api.serializers import LoginSerializer, TokenRefreshSerializer, SessionSerializer
from backend.apps.identity.models import UserSession
from backend.apps.identity.services import IdentityService

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve client IP and Agent information
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        user = IdentityService.authenticate_user(
            credentials=serializer.validated_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not user:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Create session
        session = IdentityService.create_user_session(
            user=user,
            device_name=serializer.validated_data.get('device_name', ''),
            device_fingerprint=serializer.validated_data.get('device_fingerprint', ''),
            ip_address=ip_address,
            browser=user_agent.split(' ')[0] if user_agent else 'Unknown'
        )

        return Response({
            "access_token": str(session.access_token_id),
            "refresh_token": str(session.refresh_token_id),
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Resolve active session via header access token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token_id = auth_header.split(' ')[1]
            try:
                session = UserSession.objects.get(access_token_id=token_id)
                session.revoked_at = timezone.now()
                session.save(update_fields=['revoked_at'])
            except (UserSession.DoesNotExist, ValueError):
                pass
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class RefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data['refresh_token']
        try:
            session = UserSession.objects.get(refresh_token_id=refresh_token, revoked_at=None)
            if not session.is_valid():
                raise ValueError("Session is expired or revoked.")
        except (UserSession.DoesNotExist, ValueError) as e:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Rotate tokens
        session.access_token_id = uuid.uuid4()
        session.refresh_token_id = uuid.uuid4()
        session.last_activity = timezone.now()
        session.save(update_fields=['access_token_id', 'refresh_token_id', 'last_activity'])

        return Response({
            "access_token": str(session.access_token_id),
            "refresh_token": str(session.refresh_token_id)
        }, status=status.HTTP_200_OK)


class SessionListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user, revoked_at=None)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Revoke a specific session."""
        try:
            session = UserSession.objects.get(id=pk, user=request.user)
            session.revoked_at = timezone.now()
            session.save(update_fields=['revoked_at'])
            return Response(status=status.HTTP_24_NO_CONTENT)
        except UserSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
