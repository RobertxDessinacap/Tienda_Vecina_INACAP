from datetime import timedelta
import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.authentication import generate_jwt_token
from apps.accounts.models import Persona, Rol, UserCredential, UserProfile, UserRol

_PROFILE_DANGEROUS_PATTERNS = re.compile(
    r'(javascript:|data\s*:\s*text/html|vbscript:|on\w+\s*=|<\s*script)',
    re.IGNORECASE,
)


def _validate_safe_profile_text(value: str, field_label: str) -> str:
    """Reject angle brackets and script injection patterns while allowing standard punctuation."""
    if not value:
        return value
    cleaned = value.strip()
    if '<' in cleaned or '>' in cleaned:
        raise serializers.ValidationError(
            f"El campo '{field_label}' no puede contener los caracteres '<' o '>'."
        )
    if _PROFILE_DANGEROUS_PATTERNS.search(cleaned):
        raise serializers.ValidationError(
            f"Patrón de inyección de código detectado no permitido en '{field_label}'."
        )
    return cleaned


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'rut', 'nombres', 'apellidos', 'nombre_completo', 'telefono', 'direccion']
        read_only_fields = ['id', 'nombre_completo']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializador público del UserProfile (no expone PII civil como nombre real).
    """
    roles = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'public_alias',
            'reputation_score',
            'is_verified_seller',
            'total_sales',
            'is_official_store',
            'official_store_name',
            'official_store_url',
            'official_store_status',
            'roles',
            'created_at',
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return [ur.rol.nombre for ur in obj.user_roles.filter(activo=True)]


class UserProfilePrivateSerializer(UserProfileSerializer):
    """
    Serializador privado del UserProfile para vistas autenticadas del propio usuario.
    """
    persona_nombre = serializers.CharField(source='persona.nombre_completo', read_only=True)

    class Meta(UserProfileSerializer.Meta):
        fields = UserProfileSerializer.Meta.fields + ['persona_nombre']
        read_only_fields = fields


class RegisterStoreSerializer(serializers.Serializer):
    """
    Serializador para registrar o editar una Tienda Oficial del vendedor.
    """
    store_name = serializers.CharField(max_length=150, min_length=3)
    store_url = serializers.URLField(max_length=500, required=False, allow_blank=True)

    def validate_store_name(self, value):
        from apps.products.serializers import validate_xss_safe
        return validate_xss_safe(value, "Nombre de la Tienda Oficial")

    def validate_store_url(self, value):
        if not value:
            return ''
        cleaned = value.strip()
        from apps.products.serializers import validate_xss_safe
        cleaned = validate_xss_safe(cleaned, "URL de la Tienda Oficial")

        validator = URLValidator(schemes=['https'])
        try:
            validator(cleaned)
        except DjangoValidationError:
            raise serializers.ValidationError(
                "La URL de la tienda oficial debe utilizar protocolo HTTPS válido (ej: https://mitienda.cl)."
            )

        parsed = urlparse(cleaned)
        if parsed.scheme.lower() != 'https' or not parsed.netloc:
            raise serializers.ValidationError(
                "Solo se permiten URLs seguras con protocolo HTTPS."
            )
        return cleaned


# Alias para compatibilidad
AccountProxyPublicSerializer = UserProfileSerializer


class UserMeSerializer(serializers.ModelSerializer):
    """Resumen de la sesión del usuario actual."""
    user_profile = UserProfilePrivateSerializer(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = UserCredential
        fields = ['id', 'email', 'role', 'roles', 'user_profile', 'created_at']
        read_only_fields = fields

    def get_roles(self, obj):
        if hasattr(obj, 'user_profile'):
            return obj.user_profile.get_roles()
        return [obj.role]


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[UserCredential.ROLE_BUYER, UserCredential.ROLE_SELLER],
        default=UserCredential.ROLE_BUYER
    )
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    rut = serializers.CharField(max_length=20, required=False, allow_blank=True)
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

    def validate_rut(self, value):
        if not value:
            return ''
        cleaned_rut = value.strip().upper()
        if cleaned_rut and Persona.objects.filter(rut=cleaned_rut).exists():
            raise serializers.ValidationError(
                "No fue posible completar el registro con el RUT proporcionado."
            )
        return cleaned_rut

    def validate_custom_alias(self, value):
        return _validate_safe_profile_text(value, "Alias público")

    def validate_full_name(self, value):
        return _validate_safe_profile_text(value, "Nombre completo")

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        role = validated_data.get('role', UserCredential.ROLE_BUYER)
        full_name = validated_data.get('full_name', '').strip()
        rut = validated_data.get('rut', '').strip().upper()
        custom_alias = validated_data.get('custom_alias', '').strip()

        try:
            with transaction.atomic():
                user = UserCredential.objects.create_user(
                    email=email,
                    password=password,
                    role=role
                )

                profile = user.user_profile
                if custom_alias:
                    if not UserProfile.objects.filter(public_alias=custom_alias).exclude(id=profile.id).exists():
                        profile.public_alias = custom_alias
                        profile.save(update_fields=['public_alias'])

                # Actualizar datos de la Persona asociada
                persona_updated = False
                if full_name:
                    parts = full_name.split(' ', 1)
                    profile.persona.nombres = parts[0]
                    profile.persona.apellidos = parts[1] if len(parts) > 1 else ''
                    persona_updated = True
                if rut:
                    profile.persona.rut = rut
                    persona_updated = True
                if persona_updated:
                    profile.persona.save()
        except IntegrityError:
            raise serializers.ValidationError(
                "No fue posible completar el registro debido a un conflicto con los datos proporcionados."
            )

        token = generate_jwt_token(user)
        return {
            'user': user,
            'token': token,
            'role': user.role,
            'user_profile': profile
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

        if user.is_locked():
            raise serializers.ValidationError(
                "Cuenta temporalmente bloqueada por exceso de intentos fallidos. Intente más tarde."
            )

        if not user.is_active:
            raise serializers.ValidationError("La cuenta se encuentra inactiva.")

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save(update_fields=['failed_login_attempts', 'locked_until'])
            raise serializers.ValidationError("Credenciales inválidas. Compruebe correo y contraseña.")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'locked_until', 'last_login'])

        token = generate_jwt_token(user)
        return {
            'user': user,
            'token': token,
            'role': user.role,
            'user_profile': user.user_profile
        }
