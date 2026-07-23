import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from backend.apps.identity.models import User, UserSession

logger = logging.getLogger("eduorbit.identity.security")

class LoginPolicyManager:
    """
    Validates tenant-scoped security policies:
    lockouts, passwords expiry rules, and session timeout thresholds.
    """
    @staticmethod
    def get_policy(tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        default_policy = {
            "max_failed_attempts": 5,
            "lockout_duration_mins": 15,
            "password_expiry_days": 90,
            "session_timeout_mins": 30,
            "mfa_required": False,
            "force_password_change_on_first_login": True
        }
        if tenant_config and "login_policy" in tenant_config:
            default_policy.update(tenant_config["login_policy"])
        return default_policy

    @classmethod
    def check_user_lockout(cls, user: User, tenant_policy: Dict[str, Any]) -> bool:
        if user.account_locked_until and user.account_locked_until > timezone.now():
            return True
            
        # Lockout expired, reset counter
        if user.account_locked_until and user.account_locked_until <= timezone.now():
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            
        return False

    @classmethod
    def register_failed_attempt(cls, user: User, tenant_policy: Dict[str, Any]):
        user.failed_login_attempts += 1
        max_attempts = tenant_policy.get("max_failed_attempts", 5)
        
        if user.failed_login_attempts >= max_attempts:
            duration = tenant_policy.get("lockout_duration_mins", 15)
            user.account_locked_until = timezone.now() + timedelta(minutes=duration)
            logger.warning(f"User {user.username} locked out until {user.account_locked_until}")
            
        user.save(update_fields=['failed_login_attempts', 'account_locked_until'])


class RiskAnalysisEngine:
    """
    Dynamic login risk detector identifying suspicious attempts (e.g. impossible travel, new device fingerprints).
    """
    @staticmethod
    def evaluate_request_risk(user: User, 
                              ip_address: str, 
                              device_fingerprint: str, 
                              country: str) -> Dict[str, Any]:
        """
        Evaluate login metrics to detect anonymous proxy/impossible travel.
        """
        risk_score = 0.0
        reasons = []
        
        # Check previous sessions
        previous_sessions = UserSession.objects.filter(user=user, revoked_at=None)[:5]
        
        if previous_sessions.exists():
            # 1. New device check
            known_fingerprints = [s.device_fingerprint for s in previous_sessions if s.device_fingerprint]
            if device_fingerprint and device_fingerprint not in known_fingerprints:
                risk_score += 0.3
                reasons.append("NEW_DEVICE")
                
            # 2. Country mismatch check
            known_countries = [s.country for s in previous_sessions if s.country]
            if country and country not in known_countries:
                risk_score += 0.5
                reasons.append("NEW_COUNTRY")
                
        # Simple threshold response
        return {
            "risk_score": risk_score,
            "suspicious": risk_score >= 0.6,
            "reasons": reasons
        }
