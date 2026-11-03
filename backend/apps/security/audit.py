"""
Security Exception Handling conforming to ISO 27001 Data Leakage Prevention (A.8.12).
Prevents technical stack traces or database errors from leaking to untrusted clients.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('security.exceptions')

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled internal exception: log trace privately, return standardized safe error
        view_name = context.get('view', '__unknown__').__class__.__name__
        logger.error(f"[SECURITY UNCAUGHT EXCEPTION in {view_name}]: {str(exc)}", exc_info=True)
        return Response(
            {
                "status": "error",
                "message": "Ha ocurrido un error interno de seguridad. La incidencia ha sido registrada.",
                "code": "INTERNAL_SECURITY_ERROR"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Standard DRF exception: wrap nicely
    custom_data = {
        "status": "fail",
        "errors": response.data,
        "status_code": response.status_code
    }
    response.data = custom_data
    return response
