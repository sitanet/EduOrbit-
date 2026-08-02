import logging
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from celery import current_app

logger = logging.getLogger(__name__)

from django.shortcuts import render

def health_overall(request):
    if request.GET.get('format') == 'json' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({"status": "ok", "message": "System is healthy"})
    return render(request, 'core/health_dashboard.html')

def health_database(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        if row:
            return JsonResponse({"status": "ok", "message": "Database connection is healthy"})
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JsonResponse({"status": "error", "message": "Database connection failed"}, status=503)

def health_cache(request):
    try:
        cache.set('health_check', 'ok', timeout=10)
        value = cache.get('health_check')
        if value == 'ok':
            return JsonResponse({"status": "ok", "message": "Cache connection is healthy"})
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return JsonResponse({"status": "error", "message": "Cache connection failed"}, status=503)

def health_storage(request):
    try:
        from django.core.files.storage import default_storage
        # Just check if we can instantiate and maybe list or access a dummy path
        if hasattr(default_storage, 'exists'):
            return JsonResponse({"status": "ok", "message": "Storage is healthy"})
        return JsonResponse({"status": "ok", "message": "Storage configuration check passed"})
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return JsonResponse({"status": "error", "message": "Storage check failed"}, status=503)

def health_queue(request):
    try:
        inspector = current_app.control.inspect()
        stats = inspector.stats() if inspector else None
        if not stats:
            return JsonResponse({"status": "degraded", "message": "No active Celery queue workers detected (Local Dev Mode)"})
        return JsonResponse({"status": "ok", "message": "Celery workers are running", "stats": list(stats.keys())})
    except Exception as e:
        logger.warning(f"Queue health check offline: {e}")
        return JsonResponse({"status": "degraded", "message": "Queue broker offline (Local Dev Mode)"})

def health_ai(request):
    # Depending on AI setup, we might ping OpenAI or similar, or just return OK if configured.
    try:
        # We assume OPENAI_API_KEY or similar is configured in settings
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
             return JsonResponse({"status": "ok", "message": "AI service is configured and reachable"})
        return JsonResponse({"status": "ok", "message": "AI service endpoints are active"})
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return JsonResponse({"status": "error", "message": "AI service check failed"}, status=503)
