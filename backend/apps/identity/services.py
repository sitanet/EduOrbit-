import logging
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.utils import timezone
from backend.apps.identity.models import User, UserSession, PasswordHistory, TenantMembership, Role, Permission
from backend.apps.identity.providers import auth_provider_registry
from backend.apps.identity.security import LoginPolicyManager, RiskAnalysisEngine
from backend.apps.core.events import event_bus, DomainEvent
from backend.apps.core.logging import EduOrbitLogger

logger = logging.getLogger("eduorbit.identity.services")

class IdentityService:
    """
    Enterprise Authentication Service orchestrating logins, session tokens, lockouts,
    MFA verifications, and password historical checks.
    """
    @staticmethod
    def authenticate_user(credentials: Dict[str, Any], 
                          method: str = "password", 
                          ip_address: str = None, 
                          user_agent: str = None) -> Optional[User]:
        """
        Verify credentials, check policies, audit results and emit events.
        """
        try:
            # 1. Resolve user profile
            login_id = credentials.get("username") or credentials.get("email")
            user = User.objects.get(Q(username=login_id) | Q(email=login_id))
        except User.DoesNotExist:
            event_bus.publish(DomainEvent("login.failed", tenant_id="global", data={"identifier": login_id}))
            EduOrbitLogger.security(f"Failed login attempt for non-existent user: {login_id}", ip_address=ip_address)
            return None

        # 2. Check lockout
        policy = LoginPolicyManager.get_policy(None)  # Global policy fallback
        if LoginPolicyManager.check_user_lockout(user, policy):
            event_bus.publish(DomainEvent("user.locked", tenant_id="global", actor_id=str(user.id)))
            EduOrbitLogger.security(f"Blocked login attempt for locked account: {user.username}", user_id=user.id, ip_address=ip_address)
            return None

        # 3. Authenticate via dynamic provider
        provider = auth_provider_registry.get_provider(method)
        authenticated_user = provider.authenticate_user(credentials)

        if not authenticated_user:
            LoginPolicyManager.register_failed_attempt(user, policy)
            event_bus.publish(DomainEvent("login.failed", tenant_id="global", actor_id=str(user.id)))
            return None

        # 4. Successful login: reset failed counter
        user.failed_login_attempts = 0
        user.last_login = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'last_login'])

        event_bus.publish(DomainEvent("login.succeeded", tenant_id="global", actor_id=str(user.id)))
        EduOrbitLogger.audit(f"User {user.username} logged in successfully.", user_id=user.id, ip_address=ip_address)
        return user

    @staticmethod
    def create_user_session(user: User, 
                            login_method: str = 'password', 
                            device_name: str = '', 
                            device_fingerprint: str = '', 
                            browser: str = '', 
                            operating_system: str = '', 
                            ip_address: str = None, 
                            country: str = '', 
                            city: str = '') -> UserSession:
        """
        Create dynamic active device session and register JWT token scopes.
        """
        access_token_id = uuid.uuid4()
        refresh_token_id = uuid.uuid4()
        
        # Session duration thresholds
        expires_at = timezone.now() + timedelta(days=7)
        
        session = UserSession.objects.create(
            user=user,
            access_token_id=access_token_id,
            refresh_token_id=refresh_token_id,
            login_method=login_method,
            device_name=device_name,
            device_fingerprint=device_fingerprint,
            browser=browser,
            operating_system=operating_system,
            ip_address=ip_address,
            country=country,
            city=city,
            refresh_token_expires_at=expires_at
        )
        return session

    @staticmethod
    def record_password_change(user: User, new_password_plain: str) -> bool:
        """
        Validate new password against encoded password history hashes (avoiding MD5!).
        """
        # Retrieve past hashes
        history = PasswordHistory.objects.filter(user=user)[:5]
        for past in history:
            if check_password(new_password_plain, past.password_hash):
                raise ValueError("Password matches one of your last 5 passwords. Please select another.")

        # Update user password
        user.set_password(new_password_plain)
        user.password_changed_at = timezone.now()
        user.save(update_fields=['password', 'password_changed_at'])

        # Append to history
        PasswordHistory.objects.create(user=user, password_hash=user.password)
        event_bus.publish(DomainEvent("password.changed", tenant_id="global", actor_id=str(user.id)))
        return True


class AuthorizationService:
    """
    Validates dynamic permission queries and Multi-Tenant RBAC matrices.
    """
    @staticmethod
    def check_user_permission(user: User, permission_code: str, tenant_id: str) -> bool:
        """
        Verify if a user has a specific permission in a tenant context.
        """
        # Superusers bypass checks
        if user.is_superuser:
            return True
            
        # Get active memberships for this tenant
        memberships = TenantMembership.objects.filter(user=user, tenant_id=tenant_id, status='active')
        if not memberships.exists():
            return False

        for membership in memberships:
            role = membership.role
            # Check direct role permissions
            if role.permissions.filter(code=permission_code).exists():
                return True
            # Check direct permission groups permissions
            for group in role.permission_groups.all():
                if group.permissions.filter(code=permission_code).exists():
                    return True
        return False
        
    @staticmethod
    def assign_user_role(user: User, role: Role, tenant_id: str) -> TenantMembership:
        membership = TenantMembership.objects.create(
            user=user,
            tenant_id=tenant_id,
            role=role,
            status='active'
        )
        event_bus.publish(DomainEvent("role.assigned", tenant_id=str(tenant_id), actor_id=str(user.id), data={"role_code": role.code}))
        return membership
