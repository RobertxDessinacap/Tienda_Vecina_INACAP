from datetime import datetime, timezone as dt_timezone
import jwt
from django.conf import settings
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import RevokedToken, Rol, UserCredential, UserProfile, UserRol
from apps.accounts.permissions import IsSellerOrAdmin
from apps.accounts.serializers import (
    LoginSerializer,
    RegisterStoreSerializer,
    UserMeSerializer,
    UserProfilePrivateSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class RegisterAPIView(APIView):
    """Registro con creación automática de Persona, UserProfile y UserRol."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            user = result['user']
            profile = result['user_profile']
            return Response({
                "status": "success",
                "message": "Usuario registrado exitosamente con UserProfile y Persona asociada.",
                "token": result['token'],
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "user_profile": UserProfilePrivateSerializer(profile).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """Autenticación segura generando JWT bajo ISO 27001."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.validated_data
            user = result['user']
            profile = result['user_profile']
            return Response({
                "status": "success",
                "message": "Autenticación exitosa.",
                "token": result['token'],
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "user_profile": UserProfilePrivateSerializer(profile).data
                }
            }, status=status.HTTP_200_OK)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """Cierra sesión revocando explícitamente el JWT actual mediante su jti."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payload = None
        auth_header = request.headers.get('Authorization', '')
        parts = auth_header.split()
        raw_token = None
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            raw_token = parts[1]
        elif isinstance(request.auth, str):
            raw_token = request.auth

        if raw_token:
            try:
                payload = jwt.decode(raw_token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
            except jwt.InvalidTokenError:
                payload = getattr(request, '_jwt_payload', None)
        else:
            payload = getattr(request, '_jwt_payload', None)

        if payload and payload.get('jti'):
            exp_ts = payload.get('exp')
            expires_at = None
            if isinstance(exp_ts, (int, float)):
                expires_at = datetime.fromtimestamp(exp_ts, tz=dt_timezone.utc)
            RevokedToken.objects.get_or_create(
                jti=str(payload['jti']),
                defaults={
                    'user': request.user,
                    'expires_at': expires_at,
                }
            )

        return Response({
            "status": "success",
            "message": "Sesión cerrada correctamente. El token ha sido revocado."
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    """Retorna información del usuario, roles activos y UserProfile que se mueve en el sistema."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class UpgradeToSellerAPIView(APIView):
    """Permite a un comprador autenticado ascender su cuenta al rol de Vendedor sin degradar a ADMIN."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            user = request.user
            profile = user.user_profile

            if user.role != UserCredential.ROLE_ADMIN:
                user.role = UserCredential.ROLE_SELLER
                user.save(update_fields=['role', 'updated_at'])

                rol_seller, _ = Rol.objects.get_or_create(
                    codigo='SELLER',
                    defaults={'nombre': 'Vendedor', 'descripcion': 'Permiso para publicar y vender productos'}
                )
                user_rol, ur_created = UserRol.objects.get_or_create(
                    user_profile=profile,
                    rol=rol_seller,
                    defaults={'activo': True}
                )
                if not ur_created and not user_rol.activo:
                    user_rol.activo = True
                    user_rol.save(update_fields=['activo'])

            if not profile.is_verified_seller:
                profile.is_verified_seller = True
                profile.save(update_fields=['is_verified_seller'])

        return Response({
            "status": "success",
            "message": (
                "Tu cuenta de Administrador ya cuenta con permisos completos de vendedor."
                if user.role == UserCredential.ROLE_ADMIN
                else "¡Tu cuenta ahora tiene rol de Vendedor! Ya puedes publicar tus productos."
            ),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "user_profile": UserProfilePrivateSerializer(profile).data
            }
        }, status=status.HTTP_200_OK)


class RegisterStoreAPIView(APIView):
    """
    Permite a un vendedor solicitar o actualizar su Tienda Oficial (nombre comercial y URL).
    Las cuentas SELLER quedan en estado PENDING hasta la aprobación de un administrador.
    """
    permission_classes = [permissions.IsAuthenticated, IsSellerOrAdmin]

    def post(self, request):
        serializer = RegisterStoreSerializer(data=request.data)
        if serializer.is_valid():
            store_name = serializer.validated_data['store_name']
            store_url = serializer.validated_data.get('store_url', '')

            profile = request.user.user_profile
            is_admin = (request.user.role == UserCredential.ROLE_ADMIN)
            profile.official_store_name = store_name
            profile.official_store_url = store_url

            if is_admin:
                profile.is_official_store = True
                profile.official_store_status = UserProfile.STORE_STATUS_APPROVED
                message = f"¡Tienda oficial '{store_name}' aprobada y registrada exitosamente!"
            else:
                profile.is_official_store = False
                profile.official_store_status = UserProfile.STORE_STATUS_PENDING
                message = (
                    f"Solicitud de tienda oficial '{store_name}' enviada para revisión. "
                    "Quedará visible tras la aprobación de un administrador."
                )

            profile.save(update_fields=[
                'is_official_store',
                'official_store_name',
                'official_store_url',
                'official_store_status',
            ])

            return Response({
                "status": "success",
                "message": message,
                "data": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ApproveOfficialStoreAPIView(APIView):
    """Permite a un Administrador aprobar o rechazar una solicitud de Tienda Oficial."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, profile_id):
        if request.user.role != UserCredential.ROLE_ADMIN:
            return Response(
                {"status": "fail", "message": "Solo los administradores pueden moderar tiendas oficiales."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"status": "fail", "message": "Perfil de usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        raw_approved = request.data.get('approved', True)
        if isinstance(raw_approved, bool):
            approved = raw_approved
        elif isinstance(raw_approved, str):
            lowered = raw_approved.strip().lower()
            if lowered in ('true', '1', 'yes'):
                approved = True
            elif lowered in ('false', '0', 'no'):
                approved = False
            else:
                return Response(
                    {"status": "fail", "message": "El campo 'approved' debe ser booleano (true/false)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            approved = bool(raw_approved)

        profile.is_official_store = approved
        profile.official_store_status = (
            UserProfile.STORE_STATUS_APPROVED if approved else UserProfile.STORE_STATUS_REJECTED
        )
        profile.save(update_fields=['is_official_store', 'official_store_status'])

        action_label = "aprobada" if approved else "rechazada"
        return Response({
            "status": "success",
            "message": f"Tienda oficial {action_label} correctamente.",
            "data": UserProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)
