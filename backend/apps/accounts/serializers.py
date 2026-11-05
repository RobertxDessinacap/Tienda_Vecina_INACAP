import re
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import UserCredential, UserProfile, Persona, Rol, UserRol
from apps.accounts.authentication import generate_jwt_token

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['id', 'rut', 'nombres', 'apellidos', 'nombre_completo', 'telefono', 'direccion']
        read_only_fields = ['id', 'nombre_completo']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializador del UserProfile (la entidad intermedia que se mueve en el sistema).
    """
    persona_nombre = serializers.CharField(source='persona.nombre_completo', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'public_alias',
            'persona_nombre',
            'reputation_score',
            'is_verified_seller',
            'total_sales',
            'is_official_store',
            'official_store_name',
            'official_store_url',
            'roles',
            'created_at'
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return [ur.rol.nombre for ur in obj.user_roles.filter(activo=True)]


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
        if value:
            from apps.products.serializers import validate_xss_safe
            return validate_xss_safe(value, "URL de la Tienda Oficial")
        return value


# Alias para compatibilidad
AccountProxyPublicSerializer = UserProfileSerializer


class UserMeSerializer(serializers.ModelSerializer):
    """Resumen de la sesión del usuario actual."""
    user_profile = UserProfileSerializer(read_only=True)
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

    def validate_custom_alias(self, value):
        if not value:
            return value
        cleaned = value.strip()
        # Rechazar caracteres especiales de XSS / inyección
        if re.search(r'[<>{}\[\]*\\;^$|~`]', cleaned):
            raise serializers.ValidationError("El nombre o apodo no puede contener caracteres especiales como [ } * < > \\ ; etc.")
        if re.search(r'(javascript:|data:|vbscript:|<\s*script)', cleaned, re.IGNORECASE):
            raise serializers.ValidationError("Patrón de inyección de código detectado no permitido.")
        return cleaned

    def validate_full_name(self, value):
        if not value:
            return value
        cleaned = value.strip()
        if re.search(r'[<>{}\[\]*\\;^$|~`]', cleaned):
            raise serializers.ValidationError("El nombre completo no puede contener caracteres especiales no autorizados.")
        return cleaned

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        role = validated_data.get('role', UserCredential.ROLE_BUYER)
        full_name = validated_data.get('full_name', '').strip()
        rut = validated_data.get('rut', '').strip()
        custom_alias = validated_data.get('custom_alias', '').strip()

        user = UserCredential.objects.create_user(
            email=email,
            password=password,
            role=role
        )

        profile = user.user_profile
        if custom_alias:
            if not UserProfile.objects.filter(public_alias=custom_alias).exclude(id=profile.id).exists():
                profile.public_alias = custom_alias
                profile.save()

        # Actualizar datos de la Persona asociada
        if full_name:
            parts = full_name.split(' ', 1)
            profile.persona.nombres = parts[0]
            profile.persona.apellidos = parts[1] if len(parts) > 1 else ''
        if rut:
            profile.persona.rut = rut
        profile.persona.save()

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
