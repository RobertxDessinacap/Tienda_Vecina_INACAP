from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import UserCredential, AccountProxy, UserProfileSensitive
from apps.accounts.authentication import generate_jwt_token

class AccountProxyPublicSerializer(serializers.ModelSerializer):
    """Public representation of Intermediate Account. No PII exposed."""
    class Meta:
        model = AccountProxy
        fields = ['id', 'public_alias', 'reputation_score', 'is_verified_seller', 'total_sales']
        read_only_fields = fields


class UserMeSerializer(serializers.ModelSerializer):
    """Current authenticated user profile summary."""
    intermediate_account = AccountProxyPublicSerializer(read_only=True)

    class Meta:
        model = UserCredential
        fields = ['id', 'email', 'role', 'intermediate_account', 'created_at']
        read_only_fields = fields


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[UserCredential.ROLE_BUYER, UserCredential.ROLE_SELLER],
        default=UserCredential.ROLE_BUYER
    )
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    custom_alias = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if UserCredential.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return normalized

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener un mínimo de 8 caracteres.")
        return value

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        role = validated_data.get('role', UserCredential.ROLE_BUYER)
        full_name = validated_data.get('full_name', '')
        custom_alias = validated_data.get('custom_alias', '').strip()

        user = UserCredential.objects.create_user(
            email=email,
            password=password,
            role=role
        )

        # Update alias if user supplied a custom public pseudonym
        if custom_alias:
            proxy = user.intermediate_account
            # Ensure unique alias
            if not AccountProxy.objects.filter(public_alias=custom_alias).exclude(id=proxy.id).exists():
                proxy.public_alias = custom_alias
                proxy.save()

        # Create segregated sensitive profile
        UserProfileSensitive.objects.create(
            credential=user,
            full_name=full_name
        )

        token = generate_jwt_token(user)
        return {
            'user': user,
            'token': token,
            'role': user.role,
            'intermediate_account': user.intermediate_account
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')

        try:
            user = UserCredential.objects.get(email=email)
        except UserCredential.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas. Compruebe correo y contraseña.")

        # Check account lockout
        if user.is_locked():
            raise serializers.ValidationError(
                f"Cuenta temporalmente bloqueada por exceso de intentos fallidos. Intente más tarde."
            )

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
            raise serializers.ValidationError("Credenciales inválidas. Compruebe correo y contraseña.")

        # Success: reset attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'locked_until', 'last_login'])

        token = generate_jwt_token(user)
        return {
            'user': user,
            'token': token,
            'role': user.role,
            'intermediate_account': user.intermediate_account
        }
