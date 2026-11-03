import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserCredentialManager(BaseUserManager):
    """Secure manager for UserCredential with email normalization and hashing."""
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
    Core Authentication Entity (ISO 27001 - Confidential Layer).
    Stores login secrets and RBAC definitions. Never directly exposed to public endpoints.
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
        verbose_name = 'Credencial de Usuario'
        verbose_name_plural = 'Credenciales de Usuarios'
        ordering = ['-created_at']

    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def __str__(self):
        return f"{self.email} ({self.role})"


class AccountProxy(models.Model):
    """
    Intermediate Public Account (Surrogate Identity Layer).
    Public facing entity that disconnects core identity from storefront activities.
    Products and public catalog actions link exclusively to this entity.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.OneToOneField(
        UserCredential,
        on_delete=models.CASCADE,
        related_name='intermediate_account'
    )
    public_alias = models.CharField(max_length=100, unique=True, db_index=True)
    reputation_score = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    is_verified_seller = models.BooleanField(default=False)
    total_sales = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuenta Intermedia Pública'
        verbose_name_plural = 'Cuentas Intermedias Públicas'

    def __str__(self):
        return f"Alias: {self.public_alias} (Rep: {self.reputation_score})"


class UserProfileSensitive(models.Model):
    """
    Segregated Sensitive PII Storage (ISO 27001 Restricted Access Layer).
    Holds personal data separate from transactional and public systems.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.OneToOneField(
        UserCredential,
        on_delete=models.CASCADE,
        related_name='sensitive_profile'
    )
    full_name = models.CharField(max_length=150, blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    rut_tax_id = models.CharField(max_length=20, blank=True, default='')
    shipping_address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Datos Sensibles (PII)'
        verbose_name_plural = 'Perfiles de Datos Sensibles'

    def __str__(self):
        return f"PII Profile for {self.credential.email}"


@receiver(post_save, sender=UserCredential)
def ensure_intermediate_account(sender, instance, created, **kwargs):
    """Guarantees that an Intermediate Account (AccountProxy) always exists for every user."""
    try:
        _ = instance.intermediate_account
    except AccountProxy.DoesNotExist:
        base_alias = instance.email.split('@')[0].replace('.', '_')
        unique_alias = f"{base_alias}_{uuid.uuid4().hex[:6]}"
        is_seller = (instance.role in (UserCredential.ROLE_SELLER, UserCredential.ROLE_ADMIN))
        AccountProxy.objects.create(
            credential=instance,
            public_alias=unique_alias,
            is_verified_seller=is_seller
        )

