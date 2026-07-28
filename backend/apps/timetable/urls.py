from django.urls import path, include
from django.views.generic import RedirectView
from backend.apps.timetable.views_web import TimetableMatrixWebView, ResourceBookingWebView

urlpatterns = [
    # Root redirect to builder
    path('', RedirectView.as_view(url='builder/', permanent=False)),
    # Web views
    path('builder/', TimetableMatrixWebView.as_view(), name='timetable_matrix_web'),
    path('bookings/', ResourceBookingWebView.as_view(), name='resource_booking_web'),
    
    # API endpoints versions
    path('api/v1/', include('backend.apps.timetable.api.urls')),
]
