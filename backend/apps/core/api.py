from rest_framework.renderers import JSONRenderer
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging
from datetime import datetime

logger = logging.getLogger("eduorbit.api")

class StandardResponseRenderer(JSONRenderer):
    """
    Standard Response Renderer ensuring all JSON responses match the enterprise structure:
    {
      "success": true/false,
      "data": {...},
      "meta": {"timestamp": "...", "requestId": "..."}
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None
        
        # Check if the response was an error
        is_success = response is not None and not status.is_client_error(response.status_code) and not status.is_server_error(response.status_code)
        
        meta = {
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # If response data is already formatted into the standard envelope, return it
        if isinstance(data, dict) and ("success" in data and ("data" in data or "error" in data)):
            return super().render(data, accepted_media_type, renderer_context)
            
        if is_success:
            envelope = {
                "success": True,
                "data": data,
                "meta": meta
            }
        else:
            envelope = {
                "success": False,
                "error": {
                    "code": "API_ERROR",
                    "message": data.get("detail", "An unexpected error occurred.") if isinstance(data, dict) else str(data)
                },
                "meta": meta
            }
            if isinstance(data, dict) and "errors" in data:
                envelope["error"]["details"] = data["errors"]
                
        return super().render(envelope, accepted_media_type, renderer_context)


def custom_exception_handler(exc, context):
    """
    Central Exception Handler converting validation and access exceptions into clean JSON errors.
    """
    response = exception_handler(exc, context)
    
    # Catch unhandled errors and return generic 500
    if response is None:
        logger.error("Unhandled API Exception", exc_info=exc)
        return Response({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "A critical system error occurred. Please contact administration."
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Reformat validation errors (HTTP 400)
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        errors_list = []
        if isinstance(response.data, dict):
            for field, messages in response.data.items():
                msg = messages[0] if isinstance(messages, list) else str(messages)
                errors_list.append({
                    "field": field,
                    "issue": msg
                })
        
        response.data = {
            "success": False,
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Input validation failed. Please check individual field issues.",
                "details": errors_list
            },
            "meta": {
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    
    return response
