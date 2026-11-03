"""
ISO/IEC 27001 Security Headers & Audit Logging Middleware.
Enforces defense-in-depth on HTTP responses and logs critical access events.
"""
import logging
import time

logger = logging.getLogger('security.audit')

class ISO27001SecurityHeadersMiddleware:
    """Injects high-assurance security headers required by ISO 27001."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['X-XSS-Protection'] = '1; mode=block'
        return response

class SecurityAuditLoggingMiddleware:
    """Logs security relevant requests for auditability (ISO 27001 A.8.15)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Only log mutating / authentication requests to reduce noise
        if request.path.startswith('/api/') and request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            user_info = getattr(request.user, 'email', 'Anonymous')
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Unknown'))
            logger.info(
                f"[AUDIT] Method: {request.method} | Path: {request.path} | Status: {response.status_code} "
                f"| User: {user_info} | IP: {ip} | Time: {duration:.3f}s"
            )
        return response
