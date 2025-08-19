from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    # Let DRF handle the exception first
    response = exception_handler(exc, context)

    if response is not None:
        # Extract default error detail from DRF
        errors = response.data
        message = None

        # DRF's "detail" key is common for auth errors
        if errors is not None and "detail" in errors:
            message = errors["detail"]
            errors = None 

        return Response({
            "success": False,
            "message": message or "Validation error",
            "data": None,
            "errors": errors
        }, status=response.status_code)

    # Fallback for unhandled exceptions
    return Response({
        "success": False,
        "message": str(exc),
        "data": None,
        "errors": None
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
