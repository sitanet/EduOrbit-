from backend.apps.tenants.models import School, TenantSubscription


class TenantDashboardService:
    """
    Service layer for Tenant Dashboard functionality.
    Handles all data queries and business logic for the tenant dashboard view.
    Follows Clean Architecture principles by separating business logic from view layer.
    """
    
    @staticmethod
    def get_dashboard_data(request_user, tenant=None):
        """
        Get all dashboard data for the tenant dashboard view.
        
        This method encapsulates all ORM queries and business logic for the dashboard,
        ensuring the view layer remains thin and focused only on HTTP request/response handling.
        
        Args:
            request_user: User instance making the request
            tenant: Tenant instance (can be None for superusers or unauthenticated contexts)
            
        Returns:
            Dictionary containing dashboard context data with the following structure:
            {
                'tenant': Tenant instance or None,
                'schools': QuerySet of School instances,
                'subscription': TenantSubscription instance or None,
                'is_superuser': Boolean indicating if user is superuser
            }
        """
        if request_user.is_superuser:
            # Superuser sees all schools across all tenants for administrative oversight
            schools = School.objects.all().select_related('tenant')
            subscription = None
            dashboard_tenant = None
        else:
            # Regular users see only schools from their assigned tenant
            # Using tenant-scoped queries to maintain data isolation
            schools = School.objects.filter(tenant=tenant) if tenant else School.objects.none()
            subscription = TenantSubscription.objects.filter(tenant=tenant).first() if tenant else None
            dashboard_tenant = tenant
            
        return {
            'tenant': dashboard_tenant,
            'schools': schools,
            'subscription': subscription,
            'is_superuser': request_user.is_superuser
        }