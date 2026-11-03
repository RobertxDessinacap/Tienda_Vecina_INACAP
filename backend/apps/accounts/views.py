from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.accounts.serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserMeSerializer,
    AccountProxyPublicSerializer
)

class RegisterAPIView(APIView):
    """Public registration with automatic intermediate account generation."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            user = result['user']
            proxy = result['intermediate_account']
            return Response({
                "status": "success",
                "message": "Usuario registrado exitosamente con Cuenta Intermedia protegida.",
                "token": result['token'],
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "intermediate_account": AccountProxyPublicSerializer(proxy).data
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """Public secure login generating ISO 27001 compliant JWT."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.validated_data
            user = result['user']
            proxy = result['intermediate_account']
            return Response({
                "status": "success",
                "message": "Autenticación exitosa.",
                "token": result['token'],
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "intermediate_account": AccountProxyPublicSerializer(proxy).data
                }
            }, status=status.HTTP_200_OK)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class MeAPIView(APIView):
    """Returns authenticated user's credentials and intermediate account."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
