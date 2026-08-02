from django.shortcuts import render, redirect
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.teachers.models import SchemeOfWork, Assignment, StudentObservation
from backend.apps.dashboard.views_web import RoleRequiredMixin
from backend.apps.dashboard.services import ROLE_TEACHER

class TeacherDashboardWebView(RoleRequiredMixin, View):
    required_role = ROLE_TEACHER

    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        schools = School.objects.filter(tenant=tenant)
        active_school = schools.first()
        
        schemes = SchemeOfWork.objects.filter(school=active_school, tenant=tenant)
        assignments = Assignment.objects.filter(school=active_school, tenant=tenant)
        observations = StudentObservation.objects.filter(tenant=tenant)
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'schemes': schemes,
            'assignments': assignments,
            'observations': observations
        }
        return render(request, 'teachers/dashboard.html', context)


class WeeklyPlannerWebView(RoleRequiredMixin, View):
    required_role = ROLE_TEACHER

    def get(self, request):
            
        schemes = SchemeOfWork.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'teachers/planner.html', {'schemes': schemes})
