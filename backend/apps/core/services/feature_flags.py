from django.conf import settings

class FeatureFlagEngine:
    """
    Enterprise Shared Feature Flag Engine.
    Controls module enablement (HR, SIS, Finance, Library, Hostel, Parent Portal).
    """
    DEFAULT_FLAGS = {
        'enable_hr': True,
        'enable_payroll': True,
        'enable_sis': True,
        'enable_finance': True,
        'enable_library': True,
        'enable_hostel': True,
        'enable_parent_portal': True,
        'enable_kyc_dojah': True,
        'enable_workflow_designer': True,
    }

    @classmethod
    def is_feature_enabled(cls, tenant, feature_key):
        if not tenant:
            return cls.DEFAULT_FLAGS.get(feature_key, False)
        # Check tenant-specific settings or default
        return cls.DEFAULT_FLAGS.get(feature_key, True)
