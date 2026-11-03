"""
JWT Authentication Service adhering to ISO 27001 Cryptographic Guidelines.
Issues and validates short-lived, signed JWT tokens.
"""
from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from apps.accounts.models import UserCredential

def generate_jwt_token(user: UserCredential) -> str:
    """Generates a secure, signed JWT containing minimal user claims."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'role': user.role,
        'exp': expiration,
        'iat': datetime.now(timezone.utc),
        'iss': 'inacap-ecommerce-auth',
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    return token


class JWTAuthentication(authentication.BaseAuthentication):
    """DRF Authentication provider that validates Bearer JWTs."""
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('El token de sesión ha expirado. Inicia sesión nuevamente.')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token de autenticación inválido o manipulado.')

        user_id = payload.get('sub')
        try:
            user = UserCredential.objects.get(id=user_id)
        except UserCredential.DoesNotExist:
            raise exceptions.AuthenticationFailed('Usuario no encontrado o revocado.')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('La cuenta se encuentra inactiva.')

        return (user, token)
