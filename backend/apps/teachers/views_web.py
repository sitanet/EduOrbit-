from django.shortcuts import render, redirect
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.teachers.models import SchemeOfWork, Assignment, StudentObservation

class TeacherDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        schemes = SchemeOfWork.objects.filter(school=active_school, tenant=getattr(request, 'tenant', None))
        assignments = Assignment.objects.filter(school=active_school, tenant=getattr(request, 'tenant', None))
        observations = StudentObservation.objects.filter(tenant=getattr(request, 'tenant', None))
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'schemes': schemes,
            'assignments': assignments,
            'observations': observations
        }
        return render(request, 'teachers/dashboard.html', context)


class WeeklyPlannerWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schemes = SchemeOfWork.objects.filter(tenant=getattr(request, 'tenant', None))
        return render(request, 'teachers/planner.html', {'schemes': schemes})
