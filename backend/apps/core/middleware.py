import contextvars
from django.http import Http404
from django.conf import settings

# Async-safe context variables mapping
current_tenant_var = contextvars.ContextVar('current_tenant', default=None)

def get_current_tenant():
    return current_tenant_var.get()

def set_current_tenant(tenant):
    current_tenant_var.set(tenant)

class TenantMiddleware:
    """
    Async-safe middleware resolving active Tenant via subdomain or X-Tenant-ID header.
    Utilizes ContextVar for thread and context-safe access across WSGI and ASGI (Channels) pipelines.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.apps import apps
        Tenant = apps.get_model('tenants', 'Tenant')
        CustomDomain = apps.get_model('tenants', 'CustomDomain')
        
        tenant = None
        
        # 1. Resolve header (Mobile, REST clients)
        tenant_id = request.headers.get('X-Tenant-ID') or request.META.get('HTTP_X_TENANT_ID')
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass
                
        # 2. Resolve subdomain or custom domain (Web browser clients)
        if not tenant:
            host = request.get_host().split(':')[0]  # Remove port if present
            try:
                # Direct custom domain match
                custom_domain = CustomDomain.objects.select_related('tenant').get(domain_name=host)
                tenant = custom_domain.tenant
            except CustomDomain.DoesNotExist:
                # Fallback to subdomain matching
                host_parts = host.split('.')
                subdomain = None
                if len(host_parts) > 2:
                    subdomain = host_parts[0]
                elif len(host_parts) == 2 and host_parts[1] in ['localhost', 'test']:
                    subdomain = host_parts[0]
                
                if subdomain and subdomain not in ['www', 'api', 'admin', 'localhost']:
                    try:
                        tenant = Tenant.objects.filter(is_active=True, branding_config__subdomain=subdomain).first()
                        if not tenant:
                            # Try CustomDomain matching
                            custom_domain = CustomDomain.objects.select_related('tenant').filter(
                                domain_name__icontains=subdomain
                            ).first()
                            if custom_domain:
                                tenant = custom_domain.tenant
                    except Exception:
                        pass
                        
        if not tenant:
            # Resolve from session switcher
            session_tenant_id = request.session.get('active_tenant_id') if hasattr(request, 'session') else None
            if session_tenant_id:
                try:
                    tenant = Tenant.objects.get(id=session_tenant_id, is_active=True)
                except Exception:
                    pass

        if not tenant:
            # Local development fallback: resolve first active tenant
            tenant = Tenant.objects.filter(is_active=True).first()
            
        request.tenant = tenant
        set_current_tenant(tenant)
        
        response = self.get_response(request)
        
        # Clear context
        set_current_tenant(None)
        return response
