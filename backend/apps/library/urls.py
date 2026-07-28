from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.library.views_web import LibraryDashboardWebView, BookCatalogWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', LibraryDashboardWebView.as_view(), name='library_dashboard_web'),
    path('catalog/', BookCatalogWebView.as_view(), name='catalog_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.library.api.urls')),
]
