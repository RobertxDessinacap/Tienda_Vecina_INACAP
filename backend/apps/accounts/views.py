from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.accounts.serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserMeSerializer,
    UserProfileSerializer
)

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
