from django.shortcuts import render
from django.views import View
from django.db.models import Sum
from django.contrib.auth.mixins import UserPassesTestMixin
from backend.apps.tenants.models import Tenant, School, TenantSubscription, SubscriptionPlan

class PlatformSaaSAnalyticsView(UserPassesTestMixin, View):
    """
    Platform Administration Dashboard displaying core SaaS business metrics
    such as active schools, MRR/ARR, module registration frequencies, and storage allocations.
    """
    def test_func(self):
        # Enforce check that user is a platform superuser or auditor
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def get(self, request):
        total_tenants = Tenant.objects.count()
        active_tenants = Tenant.objects.filter(is_active=True).count()
        total_schools = School.objects.count()
        
        # Calculate Mock MRR (Monthly Recurring Revenue) & ARR from active subscriptions
        active_subs = TenantSubscription.objects.filter(status='active').select_related('plan')
        mrr = 0.00
        for sub in active_subs:
            if sub.plan:
                price = float(sub.plan.price)
                interval = sub.plan.interval
                if interval == 'monthly':
                    mrr += price
                elif interval == 'annual':
                    mrr += price / 12.0
                elif interval == 'quarterly':
                    mrr += price / 3.0
                elif interval == 'termly':
                    mrr += price / 4.0 # 4 terms/cycles equivalent
                    
        arr = mrr * 12.0
        
        # Module adoption metrics calculations
        all_subs = TenantSubscription.objects.all()
        module_counts = {}
        for sub in all_subs:
            if isinstance(sub.modules_licensed, dict):
                for mod, config in sub.modules_licensed.items():
                    if config.get("enabled", False):
                        module_counts[mod] = module_counts.get(mod, 0) + 1
                        
        context = {
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'total_schools': total_schools,
            'mrr': round(mrr, 2),
            'arr': round(arr, 2),
            'module_adoption': module_counts,
            'trial_count': TenantSubscription.objects.filter(status='trial').count()
        }
        return render(request, 'tenants/saas_analytics.html', context)
