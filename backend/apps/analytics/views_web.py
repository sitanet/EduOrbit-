from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.analytics.models import Dashboard, KPI, ReportDefinition

class ExecutiveDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        dashboards = Dashboard.objects.filter(tenant=getattr(request, 'tenant', None))
        kpis = KPI.objects.filter(tenant=getattr(request, 'tenant', None))
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'dashboards': dashboards,
            'kpis': kpis
        }
        return render(request, 'analytics/dashboard.html', context)


class ReportBuilderWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        reports = ReportDefinition.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'analytics/builder.html', {'reports': reports})
