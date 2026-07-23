from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from backend.apps.tenants.models import School
from backend.apps.library.models import Book, BookIssue

class LibraryDashboardWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        schools = School.objects.filter(tenant=getattr(request, 'tenant', None))
        active_school = schools.first()
        
        books = Book.objects.filter(tenant=getattr(request, 'tenant', None))
        recent_issues = BookIssue.objects.filter(tenant=getattr(request, 'tenant', None)).select_related('copy__book', 'borrower')
        
        context = {
            'schools': schools,
            'active_school': active_school,
            'books': books,
            'recent_issues': recent_issues
        }
        return render(request, 'library/dashboard.html', context)


class BookCatalogWebView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login_web')
            
        books = Book.objects.filter(tenant=getattr(request, 'tenant', None)).prefetch_related('authors')
        return render(request, 'library/catalog.html', {'books': books})
