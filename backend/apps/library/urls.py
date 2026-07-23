from django.urls import path, include
from backend.apps.library.views_web import LibraryDashboardWebView, BookCatalogWebView

urlpatterns = [
    # Web views
    path('dashboard/', LibraryDashboardWebView.as_view(), name='library_dashboard_web'),
    path('catalog/', BookCatalogWebView.as_view(), name='catalog_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.library.api.urls')),
]
