import uuid
from django.db import models
from apps.accounts.models import UserProfile
from apps.products.models import Product

class Order(models.Model):
    """
    Orden de compra con cálculo seguro exclusivamente en el Backend (Django ORM).
    Blindada contra manipulación de precios desde el cliente JavaScript.
    """
    STATUS_CHOICES = (
        ('INITIALIZED', 'Iniciada'),
        ('AUTHORIZED', 'Aprobada / Pagada'),
        ('FAILED', 'Rechazada / Fallida'),
        ('REVERSED', 'Reversada'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('WEBPAY_PLUS', 'Transbank Webpay Plus'),
        ('MERCADO_PAGO', 'Mercado Pago'),
        ('TRANSFER', 'Transferencia Bancaria'),
        ('PREPAY', 'Tarjeta de Prepago'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buy_order = models.CharField(max_length=64, unique=True, db_index=True)
    session_id = models.CharField(max_length=100, blank=True, default='')

    # UserProfile intermedio que realiza la compra
    buyer_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    # Monto total calculado 100% en backend
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='INITIALIZED')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='WEBPAY_PLUS')

    # Transbank Audit Data
    transbank_token = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    authorization_code = models.CharField(max_length=50, blank=True, null=True)
    card_last_digits = models.CharField(max_length=10, blank=True, null=True)
    payment_type_code = models.CharField(max_length=10, blank=True, null=True)
    shares_number = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden de Compra'
        verbose_name_plural = 'Órdenes de Compra'
        ordering = ['-created_at']

    def __str__(self):
        return f"Orden {self.buy_order} - ${self.total_amount} ({self.status})"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Ítem de Orden'
        verbose_name_plural = 'Ítems de Órdenes'

    def __str__(self):
        return f"{self.quantity}x {self.product.title} (${self.subtotal})"
