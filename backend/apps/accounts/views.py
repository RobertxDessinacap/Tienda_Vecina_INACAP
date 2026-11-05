from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.accounts.models import UserCredential, Rol, UserRol
from apps.accounts.serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserMeSerializer,
    UserProfileSerializer,
    RegisterStoreSerializer
)
from apps.accounts.permissions import IsSellerOrAdmin

class RegisterAPIView(APIView):
    """Registro con creación automática de Persona, UserProfile y UserRol."""
    permission_classes = [permissions.AllowAny]

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
                    "user_profile": UserProfileSerializer(profile).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """Autenticación segura generando JWT bajo ISO 27001."""
    permission_classes = [permissions.AllowAny]

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
                    "user_profile": UserProfileSerializer(profile).data
                }
            }, status=status.HTTP_200_OK)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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
    """Permite a un comprador autenticado ascender su cuenta al rol de Vendedor."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.role = UserCredential.ROLE_SELLER
        user.save(update_fields=['role', 'updated_at'])

        rol_seller, _ = Rol.objects.get_or_create(
            codigo='SELLER',
            defaults={'nombre': 'Vendedor Autorizado', 'descripcion': 'Permiso para publicar y vender productos'}
        )
        UserRol.objects.get_or_create(
            user_profile=user.user_profile,
            rol=rol_seller,
            defaults={'activo': True}
        )
        user.user_profile.is_verified_seller = True
        user.user_profile.save(update_fields=['is_verified_seller'])

        return Response({
            "status": "success",
            "message": "¡Tu cuenta ahora tiene rol de Vendedor! Ya puedes publicar tus productos.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "user_profile": UserProfileSerializer(user.user_profile).data
            }
        }, status=status.HTTP_200_OK)


class RegisterStoreAPIView(APIView):
    """
    Permite a un vendedor registrar o actualizar su Tienda Oficial (nombre comercial y URL).
    """
    permission_classes = [permissions.IsAuthenticated, IsSellerOrAdmin]

    def post(self, request):
        serializer = RegisterStoreSerializer(data=request.data)
        if serializer.is_valid():
            store_name = serializer.validated_data['store_name']
            store_url = serializer.validated_data.get('store_url', '')

            profile = request.user.user_profile
            profile.is_official_store = True
            profile.official_store_name = store_name
            profile.official_store_url = store_url
            profile.save(update_fields=['is_official_store', 'official_store_name', 'official_store_url'])

            return Response({
                "status": "success",
                "message": f"¡Tienda oficial '{store_name}' registrada exitosamente!",
                "data": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
