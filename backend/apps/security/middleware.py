"""
ISO/IEC 27001 Security Headers & Audit Logging Middleware.
Enforces defense-in-depth on HTTP responses and logs critical access events.
"""
import ipaddress
import logging
import re
import time
from django.conf import settings

logger = logging.getLogger('security.audit')

_CONTROL_CHARS_RE = re.compile(r'[\r\n\x00-\x1f\x7f]')


def _sanitize_log_value(value) -> str:
    """Strip control characters and newlines to prevent CRLF log injection."""
    if value is None:
        return ''
    return _CONTROL_CHARS_RE.sub('', str(value))


def _extract_client_ip(request) -> str:
    """Resolve and validate the client IP without trusting spoofable headers by default."""
    raw_ip = None
    if getattr(settings, 'TRUST_X_FORWARDED_FOR', False):
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if xff:
            raw_ip = xff.split(',')[0].strip()

    if not raw_ip:
        raw_ip = request.META.get('REMOTE_ADDR', '')

    cleaned = _sanitize_log_value(raw_ip).strip()
    if not cleaned:
        return 'Unknown'

    try:
        return str(ipaddress.ip_address(cleaned))
    except ValueError:
        return 'Invalid_IP'


class ISO27001SecurityHeadersMiddleware:
    """Injects high-assurance security headers required by ISO 27001."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
        response['X-XSS-Protection'] = '1; mode=block'

        if request.is_secure() or not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        connect_sources = [
            "'self'",
            "https://webpay3gint.transbank.cl",
            "https://webpay3g.transbank.cl",
        ]
        for origin in getattr(settings, 'CORS_ALLOWED_ORIGINS', []):
            cleaned_origin = origin.strip()
            if cleaned_origin and cleaned_origin not in connect_sources:
                connect_sources.append(cleaned_origin)

        if settings.DEBUG:
            for dev_origin in (
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ):
                if dev_origin not in connect_sources:
                    connect_sources.append(dev_origin)

        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https://images.unsplash.com; "
            f"connect-src {' '.join(connect_sources)}; "
            "font-src 'self' data:; "
            "form-action 'self' https://webpay3gint.transbank.cl https://webpay3g.transbank.cl; "
            "frame-ancestors 'none';"
        )
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
            method = _sanitize_log_value(request.method)
            path = _sanitize_log_value(request.path)
            req_user = getattr(request, 'user', None)
            user_info = _sanitize_log_value(getattr(req_user, 'email', 'Anonymous') or 'Anonymous')
            ip = _extract_client_ip(request)
            logger.info(
                f"[AUDIT] Method: {method} | Path: {path} | Status: {response.status_code} "
                f"| User: {user_info} | IP: {ip} | Time: {duration:.3f}s"
            )
        return response
