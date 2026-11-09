import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==============================================================================
# 1. OBJETO PERSONA (Datos del individuo en el mundo real)
# ==============================================================================
class Persona(models.Model):
    """
    Objeto Persona solicitado explícitamente en la arquitectura.
    Contiene la identidad personal civil y PII del titular.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    telefono = models.CharField(max_length=30, blank=True, default='')
    direccion = models.CharField(max_length=250, blank=True, default='')
    correo_contacto = models.EmailField(max_length=255, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['nombres', 'apellidos']

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut or 'Sin RUT'})"


# ==============================================================================
# 2. USERDJANGO (Credencial y Autenticación del Sistema)
# ==============================================================================
class UserCredentialManager(BaseUserManager):
    """Gestor seguro para Userdjango."""
    def create_user(self, email, password=None, role='BUYER', **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio para fines de auditoría.')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserCredential.ROLE_ADMIN)
        return self.create_user(email, password, **extra_fields)


class UserCredential(AbstractBaseUser, PermissionsMixin):
    """
    User de Django (Userdjango) con autenticación criptográfica.
    """
    ROLE_ADMIN = 'ADMIN'
    ROLE_SELLER = 'SELLER'
    ROLE_BUYER = 'BUYER'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Administrador del Sistema'),
        (ROLE_SELLER, 'Vendedor Autorizado'),
        (ROLE_BUYER, 'Comprador / Cliente'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True, max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_BUYER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserCredentialManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User Django (Credencial)'
        verbose_name_plural = 'Users Django (Credenciales)'
        ordering = ['-created_at']

    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def __str__(self):
        return f"{self.email} ({self.role})"


# ==============================================================================
# 3. USERPROFILE (El perfil intermedio que conecta User y Persona y se mueve en el sistema)
# ==============================================================================
class UserProfile(models.Model):
    """
    Perfil intermedio solicitado por el profesor:
    'entre el user y la persona debe ser el userprofile y este se puede mover en el sistema'.
    Es la entidad activa que se vincula a productos, pedidos y transacciones públicas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserCredential,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    persona = models.OneToOneField(
        Persona,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    public_alias = models.CharField(max_length=100, unique=True, db_index=True)
    reputation_score = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    is_verified_seller = models.BooleanField(default=False)
    total_sales = models.PositiveIntegerField(default=0)

    # Tienda Oficial (Registrada por el vendedor)
    is_official_store = models.BooleanField(default=False, verbose_name="¿Es Tienda Oficial?")
    official_store_name = models.CharField(max_length=150, blank=True, default='', verbose_name="Nombre de la Tienda Oficial")
    official_store_url = models.URLField(max_length=500, blank=True, default='', verbose_name="URL del Sitio Oficial")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Usuario (UserProfile)'
        verbose_name_plural = 'Perfiles de Usuarios (UserProfiles)'

    def get_roles(self):
        """Retorna la lista de roles activos asignados al perfil."""
        return [ur.rol.codigo for ur in self.user_roles.filter(activo=True)]

    def has_role(self, role_code):
        return self.user_roles.filter(rol__codigo=role_code, activo=True).exists()

    def __str__(self):
        return f"UserProfile: {self.public_alias} ({self.persona.nombre_completo})"


# Alias de compatibilidad hacia atrás
AccountProxy = UserProfile


# ==============================================================================
# 4. ROL & USERROL (Rolificación explícita ROL -> UserRol)
# ==============================================================================
class Rol(models.Model):
    """
    Catálogo de Roles (ROL) del sistema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    descripcion = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class UserRol(models.Model):
    """
    Asignación de roles al UserProfile (UserRol).
    Permite rolificación dinámica para clientes y vendedores.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rol de Usuario (UserRol)'
        verbose_name_plural = 'Roles de Usuarios (UserRoles)'
        unique_together = ('user_profile', 'rol')

    def __str__(self):
        return f"{self.user_profile.public_alias} -> {self.rol.nombre}"


# ==============================================================================
# SEÑAL PARA GARANTIZAR LA CREACIÓN ATÓMICA DE PERSONA, USERPROFILE Y USERROL
# ==============================================================================
@receiver(post_save, sender=UserCredential)
def ensure_persona_and_user_profile(sender, instance, created, **kwargs):
    """
    Garantiza que cada User de Django tenga automáticamente:
    1. Su objeto Persona.
    2. Su UserProfile intermedio conectado a User y Persona.
    3. Sus UserRoles asignados (Vendedor, Cliente o Admin).
    """
    try:
        profile = instance.user_profile
    except UserProfile.DoesNotExist:
        # 1. Crear Persona base
        base_name = instance.email.split('@')[0].replace('.', ' ').title()
        persona = Persona.objects.create(
            nombres=base_name,
            apellidos='Usuario',
            correo_contacto=instance.email
        )

        # 2. Crear UserProfile intermedio
        base_alias = instance.email.split('@')[0].replace('.', '_')
        unique_alias = f"{base_alias}_{uuid.uuid4().hex[:6]}"
        is_seller = (instance.role in (UserCredential.ROLE_SELLER, UserCredential.ROLE_ADMIN))
        profile = UserProfile.objects.create(
            user=instance,
            persona=persona,
            public_alias=unique_alias,
            is_verified_seller=is_seller
        )

    # 3. Asignar ROL -> UserRol correspondiente
    role_mapping = {
        UserCredential.ROLE_ADMIN: ('Administrador', 'ADMIN'),
        UserCredential.ROLE_SELLER: ('Vendedor', 'SELLER'),
        UserCredential.ROLE_BUYER: ('Cliente', 'BUYER'),
    }
    nombre_rol, codigo_rol = role_mapping.get(instance.role, ('Cliente', 'BUYER'))
    rol_obj, _ = Rol.objects.get_or_create(
        codigo=codigo_rol,
        defaults={'nombre': nombre_rol, 'descripcion': f'Rol {nombre_rol} en Tienda Vecina'}
    )
    UserRol.objects.get_or_create(user_profile=profile, rol=rol_obj)
