from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.efbm.models import Invoice, StudentWallet

class EFBMDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        invoices = Invoice.objects.filter(student__current_school=active_school, tenant=getattr(request, 'tenant', None)).select_related('student__person')
        context = {
            'schools': schools,
            'active_school': active_school,
            'invoices': invoices
        }
        return render(request, 'efbm/dashboard.html', context)


class ParentWalletWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        wallets = StudentWallet.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('parent')
        return render(request, 'efbm/wallet.html', {'wallets': wallets})
