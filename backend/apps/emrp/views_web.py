from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.emrp.models import Examination, ExamResult

class EMRPDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        exams = Examination.objects.filter(school=active_school, tenant=getattr(request, 'tenant', None))
        context = {
            'schools': schools,
            'active_school': active_school,
            'exams': exams
        }
        return render(request, 'emrp/dashboard.html', context)


class BroadsheetWebView(View):
    def get(self, request, exam_id):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        exam = get_object_or_404(Examination, id=exam_id, tenant=getattr(request, 'tenant', None))
        results = ExamResult.objects.filter(exam=exam, tenant=getattr(request, 'tenant', None)).select_related('student__person')
        
        context = {
            'exam': exam,
            'results': results
        }
        return render(request, 'emrp/broadsheet.html', context)
