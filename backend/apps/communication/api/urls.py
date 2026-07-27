from django.urls import path
from backend.apps.communication.api.views import (
    MessageListAPIView, MessageSendAPIView, TicketCreateAPIView, TicketListAPIView
)

app_name = 'communication_api'

urlpatterns = [
    path('messages/', MessageListAPIView.as_view(), name='message_list'),
    path('messages/send/', MessageSendAPIView.as_view(), name='message_send'),
    path('tickets/', TicketListAPIView.as_view(), name='ticket_list'),
    path('tickets/create/', TicketCreateAPIView.as_view(), name='ticket_create'),
]
