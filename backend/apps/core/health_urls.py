from django.urls import path
from . import health

urlpatterns = [
    path('', health.health_overall, name='health_overall'),
    path('database/', health.health_database, name='health_database'),
    path('cache/', health.health_cache, name='health_cache'),
    path('storage/', health.health_storage, name='health_storage'),
    path('queue/', health.health_queue, name='health_queue'),
    path('ai/', health.health_ai, name='health_ai'),
]
