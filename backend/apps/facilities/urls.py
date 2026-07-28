from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.facilities.views_web import FacilitiesDashboardWebView, WorkOrdersBoardWebView

urlpatterns = [
    # Root redirect to dashboard
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    # Web views
    path('dashboard/', FacilitiesDashboardWebView.as_view(), name='facilities_dashboard_web'),
    path('board/', WorkOrdersBoardWebView.as_view(), name='work_orders_board_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.facilities.api.urls')),
]
