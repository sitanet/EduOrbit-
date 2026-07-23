from django.urls import path, include
from backend.apps.facilities.views_web import FacilitiesDashboardWebView, WorkOrdersBoardWebView

urlpatterns = [
    # Web views
    path('dashboard/', FacilitiesDashboardWebView.as_view(), name='facilities_dashboard_web'),
    path('board/', WorkOrdersBoardWebView.as_view(), name='work_orders_board_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.facilities.api.urls')),
]
